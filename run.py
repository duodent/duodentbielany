from flask import Flask, render_template, redirect, url_for, jsonify, session, request, send_from_directory, Response, abort, flash
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired
import app.utils.passwordSalt as hash
from flask_paginate import Pagination, get_page_args
import mysqlDB as msq
import secrets
from datetime import datetime, timedelta
# from googletrans import Translator
import random
import re
import os
from flask_session import Session

app = Flask(__name__)

# Klucz tajny do szyfrowania sesji
app.config['SECRET_KEY'] = secrets.token_hex(16)

# Ustawienia dla Flask-Session
app.config['SESSION_TYPE'] = 'filesystem'  # Można użyć np. 'redis', 'sqlalchemy'
app.config['SESSION_PERMANENT'] = True  # Sesja ma być permanentna
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=10)  # Czas wygaśnięcia sesji (10 minut)

# Ścieżka do katalogu z plikami
UPLOAD_FOLDER = 'dokumenty'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ustawienie ilości elementów na stronę (nie dotyczy sesji)
app.config['PER_PAGE'] = 6

# Inicjalizacja obsługi sesji
Session(app)

class LoginForm(FlaskForm):
    username = StringField('Nazwa użytkownika', validators=[DataRequired()])
    password = PasswordField('Hasło', validators=[DataRequired()])
    submit = SubmitField('Zaloguj się')

# def getLangText(text):
#     """Funkcja do tłumaczenia tekstu z polskiego na angielski"""
#     translator = Translator()
#     translation = translator.translate(str(text), dest='en')
#     return translation.text

def format_date(date_input, pl=True):
    ang_pol = {
        'January': 'styczeń',
        'February': 'luty',
        'March': 'marzec',
        'April': 'kwiecień',
        'May': 'maj',
        'June': 'czerwiec',
        'July': 'lipiec',
        'August': 'sierpień',
        'September': 'wrzesień',
        'October': 'październik',
        'November': 'listopad',
        'December': 'grudzień'
    }
    # Sprawdzenie czy data_input jest instancją stringa; jeśli nie, zakładamy, że to datetime
    if isinstance(date_input, str):
        date_object = datetime.strptime(date_input, '%Y-%m-%d %H:%M:%S')
    else:
        # Jeśli date_input jest już obiektem datetime, używamy go bezpośrednio
        date_object = date_input

    formatted_date = date_object.strftime('%d %B %Y')
    if pl:
        for en, pl in ang_pol.items():
            formatted_date = formatted_date.replace(en, pl)

    return formatted_date


#  Funkcja pobiera dane z bazy danych 
def take_data_where_ID(key, table, id_name, ID):
    dump_key = msq.connect_to_database(f'SELECT {key} FROM {table} WHERE {id_name} = {ID};')
    return dump_key

def take_data_table(key, table):
    dump_key = msq.connect_to_database(f'SELECT {key} FROM {table};')
    return dump_key

def generator_userDataDB():
    took_usrD = take_data_table('*', 'admins')
    userData = []

    # Klucze dla uprawnień i kontaktów
    permissions_keys = ['administrator', 'super_user', 'user']
    contact_keys = ['phone', 'facebook', 'instagram', 'twitter', 'linkedin']

    for data in took_usrD:
        theme = {
            'id': data[0],  # ID użytkownika
            'login': data[1],  # Login użytkownika
            'name': data[2],  # Imię i nazwisko
            'stanowisko': data[3],  # Stanowisko
            'kwalifikacje': data[4],  # Kwalifikacje
            'doswiadczenie': data[5],  # Doświadczenie zawodowe
            'wyksztalcenie': data[6],  # Wykształcenie
            'opis': data[7],  # Opis pracownika
            'email': data[8],  # Adres email
            'password': data[9],  # Hasło
            'salt': data[10],  # Sól dla hasła
            'avatar': data[11] if data[11] else '',  # Ścieżka do zdjęcia (jeśli istnieje)
            'uprawnienia': {
                key: data[12 + i] for i, key in enumerate(permissions_keys)
            },
            'contact': {
                key: data[15 + i] if data[15 + i] else '' for i, key in enumerate(contact_keys)
            },
            'status_usera': data[20]
        }
        userData.append(theme)

    return userData

############################
##      ######           ###
##      ######           ###
##     ####              ###
##     ####              ###
##    ####               ###
##    ####               ###
##   ####                ###
##   ####                ###
#####                    ###
#####                    ###
##   ####                ###
##   ####                ###
##    ####               ###
##    ####               ###
##     ####              ###
##     ####              ###
##      ######           ###
##      ######           ###
############################



@app.template_filter('smart_truncate')
def smart_truncate(content, length=400):
    if len(content) <= length:
        return content
    else:
        # Znajdujemy miejsce, gdzie jest koniec pełnego słowa, nie przekraczając maksymalnej długości
        truncated_content = content[:length].rsplit(' ', 1)[0]
        return f"{truncated_content}..."


