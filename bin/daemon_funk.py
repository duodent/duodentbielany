import logging
import datetime 
from sendEmailBySmtp import send_html_email, smtp_config
import mysqlDB as msq


def handle_visit_request(visit):
    """Obsługa zgłoszenia wizyty"""
    if visit["status"] == "in_progress" and not visit["in_progress_date"] and visit["in_progress_flag"] == 0:
        logging.info(f"📩 Wysyłanie e-maila do recepcji: {visit['email']} (Zgłoszenie ID: {visit['id']})")

        # 📌 Treść e-maila
        subject = "Nowe zgłoszenie wizyty"
        html_body = f"""
        <html>
        <body>
            <h2>Nowe zgłoszenie wizyty</h2>
            <p>Pacjent: <strong>{visit['name']}</strong></p>
            <p>Prosimy o obsługę zgłoszenia.</p>
        </body>
        </html>
        """

        # 🔹 Wysyłamy e-mail
        email_reception = smtp_config.get('smtp_username')
        if email_reception: send_html_email(subject, html_body, email_reception)

        # 🔹 Aktualizacja bazy (zakomentowane – odkomentuj, gdy chcesz używać MySQL)
        msq.safe_connect_to_database("UPDATE appointment_requests SET in_progress_flag = %s WHERE id = %s", (2, visit["id"]))

        logging.info(f"✅ E-mail wysłany do {visit['email']} i zadanie oznaczone jako wykonane (ID: {visit['id']})")


def remind_reception(visit, daemon):
    """Przypomnienie recepcji o nieobsłużonym zgłoszeniu"""
    if visit["in_progress_flag"] == 1 and visit["in_progress_date"] is None:
        intervals = [300, 600, 1800, 3600]  # 5 min, 10 min, 30 min, 1 godz.
        reminder_idx = visit["reminder_count"]

        if reminder_idx >= len(intervals):
            logging.info(f"⚠️ Maksymalna liczba przypomnień wysłana dla zgłoszenia {visit['id']}.")
            return
        
        visit["reminder_count"] += 1
        delay = intervals[reminder_idx]

        # 📌 Treść przypomnienia
        subject = "Przypomnienie o zgłoszeniu wizyty"
        html_body = f"""
        <html>
        <body>
            <h2>Przypomnienie o zgłoszeniu</h2>
            <p>Pacjent: <strong>{visit['name']}</strong></p>
            <p>To zgłoszenie wymaga obsługi.</p>
        </body>
        </html>
        """

        # 📌 Wysyłamy przypomnienie
        email_reception = smtp_config.get('smtp_username')
        if email_reception: send_html_email(subject, html_body, email_reception)

        # 📌 Aktualizacja licznika w MySQL (zakomentowane – odkomentuj, gdy chcesz używać MySQL)
        msq.safe_connect_to_database("UPDATE appointment_requests SET reminder_count = %s WHERE id = %s", (visit["reminder_count"], visit["id"]))

        logging.info(f"⏳ Przypomnienie #{visit['reminder_count']} wysłane do {visit['email']}. Kolejne za {delay//60} min.")
        
        daemon.add_task(delay, remind_reception, visit, daemon)


def schedule_visit_reminders(visit, daemon):
    """ Tworzy zadania przypomnień dla pacjenta i recepcji """

    if visit["status"] == "confirmed" and visit["confirmed_date"]:
        confirmed_date = datetime.datetime.strptime(visit["confirmed_date"], "%Y-%m-%d %H:%M:%S")

        # 🔹 Przypomnienie dla pacjenta – dzień przed wizytą
        reminder_patient_1 = confirmed_date - datetime.timedelta(days=1)
        daemon.add_task((reminder_patient_1 - datetime.datetime.now()).total_seconds(), send_patient_reminder, visit)

        # 🔹 Przypomnienie dla pacjenta – w dniu wizyty
        reminder_patient_2 = confirmed_date.replace(hour=8, minute=0, second=0)  # 8:00 rano w dniu wizyty
        daemon.add_task((reminder_patient_2 - datetime.datetime.now()).total_seconds(), send_patient_reminder, visit)

        # 🔹 Przypomnienie dla recepcji – o 7:00 rano w dniu wizyty
        reminder_reception = confirmed_date.replace(hour=7, minute=0, second=0)
        daemon.add_task((reminder_reception - datetime.datetime.now()).total_seconds(), send_reception_reminder, visit)

        logging.info(f"✅ Zadania przypomnień zaplanowane dla wizyty {visit['id']}.")

def send_patient_reminder(visit):
    """ Wysyła przypomnienie do pacjenta o wizycie """
    subject = "Przypomnienie o wizycie – DMD"
    html_body = f"""
    <html>
    <body>
        <h2>Przypomnienie o Twojej wizycie</h2>
        <p>Drogi {visit['name']},</p>
        <p>Przypominamy, że Twoja wizyta odbędzie się: <strong>{visit['confirmed_date']}</strong></p>
        <p>Jeśli masz pytania, skontaktuj się z naszą recepcją.</p>
    </body>
    </html>
    """
    send_html_email(subject, html_body, visit["email"])
    logging.info(f"📩 Wysłano przypomnienie do pacjenta {visit['name']} ({visit['email']})")

def send_reception_reminder(visit):
    """ Wysyła przypomnienie do recepcji o wizycie pacjenta """
    email_reception = smtp_config.get('smtp_username')  # Adres recepcji
    subject = "🗓 Przypomnienie o dzisiejszych wizytach"
    html_body = f"""
    <html>
    <body>
        <h2>Dzisiejsze wizyty</h2>
        <p>Prosimy o sprawdzenie grafiku wizyt na dziś.</p>
        <p>Pacjent: <strong>{visit['name']}</strong></p>
        <p>Planowana godzina wizyty: <strong>{visit['confirmed_date']}</strong></p>
    </body>
    </html>
    """
    send_html_email(subject, html_body, email_reception)
    logging.info(f"📩 Wysłano przypomnienie do recepcji ({email_reception}) o wizycie pacjenta {visit['name']}.")

def send_cancellation_email(visit):
    """ Wysyła e-mail do pacjenta o odwołaniu wizyty """
    subject = "⚠️ Odwołanie wizyty – DMD"
    html_body = f"""
    <html>
    <body>
        <h2>Twoja wizyta została odwołana</h2>
        <p>Drogi {visit['name']},</p>
        <p>Informujemy, że Twoja wizyta została odwołana przez recepcję.</p>
        <p>W razie pytań skontaktuj się z nami.</p>
    </body>
    </html>
    """
    send_html_email(subject, html_body, visit["email"])
    logging.info(f"📩 Wysłano powiadomienie o odwołaniu wizyty do {visit['name']} ({visit['email']})")
