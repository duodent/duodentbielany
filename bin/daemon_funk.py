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
        now = datetime.datetime.now()

        logging.info(f"✅ Potwierdzona wizyta dla: {visit.name}, Data: {confirmed_date}")

        # 🔹 Usunięcie zaplanowanych przypomnień dla recepcji o ustaleniu terminu
        daemon.remove_tasks_for_function(remind_reception, visit, arg_key="id")
        logging.info(f"🗑 Usunięto przypomnienia `remind_reception` dla wizyty ID {visit.id} – termin już ustalony.")
        
        # 🔹 Natychmiastowe powiadomienie dla pacjenta o potwierdzeniu wizyty
        logging.info(f"📩 Wysyłanie natychmiastowego powiadomienia o potwierdzeniu wizyty do pacjenta {visit.email}")
        send_patient_info_visit(visit)

        # 🔹 Natychmiastowe powiadomienie dla recepcji o potwierdzeniu terminu wizyty
        logging.info(f"📩 Wysyłanie natychmiastowego powiadomienia do recepcji")
        send_reception_info_visit(visit)

        # 🔹 Przypomnienie dla pacjenta – dzień przed wizytą o 12:00
        reminder_patient_1 = confirmed_date.replace(hour=12, minute=0, second=0) - datetime.timedelta(days=1)
        delay_patient_1 = (reminder_patient_1 - now).total_seconds()
        if delay_patient_1 > 0:
            daemon.add_task(delay_patient_1, send_patient_reminder, visit)
            logging.info(f"📅 Zaplanowano przypomnienie dla pacjenta dzień wcześniej o 12:00 (za {delay_patient_1 / 3600:.2f} godzin)")

        # 🔹 Przypomnienie dla pacjenta – godzinę przed wizytą
        reminder_patient_2 = confirmed_date - datetime.timedelta(hours=1)
        delay_patient_2 = (reminder_patient_2 - now).total_seconds()
        if delay_patient_2 > 0:
            daemon.add_task(delay_patient_2, send_patient_reminder, visit)
            logging.info(f"📅 Zaplanowano przypomnienie dla pacjenta godzinę przed wizytą o {reminder_patient_2.strftime('%H:%M')} (za {delay_patient_2 / 60:.2f} minut)")

        # 🔹 Przypomnienie dla recepcji – w dniu wizyty o 7:00 rano
        reminder_reception = confirmed_date.replace(hour=7, minute=0, second=0)
        delay_reception = (reminder_reception - now).total_seconds()
        if delay_reception > 0:
            daemon.add_task(delay_reception, send_reception_reminder, visit)
            logging.info(f"📅 Zaplanowano przypomnienie dla recepcji w dniu wizyty o 7:00 rano (za {delay_reception / 3600:.2f} godzin)")

        logging.info(f"✅ Wszystkie przypomnienia zaplanowane dla wizyty {visit.id}.")


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
    subject_patient = f"⚠️ Ważne: Twoja wizyta w Duodent Bielany została odwołana!"
    html_body_patient = html_body_dict.get('send_cancellation_email', '')\
        .replace("{{visit.name}}", visit.name)\
        .replace("{{visit.confirmed_date}}", visit.confirmed_date.strftime("%Y-%m-%d %H:%M") if isinstance(visit.confirmed_date, datetime.datetime) else "")

    send_html_email(subject_patient, html_body_patient, visit.email)
    logging.info(f"📩 Wysłano powiadomienie o odwołaniu wizyty do pacjenta {visit.name} ({visit.email})")

    """ Wysyła e-mail do recepcji o odwołaniu wizyty """
    email_reception = smtp_config.get('smtp_username')  # Adres recepcji
    subject_reception = f"📢 Odwołanie wizyty pacjenta: {visit.name}"
    html_body_reception = html_body_dict.get('send_cancellation_reception', '')\
        .replace("{{visit.name}}", visit.name)\
        .replace("{{visit.email}}", visit.email)\
        .replace("{{visit.phone}}", visit.phone)\
        .replace("{{visit.patient_type}}", visit.patient_type)\
        .replace("{{visit.link_hash}}", visit.link_hash)\
        .replace("{{visit.confirmed_date}}", visit.confirmed_date.strftime("%Y-%m-%d %H:%M") if isinstance(visit.confirmed_date, datetime.datetime) else visit.visit_date.strftime("%Y-%m-%d"))
    send_html_email(subject_reception, html_body_reception, email_reception)
    logging.info(f"📩 Wysłano powiadomienie do recepcji ({email_reception}) o odwołaniu wizyty pacjenta {visit.name}.")


def send_patient_info_visit(visit):
    """ Wysyła powiadomienie do pacjenta o potwierdzeniu wizyty """
    subject = f"✅ Twoja wizyta w Duodent Bielany została potwierdzona – {visit.confirmed_date.strftime('%Y-%m-%d %H:%M')}"
    html_body = html_body_dict.get('send_patient_info_visit', '')\
        .replace("{{visit.name}}", visit.name)\
        .replace("{{visit.confirmed_date}}", visit.confirmed_date.strftime("%Y-%m-%d %H:%M") if isinstance(visit.confirmed_date, datetime.datetime) else "")

    send_html_email(subject, html_body, visit.email)
    logging.info(f"📩 Wysłano powiadomienie o potwierdzeniu wizyty do pacjenta {visit.name} ({visit.email})")


def send_reception_info_visit(visit):
    """ Wysyła powiadomienie do recepcji o potwierdzeniu terminu wizyty """
    email_reception = smtp_config.get('smtp_username')  # Adres recepcji
    subject = f"✅ Wizyta pacjenta {visit.name} została potwierdzona na {visit.confirmed_date.strftime('%H:%M')}"
    html_body = html_body_dict.get('send_reception_info_visit', '')\
        .replace("{{visit.name}}", visit.name) \
        .replace("{{visit.email}}", visit.email) \
        .replace("{{visit.phone}}", visit.phone) \
        .replace("{{visit.patient_type}}", visit.patient_type)\
        .replace("{{visit.link_hash}}", visit.link_hash)\
        .replace("{{visit.confirmed_date}}", visit.confirmed_date.strftime("%Y-%m-%d %H:%M") if isinstance(visit.confirmed_date, datetime.datetime) else "")

    send_html_email(subject, html_body, email_reception)
    logging.info(f"📩 Wysłano powiadomienie do recepcji ({email_reception}) o potwierdzeniu wizyty pacjenta {visit.name}.")