@app.route('/robots.txt', methods=['GET'])
def robots():
    robots_content = """
    User-agent: *
    Disallow: /admin/
    Disallow: /private/
    Disallow: /tmp/
    Allow: /

    Sitemap: https://www.duodentbielany.pl/sitemap.xml
    """
    return Response(robots_content, mimetype='text/plain')

@app.route('/sitemap.xml', methods=['GET'])
def serve_sitemap():
    return send_from_directory(directory='.', path='sitemap.xml', mimetype='application/xml')

@app.route('/favicon.png')
def favicon():
    return send_from_directory(
        directory='static/img',
        path='favicon.png',
        mimetype='image/png'
    )



# ERROR 404
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html', pageTitle='Strona nie znaleziona'), 404

# ERROR 500
@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html', pageTitle='Błąd serwera'), 500

@app.route('/admin')
def admin():
    if 'username' in session:
        # username = session['username']
        return redirect(url_for('index'))
    return render_template('gateway.html', form=LoginForm())

@app.route('/admin/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        # Pobierz dane użytkowników z bazy
        userDataDB = generator_userDataDB()
        print(userDataDB)
        # Przygotowanie struktur do weryfikacji
        usersTempDict = {}
        users_data = {}
        permTempDict = {}

        for un in userDataDB:
            usersTempDict[un['login']] = {
                'hashed_password': un['password'],
                'salt': un['salt']
            }
            permTempDict[un['login']] = un['uprawnienia']
            users_data[un['login']] = {
                'id': un['id'],
                'name': un['name'],
                'stanowisko': un['stanowisko'],
                'opis': un['opis'],
                'email': un['email'],
                'avatar': un['avatar'],
                'contact': un['contact'],
                'status': un['status_usera']  # Zakładam, że aktywność konta jest ustawiana tutaj status_usera
            }


        # weryfikacja danych użytkownika
        if username in usersTempDict and \
            hash.hash_password(
                password, usersTempDict[username]['salt']
                ) == usersTempDict[username]['hashed_password'] and \
                    int(users_data[username]['status']) == 1:
            
            session['username'] = username
            session['userperm'] = permTempDict[username]
            session['user_data'] = users_data[username]

            return redirect(url_for('index'))
        elif username in users_data and users_data.get(username, {}).get('status') == '0':
            flash('Konto nie aktywne!', 'danger')
        else:
            flash('Błędne nazwa użytkownika lub hasło', 'danger')
    return render_template('gateway.html', form=form)

@app.route('/admin/logout')
def logout():
    if "username" in session:
        session.pop('username', None)
        session.pop('userperm', None)
        session.pop('user_data', None)

    return redirect(url_for('index'))

@app.route('/admin/rejestracja')
def rejestracja():
    session['page'] = 'rejestracja'
    pageTitle = 'Rejestracja użytkownika'
    return render_template(
        'register.html',
        pageTitle=pageTitle
    )

# Strona główna
@app.route('/')
def index():
    session['page'] = 'index'
    pageTitle = 'Strona Główna'

    return render_template(
        'index.html',
        pageTitle=pageTitle
    )


# Poznaj nas bliżej
@app.route('/o-nas-twoja-klinika-stomatologiczna')
def about_us():
    session['page'] = 'about_us'
    pageTitle = 'Poznaj nas bliżej'
    return render_template(
        'about_us.html',
        pageTitle=pageTitle
    )

# Zabiegi - lista
@app.route('/zabiegi-stomatologiczne-kompleksowa-oferta')
def treatments():
    session['page'] = 'treatments'
    pageTitle = 'Zabiegi'
    return render_template(
        'treatments.html',
        pageTitle=pageTitle
    )

treatments_dict = {
    'ortodoncja-aparaty-na-prosty-usmiech': 'Ortodoncja',
    'chirurgia-stomatologiczna-implantologia-odbudowa-usmiechu': 'Chirurgia i Implantologia',
    'protetyka-stomatologiczna-estetyczna-odbudowa': 'Protetyka',
    'endodoncja-leczenie-kanalowe-precyzyjnie': 'Endodoncja',
    'periodontologia-choroby-przyzebia-leczenie': 'Periodontologia',
    'nowoczesna-diagnostyka-rtg-i-scanner-3d': 'Nowoczesna diagnostyka',
    'profilaktyka-stomatologiczna-higienizacja-i-wybielanie': 'Profilaktyka',
    'stomatologia-dziecieca-zdrowy-usmiech-dziecka': 'Stomatologia dziecięca'
}

@app.route('/zabieg-stomatologiczny/<path:treatment_slug>')
def treatment_dynamic(treatment_slug):
    if treatment_slug in treatments_dict:
        pageTitle = treatments_dict[treatment_slug]
        session['page'] = treatment_slug
        return render_template(
            'treatment_details.html',
            pageTitle=pageTitle,
            nazwa_uslugi=treatments_dict[treatment_slug]
        )
    else:
        abort(404)

# Zespół
@app.route('/poznaj-nasz-zespol-specjalistow-stomatologii')
def team():
    session['page'] = 'team'
    pageTitle = 'Zespół'
    return render_template(
        'team.html',
        pageTitle=pageTitle
    )

# Szczegóły członka zespołu
team_memeber_dict = {
    'doktor-nauk-medycznych-elzbieta-fedorowicz': 1,
    'lekarz-dentysta-arkadiusz-zmuda': 2,
    'lekarz-dentysta-przemyslaw-zmuda': 3,
    'lekarz-dentysta-sylwia-zmuda': 4
}

@app.route('/zespol/<string:name_pracownika>')
def team_mambers(name_pracownika):
    if name_pracownika in team_memeber_dict:
        idPracownika = team_memeber_dict[name_pracownika]
        ready_name = name_pracownika.replace('-', ' ').capitalize()
        pageTitle = ready_name
        session['page'] = ready_name
        return render_template(
            'team_member.html',
            pageTitle=pageTitle,
            dane_pracownika=team_memeber_dict[name_pracownika]
        )
    else:
        abort(404)

# Dla Pacjenta
@app.route('/informacje-dla-pacjentow-stomatologicznych')
def for_patients():
    session['page'] = 'for_patients'
    pageTitle = 'Dla Pacjenta'
    return render_template(
        'for_patients.html',
        pageTitle=pageTitle
    )

@app.route('/dokumenty/<path:filename>')
def download_file(filename):
    # Sprawdź, czy plik istnieje w katalogu
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)
    else:
        # Zwróć błąd 404, jeśli plik nie istnieje
        abort(404)

