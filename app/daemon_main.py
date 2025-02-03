import time
import signal
import logging
import threading
from daemon_heart import Daemon
from daemon_funk import handle_visit_request, remind_reception, schedule_visit_reminders

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
    """Cyklicznie sprawdza bazę i aktualizuje zadania w daemonie"""
    logging.info("🔄 Sprawdzanie bazy pod kątem nowych zgłoszeń...")

    # 🔹 Pobieramy zgłoszenia z MySQL (lub testowo używamy statycznej listy)
    visit_requests = [
        {"id": 1, "name": "Jan Kowalski", "email": "jan.kowalski@example.com", "status": "in_progress", "in_progress_date": None, "in_progress_flag": 0, "reminder_count": 0, "confirmed_date": None},
        {"id": 2, "name": "Anna Nowak", "email": "anna.nowak@example.com", "status": "confirmed", "in_progress_date": "2025-02-01 10:00:00", "in_progress_flag": 1, "reminder_count": 0, "confirmed_date": "2025-02-05 15:30:00"},
    ]

    for visit in visit_requests:
        if visit["status"] == "in_progress" and visit["in_progress_flag"] == 0:
            daemon.add_task(5, handle_visit_request, visit)  # Wysyłka pierwszego e-maila

        elif visit["status"] == "in_progress" and visit["in_progress_flag"] == 1 and visit["in_progress_date"] is None:
            if visit["reminder_count"] == 0:
                daemon.add_task(5, remind_reception, visit, daemon)

        # 🔹 Nowość: Jeśli status jest "confirmed", planujemy przypomnienia!
        elif visit["status"] == "confirmed" and visit["confirmed_date"]:
            schedule_visit_reminders(visit, daemon)

    daemon.add_task(30, monitor_database)  # Sprawdzamy bazę co 30 sekund

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
