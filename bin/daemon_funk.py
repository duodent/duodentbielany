import logging
import datetime 
from sendEmailBySmtp import send_html_email, smtp_config
import mysqlDB as msq
from HTMLbody import html_body_dict


def handle_visit_request(visit):
    """Obsługa zgłoszenia wizyty"""
    if visit.status == "in_progress" and not visit.in_progress_date and visit.in_progress_flag == 0:
        logging.info(f"📩 Wysyłanie e-maila do recepcji: {visit.email} (Zgłoszenie ID: {visit.id})")

        # 📌 Treść e-maila
        subject = f"⏳ Potwierdzenie rezerwacji wizyty – wymagana godzina dla pacjenta: {visit.name}"
        html_body = html_body_dict.get('handle_visit_request', '') \
            .replace("{{visit.name}}", visit.name) \
            .replace("{{visit.email}}", visit.email) \
            .replace("{{visit.phone}}", visit.phone) \
            .replace("{{visit.visit_date}}", visit.visit_date.strftime("%Y-%m-%d"))\
            .replace("{{visit.patient_type}}", visit.patient_type)\
            .replace("{{visit.link_hash}}", visit.link_hash)
            

        # 🔹 Wysyłamy e-mail
        email_reception = smtp_config.get('smtp_username')
        if email_reception: send_html_email(subject, html_body, email_reception)

        # 🔹 Aktualizacja bazy (zakomentowane – odkomentuj, gdy chcesz używać MySQL)
        msq.insert_to_database(
                "UPDATE appointment_requests SET in_progress_flag = %s WHERE id = %s", 
                (2, visit.id)
            )

        logging.info(f"✅ E-mail wysłany do {visit.email} i zadanie oznaczone jako wykonane (ID: {visit.id})")


def remind_reception(visit, daemon):
    """Przypomnienie recepcji o nieobsłużonym zgłoszeniu"""
    if visit.in_progress_flag == 1 and visit.in_progress_date is None:
        intervals = [3600, 7200, 9000, 14400] 
        reminder_idx = visit.reminder_count

        if reminder_idx >= len(intervals):
            logging.info(f"⚠️ Maksymalna liczba przypomnień wysłana dla zgłoszenia {visit.id}.")
            return
        
        visit.reminder_count += 1
        delay = intervals[reminder_idx]

        # 📌 Treść przypomnienia
        subject = f"⚠️ Pilne: wybierz godzinę dla zgłoszonej wizyty dla pacjenta: {visit.name}"
        html_body = html_body_dict.get('remind_reception', '')\
            .replace("{{visit.name}}", visit.name) \
            .replace("{{visit.email}}", visit.email) \
            .replace("{{visit.phone}}", visit.phone) \
            .replace("{{visit.visit_date}}", visit.visit_date.strftime("%Y-%m-%d"))\
            .replace("{{visit.patient_type}}", visit.patient_type)\
            .replace("{{visit.link_hash}}", visit.link_hash)

        # 📌 Wysyłamy przypomnienie
        email_reception = smtp_config.get('smtp_username')
        if email_reception: send_html_email(subject, html_body, email_reception)

        # 📌 Aktualizacja licznika w MySQL **ZMIANA - używamy insert_to_database() zamiast safe_connect_to_database()**
        update_success = msq.insert_to_database(
            "UPDATE appointment_requests SET reminder_count = %s WHERE id = %s", 
            (visit.reminder_count, visit.id)
        )

        if update_success:
            logging.info(f"✅ reminder_count zaktualizowany do {visit.reminder_count} dla zgłoszenia {visit.id}")
        else:
            logging.error(f"❌ Błąd przy aktualizacji reminder_count dla zgłoszenia {visit.id}")

        logging.info(f"⏳ Przypomnienie #{visit.reminder_count} wysłane do {email_reception}. Kolejne za {delay//60} min.")
        
        daemon.add_task(delay, remind_reception, visit, daemon)