# Polityka Prywatności
@app.route('/polityka-prywatnosci')
def privacy_policy():
    session['page'] = 'privacy_policy'
    pageTitle = 'Polityka Prywatności'
    return render_template(
        'privacy_policy.html',
        pageTitle=pageTitle
    )

# FAQ
@app.route('/faq')
def faq():
    session['page'] = 'faq'
    pageTitle = 'FAQ'
    return render_template(
        'faq.html',
        pageTitle=pageTitle
    )

# Zasady Witryny
@app.route('/zasady-witryny')
def site_rules():
    session['page'] = 'site_rules'
    pageTitle = 'Zasady Witryny'
    return render_template(
        'site_rules.html',
        pageTitle=pageTitle
    )

# Kontakt
# Strona kontaktu
@app.route('/kontakt-z-klinika-stomatologiczna', methods=['GET'])
def contact_page():
    session['page'] = 'kontakt'
    pageTitle = 'Kontakt z kliniką stomatologiczną'
    return render_template('contact.html', pageTitle=pageTitle)

# API do obsługi formularza i danych JSON
@app.route('/api/kontakt', methods=['POST'])
def contact_api():
    if request.is_json:
        # Obsługa danych JSON
        data = request.get_json()
        name = data.get('name')
        email = data.get('email')
        message = data.get('message')
        # Możesz tutaj zapisać dane do bazy lub wysłać e-mail
        return jsonify({
            "status": "success",
            "message": "Dziękujemy za kontakt!",
            "data": {
                "name": name,
                "email": email,
                "message": message
            }
        }), 200
    else:
        # Obsługa formularza HTML
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')
        # Możesz tutaj zapisać dane do bazy lub wysłać e-mail
        return render_template(
            'contact_success.html',
            pageTitle='Dziękujemy za kontakt!',
            name=name,
            email=email,
            message=message
        )

@app.route('/umow-wizyte-online', methods=['GET'])
def book_appointment_page():
    session['page'] = 'umow_wizyte_online'
    pageTitle = 'Umów wizytę online'
    return render_template('book_appointment.html', pageTitle=pageTitle)

@app.route('/api/umow-wizyte', methods=['POST'])
def book_appointment_api():
    # Sprawdzamy, czy dane zostały przesłane w formacie JSON
    if request.is_json:
        data = request.get_json()
        name = data.get('name')
        email = data.get('email')
        phone = data.get('phone')
        birth_date = data.get('birth_date')
        visit_date = data.get('visit_date')
        visit_time = data.get('visit_time')
        consent = data.get('consent')

        # Walidacja checkboxa zgody
        if not consent:
            return jsonify({"status": "error", "message": "Musisz wyrazić zgodę na przetwarzanie danych osobowych."}), 400

        # Tutaj możesz zapisać dane do bazy lub wysłać e-mail
        return jsonify({
            "status": "success",
            "message": "Rezerwacja przyjęta!",
            "data": {
                "name": name,
                "email": email,
                "phone": phone,
                "birth_date": birth_date,
                "visit_date": visit_date,
                "visit_time": visit_time
            }
        }), 200
    else:
        return jsonify({"status": "error", "message": "Nieprawidłowy format danych"}), 400


if __name__ == '__main__':
    # app.run(debug=True, port=5000)
    app.run(debug=True, host='0.0.0.0', port=5000)