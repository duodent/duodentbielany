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

class AppointmentRequest:
    """ Obiekt reprezentujący wizytę pacjenta """
    def __init__(self, id, name, email, phone, patient_type, visit_date, consent, status, created_at,
                 in_progress_date, in_progress_description, in_progress_flag, verified_date, verified_description,
                 verified_flag, confirmed_date, confirmed_description, confirmed_flag, cancelled_date,
                 cancelled_description, cancelled_flag, error_date, error_description, error_flag, link_hash):

        self.id = id
        self.name = name
        self.email = email
        self.phone = phone
        self.patient_type = patient_type
        self.visit_date = visit_date
        self.consent = consent
        self.status = status
        self.created_at = created_at
        self.in_progress_date = in_progress_date
        self.in_progress_description = in_progress_description
        self.in_progress_flag = in_progress_flag
        self.verified_date = verified_date
        self.verified_description = verified_description
        self.verified_flag = verified_flag
        self.confirmed_date = confirmed_date
        self.confirmed_description = confirmed_description
        self.confirmed_flag = confirmed_flag
        self.cancelled_date = cancelled_date
        self.cancelled_description = cancelled_description
        self.cancelled_flag = cancelled_flag
        self.error_date = error_date
        self.error_description = error_description
        self.error_flag = error_flag
        self.link_hash = link_hash

    @classmethod
    def from_tuple(cls, data):
        """ Tworzy obiekt `AppointmentRequest` z krotki (dane z MySQL) """
        return cls(*data)

    def to_dict(self):
        """ Konwertuje obiekt na słownik (przydatne do logowania/debugowania) """
        return self.__dict__

# **NOWE: Funkcja cyklicznie sprawdzająca bazę i aktualizująca zadania**
def monitor_database():
    """ Demon sprawdza bazę i wykrywa nowe wizyty do obsługi """
    logging.info("🔄 Sprawdzanie bazy pod kątem nowych zgłoszeń...")

    # 🔹 **1. Pobieramy zgłoszenia wymagające kontaktu z recepcją**
    raw_data = msq.connect_to_database(
        "SELECT * FROM appointment_requests WHERE status = 'in_progress' AND in_progress_flag = 0"
    )
    visit_requests = [AppointmentRequest.from_tuple(row) for row in raw_data]

    for visit in visit_requests:
        logging.info(f"📩 Znaleziono nowe zgłoszenie: {visit.to_dict()}")
        daemon.add_task(5, handle_visit_request, visit)

        # 🔹 Oznaczamy w bazie, że powiadomienie zostało wysłane
        msq.insert_to_database(
            "UPDATE appointment_requests SET in_progress_flag = %s WHERE id = %s",
            (1, visit.id)
        )

    # 🔹 **2. Pobieramy zgłoszenia wymagające przypomnienia dla recepcji**
    raw_data = msq.connect_to_database(
        "SELECT * FROM appointment_requests WHERE status = 'in_progress' AND in_progress_flag = 1 AND in_progress_date IS NULL"
    )
    pending_reception_reminders = [AppointmentRequest.from_tuple(row) for row in raw_data]

    for visit in pending_reception_reminders:
        logging.info(f"⏳ Przypomnienie dla recepcji: {visit.to_dict()}")
        daemon.add_task(10, remind_reception, visit, daemon)

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
