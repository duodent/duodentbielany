import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
global smtp_config
# from config_utils import smtp_config
from mysqlDB import connect_to_database
table_setting = 'system_setting'
smtp_config = {
    'smtp_server': connect_to_database(f'SELECT config_smtp_server FROM {table_setting};')[0][0],
    'smtp_port': connect_to_database(f'SELECT config_smtp_port FROM {table_setting};')[0][0],  # Domyślny port dla TLS
    'smtp_username': connect_to_database(f'SELECT config_smtp_username FROM {table_setting};')[0][0],
    'smtp_password': connect_to_database(f'SELECT config_smtp_password FROM {table_setting};')[0][0]
}

from bin.appslib import handle_error

def send_html_email(subject, html_body, to_email):
    try:
        # Utwórz wiadomość
        message = MIMEMultipart()
        smtp_server = smtp_config['smtp_server']
        smtp_port =smtp_config['smtp_port']
        smtp_username = smtp_config['smtp_username']
        smtp_password = smtp_config['smtp_password']
        message["From"] = smtp_username
        message["To"] = to_email
        message["Subject"] = subject
        

        # Dodaj treść HTML
        message.attach(MIMEText(html_body, "html"))
        print(smtp_config)
        # Utwórz połączenie z serwerem SMTP
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            # Rozszerzenie STARTTLS
            server.starttls()
            # Zaloguj się do konta SMTP
            server.login(smtp_username, smtp_password)

            # Wyślij wiadomość
            server.sendmail(smtp_username, to_email, message.as_string())
    except Exception as e:
        handle_error(f'Wysyłanie  maila do {to_email} nieudane: {e}', './logs/errors.log')

if __name__ == "__main__":
    
    # Przykładowe dane
    subject = "Testy"
    html_body = "<html><body><h1>Witaj!</h1><p>To jest treść wiadomości HTML.</p></body></html>"
    to_email = "informatyk@dmdbudownictwo.pl"


    # Wywołaj funkcję wysyłania e-maila HTML
    send_html_email(subject, html_body, to_email)
