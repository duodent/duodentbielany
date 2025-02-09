import time
import signal
import logging
import threading
from daemon_heart import Daemon
from daemon_funk import handle_visit_request, remind_reception, schedule_visit_reminders, send_cancellation_email
import mysqlDB as msq
from AppointmentRequest import AppointmentRequest
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

    # 🔹 **1. Pobieramy zgłoszenia wymagające kontaktu z recepcją (TYLKO PRZYSZŁE WIZYTY)**
    raw_data = msq.connect_to_database(
        "SELECT * FROM appointment_requests WHERE status = 'in_progress' AND in_progress_flag = 0 AND visit_date >= CURDATE()"
    )
    visit_requests = [AppointmentRequest.from_tuple(row) for row in raw_data]

    for visit in visit_requests:
        logging.info(f"📩 Znaleziono nowe zgłoszenie: {visit.to_dict()}")

        # ✅ Natychmiastowa wysyłka e-maila do recepcji
        daemon.add_task(5, handle_visit_request, visit)

        # ✅ **ZAPLANUJEMY pierwsze przypomnienie recepcji PO opóźnieniu, a nie od razu!**
        daemon.add_task(3600, remind_reception, visit, daemon)  # Opóźnienie 1 godzina (3600 sekund)

        # 🔹 Oznaczamy w bazie, że powiadomienie zostało wysłane
        msq.insert_to_database(
            "UPDATE appointment_requests SET in_progress_flag = %s WHERE id = %s",
            (1, visit.id)
        )

    # 🔹 **2. Pobieramy zgłoszenia wymagające przypomnienia dla recepcji**
    raw_data = msq.connect_to_database(
        "SELECT * FROM appointment_requests WHERE status = 'in_progress' AND in_progress_flag = 1 AND in_progress_date IS NULL AND visit_date >= CURDATE()"
    )
    pending_reception_reminders = [AppointmentRequest.from_tuple(row) for row in raw_data]

    for visit in pending_reception_reminders:
        logging.info(f"⏳ Przypomnienie dla recepcji: {visit.to_dict()}")
        daemon.add_task(300, remind_reception, visit, daemon)

    # 🔹 **3. Pobieramy tylko nowe potwierdzone wizyty z przyszłości**
    raw_data = msq.connect_to_database(
        "SELECT * FROM appointment_requests WHERE status = 'confirmed' "
        "AND (confirmed_flag = 0 OR confirmed_date > last_confirmed_check) "
        "AND confirmed_date >= NOW()"
    )
    confirmed_visits = [AppointmentRequest.from_tuple(row) for row in raw_data]

    for visit in confirmed_visits:
        logging.info(f"📅 Planowanie przypomnień dla wizyty: {visit.to_dict()}")
        schedule_visit_reminders(visit, daemon)

        # msq.insert_to_database(
        #     "UPDATE appointment_requests SET confirmed_flag = 1 WHERE id = %s",
        #     (visit.id,)
        # )
        msq.insert_to_database(
            "UPDATE appointment_requests SET confirmed_flag = 1, last_confirmed_check = NOW() WHERE id = %s",
            (visit.id,)
        )

    # 🔹 **4. Pobieramy odwołane wizyty i wysyłamy powiadomienie do pacjenta**
    raw_data = msq.connect_to_database(
        "SELECT * FROM appointment_requests WHERE status = 'cancelled' AND cancelled_flag = 0"
    )
    cancelled_visits = [AppointmentRequest.from_tuple(row) for row in raw_data]

    for visit in cancelled_visits:
        logging.info(f"⚠️ Odwołana wizyta – powiadomienie do pacjenta: {visit.to_dict()}")
        daemon.add_task(5, send_cancellation_email, visit)

        msq.insert_to_database(
            "UPDATE appointment_requests SET cancelled_flag = 1 WHERE id = %s",
            (visit.id,)
        )

    # 🔄 Demon sprawdza bazę co 30 sekund
    daemon.add_task(30, monitor_database)


