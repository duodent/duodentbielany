import time
import signal
import logging
import threading
from daemon_heart import Daemon
from daemon_funk import handle_visit_request, remind_reception, schedule_visit_reminders, send_cancellation_email
import mysqlDB as msq

# 🔹 Konfiguracja logowania
DEBUG = True
log_level = logging.DEBUG if DEBUG else logging.INFO
logging.basicConfig(level=log_level, format="%(asctime)s - %(message)s", datefmt="%H:%M:%S")

# Inicjalizacja daemona
daemon = Daemon()


# **NOWE: Funkcja cyklicznie sprawdzająca bazę i aktualizująca zadania**
def monitor_database():
    """ Demon sprawdza bazę i wykrywa nowe wizyty do obsługi """
    logging.info("🔄 Sprawdzanie bazy pod kątem nowych zgłoszeń...")

    # 🔹 **1. Pobieramy zgłoszenia, które wymagają kontaktu z recepcją**
    visit_requests = msq.connect_to_database(
        "SELECT id, name, email FROM appointment_requests WHERE status = 'in_progress' AND in_progress_flag = 0"
    )

    for visit in visit_requests:
        visit_dict = {
            "id": visit[0],
            "name": visit[1],
            "email": visit[2]
        }

        # 🔹 Wysyłamy powiadomienie do recepcji
        daemon.add_task(5, handle_visit_request, visit_dict)

        # 🔹 Oznaczamy w bazie, że powiadomienie zostało wysłane
        msq.insert_to_database(
            "UPDATE appointment_requests SET in_progress_flag = %s WHERE id = %s",
            (1, visit[0])
        )

    # 🔹 **2. Pobieramy zgłoszenia wymagające przypomnienia dla recepcji**
    pending_reception_reminders = msq.connect_to_database(
        "SELECT id, name, email FROM appointment_requests WHERE status = 'in_progress' AND in_progress_flag = 1 AND in_progress_date IS NULL"
    )

    for visit in pending_reception_reminders:
        visit_dict = {
            "id": visit[0],
            "name": visit[1],
            "email": visit[2]
        }
        daemon.add_task(10, remind_reception, visit_dict, daemon)

    # 🔹 **3. Pobieramy tylko nowe potwierdzone wizyty z przyszłości**
    confirmed_visits = msq.connect_to_database(
        "SELECT id, name, email, confirmed_date FROM appointment_requests WHERE status = 'confirmed' AND confirmed_flag = 0 AND confirmed_date >= NOW()"
    )

    for visit in confirmed_visits:
        visit_dict = {
            "id": visit[0],
            "name": visit[1],
            "email": visit[2],
            "confirmed_date": visit[3]
        }

        # 🔹 Planowanie przypomnień
        schedule_visit_reminders(visit_dict, daemon)

        # 🔹 Oznaczamy w bazie, że przypomnienia są już zaplanowane
        msq.insert_to_database(
            "UPDATE appointment_requests SET confirmed_flag = 1 WHERE id = %s",
            (visit[0],)
        )

    # 🔹 **4. Pobieramy odwołane wizyty i wysyłamy powiadomienie do pacjenta**
    cancelled_visits = msq.connect_to_database(
        "SELECT id, name, email FROM appointment_requests WHERE status = 'cancelled' AND cancelled_flag = 0"
    )

    for visit in cancelled_visits:
        visit_dict = {
            "id": visit[0],
            "name": visit[1],
            "email": visit[2]
        }

        # 🔹 Wysyłamy e-mail o odwołaniu wizyty
        daemon.add_task(5, send_cancellation_email, visit_dict)

        # 🔹 Oznaczamy w bazie, że e-mail został wysłany
        msq.insert_to_database(
            "UPDATE appointment_requests SET cancelled_flag = 1 WHERE id = %s",
            (visit[0],)
        )

    # 🔄 Demon sprawdza bazę co 30 sekund
    daemon.add_task(30, monitor_database)



# **Dodajemy pierwsze wywołanie monitorowania**
daemon.add_task(1, monitor_database)

# **Obsługa CTRL+C**
def stop_daemon(sig, frame):
    logging.info("🛑 Otrzymano sygnał zatrzymania! Zamykamy daemon...")
    daemon.stop()
    daemon_thread.join()
    logging.info("✅ Daemon został bezpiecznie zatrzymany!")

signal.signal(signal.SIGINT, stop_daemon)

# Uruchamiamy daemona
daemon_thread = threading.Thread(target=daemon.run)
daemon_thread.start()

# Główna pętla programu – teraz możemy zatrzymać `CTRL+C`
while daemon.running:
    time.sleep(1)