def schedule_visit_reminders(visit, daemon):
    """ Tworzy zadania przypomnień dla pacjenta i recepcji """

    if visit.status == "confirmed" and visit.confirmed_date:
        confirmed_date = visit.confirmed_date  # ✅ Już jest datetime.datetime, nie trzeba parsować!
        logging.info(f"✅ dane confirmed: {visit}.")

        # 🔹 Natychmiastowe powiadomienie dla pacjenta o potwierdzeniu wizyty
        logging.info(f"📩 Wysyłanie powiadomienia o potwierdzeniu wizyty do pacjenta {visit.email}")
        send_patient_reminder(visit)

        # 🔹 Natychmiastowe powiadomienie dla recepcji o potwierdzeniu terminu wizyty
        logging.info(f"📩 Wysyłanie powiadomienia o potwierdzeniu terminu do recepcji")
        send_reception_reminder(visit)

        # 🔹 Przypomnienie dla pacjenta – dzień przed wizytą
        reminder_patient_1 = confirmed_date - datetime.timedelta(days=1)
        daemon.add_task((reminder_patient_1 - datetime.datetime.now()).total_seconds(), send_patient_reminder, visit)

        # 🔹 Przypomnienie dla pacjenta – w dniu wizyty
        reminder_patient_2 = confirmed_date.replace(hour=8, minute=0, second=0)  # 8:00 rano w dniu wizyty
        daemon.add_task((reminder_patient_2 - datetime.datetime.now()).total_seconds(), send_patient_reminder, visit)

        # 🔹 Przypomnienie dla recepcji – o 7:00 rano w dniu wizyty
        reminder_reception = confirmed_date.replace(hour=7, minute=0, second=0)
        daemon.add_task((reminder_reception - datetime.datetime.now()).total_seconds(), send_reception_reminder, visit)

        logging.info(f"✅ Zadania przypomnień zaplanowane dla wizyty {visit.id}.")

def send_patient_reminder(visit):
    """ Wysyła przypomnienie do pacjenta o wizycie """
    subject = f"🦷 Przypomnienie: Twoja wizyta w Duodent Bielany {visit.confirmed_date.strftime('%Y-%m-%d %H:%M')}"
    html_body = html_body_dict.get('send_patient_reminder', '')\
        .replace("{{visit.name}}", visit.name)\
        .replace("{{visit.confirmed_date}}", visit.confirmed_date.strftime("%Y-%m-%d %H:%M") if isinstance(visit.confirmed_date, datetime.datetime) else "")

    send_html_email(subject, html_body, visit.email)
    logging.info(f"📩 Wysłano przypomnienie do pacjenta {visit.name} ({visit.email})")

def send_reception_reminder(visit):
    """ Wysyła przypomnienie do recepcji o wizycie pacjenta """
    email_reception = smtp_config.get('smtp_username')  # Adres recepcji
    subject = f"📅 Przypomnienie: Wizyta pacjenta {visit.name} o {visit.confirmed_date.strftime('%H:%M')}"
    html_body = html_body_dict.get('send_reception_reminder', '')\
        .replace("{{visit.name}}", visit.name) \
        .replace("{{visit.email}}", visit.email) \
        .replace("{{visit.phone}}", visit.phone) \
        .replace("{{visit.patient_type}}", visit.patient_type)\
        .replace("{{visit.link_hash}}", visit.link_hash)\
        .replace("{{visit.confirmed_date}}", visit.confirmed_date.strftime("%Y-%m-%d %H:%M") if isinstance(visit.confirmed_date, datetime.datetime) else "")

    send_html_email(subject, html_body, email_reception)
    logging.info(f"📩 Wysłano przypomnienie do recepcji ({email_reception}) o wizycie pacjenta {visit.name}.")

def send_cancellation_email(visit):
    """ Wysyła e-mail do pacjenta o odwołaniu wizyty """
    subject = f"⚠️ Ważne: Twoja wizyta w Duodent Bielany została odwołana!"
    html_body = html_body_dict.get('send_cancellation_email', '')\
        .replace("{{visit.name}}", visit.name)\
        .replace("{{visit.confirmed_date}}", visit.confirmed_date.strftime("%Y-%m-%d %H:%M") if isinstance(visit.confirmed_date, datetime.datetime) else "")

    send_html_email(subject, html_body, visit.email)
    logging.info(f"📩 Wysłano powiadomienie o odwołaniu wizyty do {visit.name} ({visit.email})")