def monitor_database_old_2():
    """ Demon sprawdza bazę i wykrywa nowe wizyty do obsługi """
    logging.info("🔄 Sprawdzanie bazy pod kątem nowych zgłoszeń...")

    # now = datetime.datetime.now()

    # 🔹 **1. Pobieramy zgłoszenia wymagające kontaktu z recepcją (TYLKO PRZYSZŁE WIZYTY)**
    raw_data = msq.connect_to_database(
        "SELECT * FROM appointment_requests WHERE status = 'in_progress' AND in_progress_flag = 0 AND visit_date >= CURDATE()"
    )
    visit_requests = [AppointmentRequest.from_tuple(row) for row in raw_data]

    for visit in visit_requests:
        daemon.add_task(5, handle_visit_request, visit)

        # 🔹 Oznaczamy w bazie, że powiadomienie zostało wysłane
        msq.insert_to_database(
            "UPDATE appointment_requests SET in_progress_flag = %s WHERE id = %s",
            (1, visit.id)
        )

        # 🔹 Pierwsze przypomnienie dla recepcji dodajemy **po 1h**, a nie od razu!
        daemon.add_task(3600, remind_reception, visit, daemon)

    # 🔹 **2. Pobieramy zgłoszenia wymagające przypomnienia dla recepcji (TYLKO PRZYSZŁE WIZYTY)**
    raw_data = msq.connect_to_database(
        "SELECT * FROM appointment_requests WHERE status = 'in_progress' AND in_progress_flag = 1 "
        "AND in_progress_date IS NULL AND visit_date >= CURDATE()"
    )
    pending_reception_reminders = [AppointmentRequest.from_tuple(row) for row in raw_data]

    for visit in pending_reception_reminders:
        if visit.reminder_count > 0:
            logging.info(f"⏳ Kolejne przypomnienie dla recepcji: {visit.to_dict()}")
            daemon.add_task(3600, remind_reception, visit, daemon)

    # 🔹 **3. Pobieramy tylko nowe potwierdzone wizyty z przyszłości**
    raw_data = msq.connect_to_database(
        "SELECT * FROM appointment_requests WHERE status = 'confirmed' AND confirmed_flag = 0 AND confirmed_date >= NOW()"
    )
    confirmed_visits = [AppointmentRequest.from_tuple(row) for row in raw_data]

    for visit in confirmed_visits:
        logging.info(f"📅 Planowanie przypomnień dla wizyty: {visit.to_dict()}")
        schedule_visit_reminders(visit, daemon)

        msq.insert_to_database(
            "UPDATE appointment_requests SET confirmed_flag = 1 WHERE id = %s",
            (visit.id,)
        )

    # 🔹 **4. Pobieramy odwołane wizyty i wysyłamy powiadomienie do pacjenta**
    raw_data = msq.connect_to_database(
        "SELECT * FROM appointment_requests WHERE status = 'cancelled' AND cancelled_flag = 0"
    )
    cancelled_visits = [AppointmentRequest.from_tuple(row) for row in raw_data]

    for visit in cancelled_visits:
        logging.info(f"⚠️ Odwołana wizyta – powiadomienie do pacjenta: {visit.to_dict()}")
        daemon.add_task(5, send_cancellation_email, visit)

        msq.insert_to_database(
            "UPDATE appointment_requests SET cancelled_flag = 1 WHERE id = %s",
            (visit.id,)
        )

    # 🔄 Demon sprawdza bazę co 30 sekund
    daemon.add_task(30, monitor_database)


def monitor_database_old():
    """ Demon sprawdza bazę i wykrywa nowe wizyty do obsługi """
    logging.info("🔄 Sprawdzanie bazy pod kątem nowych zgłoszeń...")

    # 🔹 **1. Pobieramy zgłoszenia wymagające kontaktu z recepcją (TYLKO PRZYSZŁE WIZYTY)**
    raw_data = msq.connect_to_database(
        "SELECT * FROM appointment_requests WHERE status = 'in_progress' AND in_progress_flag = 0 AND visit_date >= CURDATE()"
    )
    visit_requests = [AppointmentRequest.from_tuple(row) for row in raw_data]

    for visit in visit_requests:
        # logging.info(f"📩 Znaleziono nowe zgłoszenie: {visit.to_dict()}")
        daemon.add_task(5, handle_visit_request, visit)

        # 🔹 Oznaczamy w bazie, że powiadomienie zostało wysłane
        msq.insert_to_database(
            "UPDATE appointment_requests SET in_progress_flag = %s WHERE id = %s",
            (1, visit.id)
        )

    # 🔹 **2. Pobieramy zgłoszenia wymagające przypomnienia dla recepcji (TYLKO PRZYSZŁE WIZYTY)**
    raw_data = msq.connect_to_database(
        "SELECT * FROM appointment_requests WHERE status = 'in_progress' AND in_progress_flag = 1 AND in_progress_date IS NULL AND visit_date >= CURDATE()"
    )
    pending_reception_reminders = [AppointmentRequest.from_tuple(row) for row in raw_data]
    # logging.info(f"⏳ Dane pending_reception_reminders:\n {pending_reception_reminders}")

    for visit in pending_reception_reminders:
        logging.info(f"⏳ Przypomnienie dla recepcji: {visit.to_dict()}")
        daemon.add_task(300, remind_reception, visit, daemon)

    # 🔹 **3. Pobieramy tylko nowe potwierdzone wizyty z przyszłości**
    raw_data = msq.connect_to_database(
        "SELECT * FROM appointment_requests WHERE status = 'confirmed' AND confirmed_flag = 0 AND confirmed_date >= NOW()"
    )
    confirmed_visits = [AppointmentRequest.from_tuple(row) for row in raw_data]
    # logging.info(f"⏳ Dane confirmed_visits:\n {confirmed_visits}")


    for visit in confirmed_visits:
        logging.info(f"📅 Planowanie przypomnień dla wizyty: {visit.to_dict()}")
        schedule_visit_reminders(visit, daemon)

        msq.insert_to_database(
            "UPDATE appointment_requests SET confirmed_flag = 1 WHERE id = %s",
            (visit.id,)
        )

    # 🔹 **4. Pobieramy odwołane wizyty i wysyłamy powiadomienie do pacjenta**
    raw_data = msq.connect_to_database(
        "SELECT * FROM appointment_requests WHERE status = 'cancelled' AND cancelled_flag = 0"
    )
    cancelled_visits = [AppointmentRequest.from_tuple(row) for row in raw_data]
    # logging.info(f"⏳ Dane cancelled_visits:\n {cancelled_visits}")


    for visit in cancelled_visits:
        logging.info(f"⚠️ Odwołana wizyta – powiadomienie do pacjenta: {visit.to_dict()}")
        daemon.add_task(5, send_cancellation_email, visit)

        msq.insert_to_database(
            "UPDATE appointment_requests SET cancelled_flag = 1 WHERE id = %s",
            (visit.id,)
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
