import time
import signal
import logging
import threading
from daemon_heart import Daemon
from daemon_funk import handle_visit_request, remind_reception, schedule_visit_reminders
import mysqlDB as msq

# 🔹 Konfiguracja logowania
DEBUG = True
log_level = logging.DEBUG if DEBUG else logging.INFO
logging.basicConfig(level=log_level, format="%(asctime)s - %(message)s", datefmt="%H:%M:%S")

# Inicjalizacja daemona
daemon = Daemon()

# Symulowana baza zgłoszeń (zakomentuj i odkomentuj pobieranie z MySQL w monitor_database)
# visit_requests = [
#     {"id": 1, "name": "Jan Kowalski", "email": "informatyk@dmdbudownictwo.pl", "status": "in_progress", "in_progress_date": None, "in_progress_flag": 0, "reminder_count": 0},
#     {"id": 2, "name": "Anna Nowak", "email": "heretykboga@gmail.com", "status": "in_progress", "in_progress_date": None, "in_progress_flag": 1, "reminder_count": 0},
# ]

# **NOWE: Funkcja cyklicznie sprawdzająca bazę i aktualizująca zadania**
def monitor_database():
    """ Demon sprawdza bazę i wykrywa nowe wizyty do obsługi """
    logging.info("🔄 Sprawdzanie bazy pod kątem nowych zgłoszeń...")

    # 🔹 Pobieramy tylko potwierdzone wizyty, które nie mają jeszcze przypomnień
    visit_requests = msq.safe_connect_to_database(
        "SELECT id, name, email, confirmed_date FROM visit_requests WHERE status = 'confirmed' AND confirmed_flag = 0"
    )

    for visit in visit_requests:
        visit_dict = {
            "id": visit[0],
            "name": visit[1],
            "email": visit[2],
            "confirmed_date": visit[3]
        }

        # 🔹 Planowanie przypomnień
        schedule_visit_reminders(visit_dict, daemon)

        # 🔹 Oznaczamy w bazie, że przypomnienia są już zaplanowane
        msq.safe_connect_to_database(
            "UPDATE visit_requests SET confirmed_flag = 1 WHERE id = %s", (visit[0],)
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
