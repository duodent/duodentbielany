from flask import Flask, render_template, redirect, url_for, jsonify, session, request, send_from_directory, Response, abort, flash
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired
import imghdr
from werkzeug.utils import secure_filename
from PIL import Image
import redis
from bin.config_utils import SESSION_FLASK_KEY
import app.utils.passwordSalt as hash
from flask_paginate import Pagination, get_page_args
import mysqlDB as msq
import unicodedata
from datetime import datetime, timedelta
# from googletrans import Translator
import time
import random
import re
import os
from flask_session import Session

app = Flask(__name__)

# Klucz tajny do szyfrowania sesji
app.config['SECRET_KEY'] = SESSION_FLASK_KEY

# Ustawienia dla Flask-Session
app.config['SESSION_TYPE'] = 'redis'  # Redis jako magazyn sesji
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=10)
app.config['SESSION_KEY_PREFIX'] = 'session:'  # Prefiks dla kluczy w Redis
app.config['SESSION_REDIS'] = redis.StrictRedis(host='localhost', port=6379, db=0)

# Ścieżka do katalogu z plikami
UPLOAD_FOLDER = 'dokumenty'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'doc', 'docx', 'odt'}  # Rozszerzenia dozwolone
UPLOAD_FOLDER_TREATMENTS = './static/img/services'
ALLOWED_EXTENSIONS_IMAGES = {'png', 'jpg', 'jpeg', 'gif'}

# Konfiguracja katalogu dla plików związanych z zabiegami
app.config['UPLOAD_FOLDER_TREATMENTS'] = UPLOAD_FOLDER_TREATMENTS

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def allowed_img_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS_IMAGES


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
def bez_polskich_znakow(text):
    """Zamienia polskie znaki na zwykłe litery."""
    return ''.join(
        c for c in unicodedata.normalize('NFD', text)
        if unicodedata.category(c) != 'Mn'
    )

def slugify(text):
    # Zamiana znaków diakrytycznych na ich odpowiedniki
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')
    # Usunięcie wszystkich znaków poza literami, cyframi i spacjami
    text = re.sub(r'[^\w\s-]', '', text)
    # Zamiana spacji i podwójnych myślników na pojedynczy myślnik
    text = re.sub(r'[-\s]+', '-', text).strip('-')
    return text.lower()

def generator_teamDB():
    # Pobranie danych z tabeli workers_team
    took_teamD = take_data_table('*', 'workers_team')

    # Pobranie danych użytkowników z generator_userDataDB()
    user_data = generator_userDataDB()  # Dostosowane do aktualnej struktury
    allowed_users = {user['login'] for user in user_data if user['uprawnienia']['user'] == 1}

    teamData = []
    for data in took_teamD:
        employee_login = data[2]  # Przyjmujemy, że login jest przechowywany w EMPLOYEE_NAME
        
        # Filtracja tylko użytkowników, którzy mają user = 1
        memeber_route = None
        if employee_login in allowed_users:
            user_name=data[3]
            user_role=data[4]
            if user_name and user_role:
                # Zamiana polskich znaków na zwykłe litery
                pre_name = bez_polskich_znakow(str(user_name).strip().replace(' ', '-').lower())
                pre_role = bez_polskich_znakow(str(user_role).strip().replace(' ', '-').lower())
                memeber_route = f'{pre_role}-{pre_name}'

            theme = {
                'ID': int(data[0]),
                'EMPLOYEE_PHOTO': data[1],
                'EMPLOYEE_LOGIN': data[2],
                'EMPLOYEE_NAME': data[3],
                'EMPLOYEE_ROLE': data[4],
                'EMPLOYEE_DEPARTMENT': data[5],
                'PHONE': '' if data[5] is None else data[6],
                'EMAIL': '' if data[6] is None else data[7],
                'FACEBOOK': '' if data[7] is None else data[8],
                'LINKEDIN': '' if data[8] is None else data[9],
                'STATUS': int(data[10]),  # Status (1 = aktywny, 0 = nieaktywny)
                'ROUTE': memeber_route if memeber_route is not None else ''
            }
            teamData.append(theme)

    return teamData
def validate_register_data(data, existing_users):
    """
    Waliduje dane przesłane podczas rejestracji, w tym unikalność loginu i emaila.
    
    Args:
        data (dict): Dane przesłane z formularza.
        existing_users (list): Lista istniejących użytkowników z bazy danych.

    Returns:
        list: Lista błędów (jeśli występują).
    """
    errors = []

    # Wymagane pola
    if not data.get('login'):
        errors.append("Pole 'login' jest wymagane.")
    if not data.get('fullName'):
        errors.append("Pole 'Imię i nazwisko' jest wymagane.")
    if not data.get('email'):
        errors.append("Pole 'email' jest wymagane.")
    if not data.get('password') or not data.get('confirmPassword'):
        errors.append("Hasło i potwierdzenie hasła są wymagane.")
    if data.get('password') != data.get('confirmPassword'):
        errors.append("Hasła muszą się zgadzać.")

    # Walidacja unikalności loginu i emaila
    login = data.get('login')
    email = data.get('email')

    if any(user['login'] == login for user in existing_users):
        errors.append(f"Użytkownik z loginem '{login}' już istnieje.")
    if any(user['email'] == email for user in existing_users):
        errors.append(f"Użytkownik z emailem '{email}' już istnieje.")

    # Walidacja dla roli pracownika
    if 'user' in data.getlist('roles[]', []):
        if not data.get('position'):
            errors.append("Pole 'Stanowisko' jest wymagane dla pracownika.")
        if not data.get('qualifications'):
            errors.append("Pole 'Kwalifikacje' jest wymagane dla pracownika.")
        if not data.get('experience'):
            errors.append("Pole 'Doświadczenie zawodowe' jest wymagane dla pracownika.")
        if not data.get('education'):
            errors.append("Pole 'Wykształcenie' jest wymagane dla pracownika.")
        if not data.get('description'):
            errors.append("Pole 'Opis pracownika' jest wymagane dla pracownika.")

    return errors



def process_photo(photo, save_path):
    try:
        # Otwórz obraz
        img = Image.open(photo)

        # Sprawdzenie orientacji obrazu (portretowa)
        width, height = img.size
        if width > height:
            raise ValueError("Zdjęcie nie jest w orientacji portretowej.")

        # Zmniejszenie do podstawy 350px, zachowując proporcje
        base_width = 350
        ratio = base_width / width
        new_height = int(height * ratio)
        img = img.resize((base_width, new_height))

        # Przycinanie do wymiarów 350x380px
        target_height = 380
        if new_height > target_height:
            # Obcięcie równo na środku
            top = (new_height - target_height) // 2
            bottom = top + target_height
            img = img.crop((0, top, base_width, bottom))
        elif new_height < target_height:
            # Dodaj tło, jeśli wysokość jest za mała
            background = Image.new("RGB", (base_width, target_height), (255, 255, 255))
            offset = (0, (target_height - new_height) // 2)
            background.paste(img, offset)
            img = background

        # Zapisz przetworzony obraz
        img.save(save_path)
    except Exception as e:
        # print(f"Error processing photo: {e}")
        raise ValueError(f"Nie udało się przetworzyć obrazu: {e}")
    

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
    if 'username' not in session:
        return redirect(url_for('index'))
    
    if not (session['userperm']['administrator'] == 1 or session['userperm']['super_user'] == 1):
        flash('Nie masz uprawnień do zarządzania tymi zasobami. Skontaktuj się z administratorem!', 'danger')
        return redirect(url_for('index'))
        
    session['page'] = 'rejestracja'
    pageTitle = 'Rejestracja użytkownika'
    if "username" in session:
        return render_template(
            'register.html',
            pageTitle=pageTitle
        )
    else:
        return redirect(url_for('index'))   

def preparoator_team(deaprtment_team='user', highlight=4):
    highlight += 1
    users_atributes = {}
    assigned_duodent = []

    # Mapowanie użytkowników
    for usr_d in generator_userDataDB():  # [Dostosowane do aktualnej struktury]
        u_name = usr_d['name']
        u_login = usr_d['login']  # Zmiana na 'login' zgodnie z nową strukturą
        users_atributes[u_login] = usr_d
        
        # Sprawdzenie uprawnień użytkownika do danego działu
        if usr_d['uprawnienia'].get(f'{deaprtment_team}', 0) == 1:
            assigned_duodent.append(u_login)


    
    # Struktura kolekcji
    collections = {
        f'{deaprtment_team}': {
            'home': [],
            'team': [],
            'available': []
        }
    }

    employee_photo_dict = {}

    i_duodent = 1
    # Iteracja przez pracowników z generator_teamDB
    generator_teamDB_v = generator_teamDB()
    for employees in generator_teamDB_v:  # [Dostosowane do aktualnej struktury]
        group = employees['EMPLOYEE_DEPARTMENT']
        department = str(group)
        employee = employees['EMPLOYEE_LOGIN']

        if employee not in users_atributes:
            continue  # Jeśli pracownik nie jest w słowniku użytkowników, pomijamy
        
        employee_login = users_atributes[employee]['login']  

        employee_photo = users_atributes[employee]['avatar']
        try:
            employee_photo_dict[employee_login]
        except KeyError:
            employee_photo_dict[employee_login] = employee_photo
        
        if i_duodent < highlight and department == f'{deaprtment_team}':
            collections[department]['home'].append(employee_login)
        elif i_duodent >= highlight and department == f'{deaprtment_team}':
            collections[department]['team'].append(employee_login)
        if department == f'{deaprtment_team}':
            i_duodent += 1

    # Dodawanie dostępnych użytkowników
    for assign in assigned_duodent:
        if assign not in collections[f'{deaprtment_team}']['home'] + collections[f'{deaprtment_team}']['team']:
            collections[f'{deaprtment_team}']['available'].append(assign)

            for row in generator_userDataDB():  
                if row['login'] == assign:
                    employee_photo = row['avatar']
                    try:
                        employee_photo_dict[assign]
                    except KeyError:
                        employee_photo_dict[assign] = employee_photo

    return {
        "collections": collections[f'{deaprtment_team}'],
        "employee_photo_dict": employee_photo_dict
    }

@app.route('/admin/team-stomatologia')
def team_stomatologia():
    """Strona zespołu stomatologia."""
    if 'username' not in session:
        return redirect(url_for('index'))
    
    if not (session['userperm']['administrator'] == 1 or session['userperm']['super_user'] == 1):
        flash('Nie masz uprawnień do zarządzania tymi zasobami. Skontaktuj się z administratorem!', 'danger')
        return redirect(url_for('index'))

    preparoator_team_dict = preparoator_team('user', 4)


    return render_template(
            "team_management_stomatologia.html", 
            members=preparoator_team_dict['collections'], 
            photos_dict=preparoator_team_dict['employee_photo_dict']
            )

@app.route('/admin/ustawieni_pracownicy', methods=['POST'])
def ustawieni_pracownicy():
    if 'username' not in session:
        return redirect(url_for('index'))
    
    if not (session['userperm']['administrator'] == 1 or session['userperm']['super_user'] == 1):
        flash('Nie masz uprawnień do zarządzania tymi zasobami. Skontaktuj się z administratorem!', 'danger')
        return redirect(url_for('index'))

    data = request.get_json()
    if not data or 'pracownicy' not in data:
        return jsonify({"error": "Nieprawidłowy format danych, oczekiwano klucza 'pracownicy'."}), 400
    
    sequence_data = data['pracownicy']
    department = str(data['grupa']).strip()
    
    sequence = []
    for s in sequence_data:
        clear_data = s.strip()
        sequence.append(clear_data)

    users_atributesByLogin = {}
    for usr_d in generator_userDataDB():  # [Dostosowane do nowego szablonu]
        u_login = usr_d['login']
        users_atributesByLogin[u_login] = usr_d

    ready_exportDB = []
    for u_login in sequence:
        set_row = {
            'EMPLOYEE_PHOTO': users_atributesByLogin[u_login]['avatar'],
            'EMPLOYEE_LOGIN': users_atributesByLogin[u_login]['login'],
            'EMPLOYEE_NAME': users_atributesByLogin[u_login]['name'],
            'EMPLOYEE_ROLE': users_atributesByLogin[u_login]['stanowisko'],
            'EMPLOYEE_DEPARTMENT': f'{department}',
            'PHONE': users_atributesByLogin[u_login]['contact']['phone'],
            'EMAIL': users_atributesByLogin[u_login]['email'],
            'FACEBOOK': users_atributesByLogin[u_login]['contact']['facebook'],
            'LINKEDIN': users_atributesByLogin[u_login]['contact']['linkedin'],
            'STATUS': 1
        }
        ready_exportDB.append(set_row)

    if len(ready_exportDB):
        msq.delete_row_from_database(
            """
                DELETE FROM workers_team WHERE EMPLOYEE_DEPARTMENT = %s;
            """,
            (f'{department}', )
        )

        for i, row in enumerate(ready_exportDB):
            zapytanie_sql = '''
                    INSERT INTO workers_team (EMPLOYEE_PHOTO, EMPLOYEE_LOGIN, EMPLOYEE_NAME, EMPLOYEE_ROLE, EMPLOYEE_DEPARTMENT, PHONE, EMAIL, FACEBOOK, LINKEDIN, STATUS)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
                '''
            dane = (
                    row['EMPLOYEE_PHOTO'], 
                    row['EMPLOYEE_LOGIN'], 
                    row['EMPLOYEE_NAME'], 
                    row['EMPLOYEE_ROLE'], 
                    row['EMPLOYEE_DEPARTMENT'], 
                    row['PHONE'], 
                    row['EMAIL'], 
                    row['FACEBOOK'], 
                    row['LINKEDIN'], 
                    row['STATUS'], 
                )
            if msq.insert_to_database(zapytanie_sql, dane):  # [Działająca funkcja]
                print(f'Ustawiono {row["EMPLOYEE_NAME"]} przez {session["username"]}!')
    else:
        return jsonify({"status": "Sukces", "pracownicy": sequence_data}), 200
    
    return jsonify({"status": "Sukces", "pracownicy": sequence_data}), 200

@app.context_processor
def inject_shared_variable():
    return {
        'userName': session.get("username", 'NotLogin'),
        'treatmentMenu': {item["ready_route"]: item["tytul_glowny"] for item in treatments_db()}
    }

@app.route('/admin/zarzadzanie-zabiegami')
def treatment_managment():
    session['page'] = 'for_patients'
    pageTitle = 'Zarządzanie Zabiegami'

    """Strona plików do pobrania."""
    if 'username' not in session:
        return redirect(url_for('index'))
    
    if not (session['userperm']['administrator'] == 1 or session['userperm']['super_user'] == 1):
        flash('Nie masz uprawnień do zarządzania tymi zasobami. Skontaktuj się z administratorem!', 'danger')
        return redirect(url_for('index'))
    
    return render_template(
        "treatment_management.html", 
        pageTitle=pageTitle,
        treatments_items=treatments_db()
    )

# Funkcja do aktualizacji danych w bazie
def update_element_in_db(element_id, data_type, value):

    # Dynamiczne zapytanie SQL w zależności od typu
    if data_type == 'text':
        if "_" in str(element_id):

            element_id_n = element_id.split("_")

            
        query = "UPDATE elements SET text_value = %s WHERE id = %s"
        # msq.insert_to_database()
    elif data_type == 'picker':
        query = "UPDATE elements SET int_value = ? WHERE id = ?"
    elif data_type == 'adder':
        query = "UPDATE elements SET int_value = ? WHERE id = ?"
    elif data_type == 'remover':
        query = "UPDATE elements SET int_value = ? WHERE id = ?"
    elif data_type == 'img':
        query = "UPDATE elements SET image_url = ? WHERE id = ?"
    elif data_type == 'url':
        query = "UPDATE elements SET url = ? WHERE id = ?"
    elif data_type == 'splx':
        query = "UPDATE elements SET splx_value = ? WHERE id = ?"
    else:
        print(f"Nieobsługiwany typ danych: {data_type}")
        return False

    print(element_id, data_type, value)
    return True


# Przykładowe dane do wysłania
OPTIONS_DATA = {
    "page_attached_worker_descriptions_list": [
        {"id": "1", "description": "Opcja 1 dla elementu 1"},
        {"id": "2", "description": "Opcja 2 dla elementu 1"},
        {"id": "3", "description": "Opcja 3 dla elementu 1"}
    ],
    "page_attached_files_list": [
        {"id": "10", "description": "Opcja A dla elementu 2"},
        {"id": "11", "description": "Opcja B dla elementu 2"},
        {"id": "12", "description": "Opcja C dla elementu 2"}
    ]
}

@app.route('/admin/get-picker-options', methods=['GET'])
def get_picker_options():
    # Pobierz ID elementu z parametrów zapytania
    element_id = request.args.get('id')

    # Sprawdź, czy istnieją dane dla danego ID
    if element_id in OPTIONS_DATA:
        return jsonify({"options": OPTIONS_DATA[element_id]})
    else:
        return jsonify({"error": "Opcje nie znalezione"}), 404

@app.route('/admin/edytuj-wybrany-element', methods=['POST'])
def edit_element():
    data = request.json
    element_id = data.get('id')
    data_type = data.get('type')
    value = data.get('value')

    if not element_id or not data_type:
        return jsonify({'error': 'Brak wymaganych danych'}), 400

    # Obsługa typów danych
    if data_type == 'text':
        # Walidacja i przypisanie ID z selektora
        if not isinstance(value, str):
            return jsonify({'error': 'Nieprawidłowy format dla text'}), 400

    if data_type == 'splx':
        # Zapis jako string z separatorami w bazie
        if isinstance(value, list):
            value = ','.join(value)
        else:
            return jsonify({'error': 'Nieprawidłowy format dla splx'}), 400

    if data_type == 'picker':
        try: value=int(value)
        except: return jsonify({'error': 'Nieprawidłowy format wymagana liczba int'}), 400
        # Walidacja i przypisanie ID z selektora
        if not isinstance(value, int):
            return jsonify({'error': 'Nieprawidłowy format dla int'}), 400
        
    if data_type == 'adder':
        try: value=int(value)
        except: return jsonify({'error': 'Nieprawidłowy format wymagana liczba int'}), 400
        # Walidacja i przypisanie ID z selektora
        if not isinstance(value, int):
            return jsonify({'error': 'Nieprawidłowy format dla int'}), 400
    
    if data_type == 'remover':
        # Walidacja i przypisanie ID z selektora
        if not isinstance(value, None) or not isinstance(element_id, str):
            return jsonify({'error': 'Nieprawidłowy format dla remover'}), 400
        
    if data_type == 'img':
        if 'file' in request.files:
            file = request.files['file']
            element_id = request.form.get('id')
            data_type = request.form.get('type')

            if not file or not element_id or data_type != 'img':
                return jsonify({'error': 'Nieprawidłowe dane'}), 400

            # Zapis pliku
            try:
                filename = f"{element_id}_{file.filename}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                # file.save(filepath)

                # Aktualizacja w bazie (jeśli potrzebna)
                # update_image_in_db(element_id, filename)

                # return jsonify({'message': 'Zdjęcie zapisane!', 'newImageUrl': f"/{filepath}"})
            except Exception as e:
                return jsonify({'error': str(e)}), 500

    # Aktualizacja w bazie (logika zależna od typu danych)
    success = update_element_in_db(element_id, data_type, value)
    if success:
        return jsonify({'message': 'Aktualizacja zakończona sukcesem!'})
    else:
        return jsonify({'error': 'Błąd podczas aktualizacji'}), 500

@app.route('/admin/add-treatment', methods=['POST'])
def add_treatment():
    """Dodawanie nowego zabiegu."""
    if 'username' not in session:
        return jsonify({'message': 'Musisz być zalogowany!'}), 401
    
    if not (session['userperm']['administrator'] == 1 or session['userperm']['super_user'] == 1):
        return jsonify({'message': 'Nie masz odpowiednich uprawnień!'}), 403

    try:
        # Pobieranie danych z formularza
        name = request.form.get('name').strip()
        route = request.form.get('route').strip().lower()
        icon = request.form.get('icon')  # Pobieranie wartości ikony
        descrition = request.form.get('descrition')  # Pobranie opisu
        file = request.files.get('file')  # Pobranie pliku

        # Generowanie SEO-friendly wersji name i route
        name_seoroute = slugify(name.lower())
        route_seoroute = slugify(route)

        # Łączenie w jeden ciąg dla finalnego routa
        ready_route = f"{name_seoroute}-{route_seoroute}".strip('-')  # Usuwa myślniki z początku i końca

        # Alternatywne podejście, aby zabezpieczyć przed przypadkami pustego `route_seoroute`
        if not route_seoroute:  # Jeśli route_seoroute jest pusty
            ready_route = name_seoroute  # Ustaw tylko name_seoroute jako ready_route
        else:
            ready_route = f"{name_seoroute}-{route_seoroute}".strip('-')  # Łączy, usuwając końcowe myślniki

        # Walidacja danych
        if not name or not route or not icon or not descrition or not file:
            return jsonify({'message': 'Wszystkie pola są wymagane!'}), 400

        if file and allowed_img_file(file.filename):
            # Generowanie nowej nazwy pliku
            original_name = file.filename
            base_name, extension = original_name.lower().rsplit('.', 1)
            year = time.strftime("%Y")  # Rok
            unix_suffix = str(int(time.time()))[-6:]  # Ostatnie 6 cyfr czasu Unix
            new_file_name = f"{base_name}-{year}-{unix_suffix}.{extension}"  # Nowa nazwa pliku
            
            # Zapis pliku w folderze static/img/_TREATMENTS
            filepath = os.path.join(app.config['UPLOAD_FOLDER_TREATMENTS'], new_file_name)
            file.save(filepath)
        else:
            return jsonify({'message': 'Nieprawidłowy format pliku!'}), 400

        # Zapis do bazy danych
        query = """
            INSERT INTO tabela_uslug (tytul_glowny, ready_route, foto_home, icon, opis_home, pozycja_kolejnosci, treatment_general_status) 
            VALUES (%s, %s, %s, %s, %s, 0, 1);
        """
        # Wstawianie danych do bazy
        success = msq.insert_to_database(query, (name, ready_route, new_file_name, icon, descrition))

        if success:
            return jsonify({
                'message': 'Zabieg został pomyślnie dodany!',
                'uploaded_file': new_file_name,
                'icon': icon  # Wartość wybranej ikony
            }), 200
        else:
            return jsonify({'message': 'Wystąpił błąd zapisu do bazy danych!'}), 500

    except Exception as e:
        return jsonify({'message': f'Wystąpił błąd: {str(e)}'}), 500


@app.route('/admin/aktualizuj_kolejnosc_zabiegow', methods=['POST'])
def update_category_treatment():
    """Aktualizacja kolejności zabiegow."""
    data = request.get_json()
    new_order = data.get('order')  # Lista z ID kategorii w nowej kolejności
    # print(data, new_order)
    if not new_order or not isinstance(new_order, list):
        return jsonify({"status": "error", "message": "Nieprawidłowe dane"}), 400

    # Aktualizacja kolejności w bazie
    for index, category_id in enumerate(new_order):
        query = "UPDATE tabela_uslug SET pozycja_kolejnosci = %s WHERE id = %s;"
        params = (index + 1, category_id)
        msq.insert_to_database(query, params)

    return jsonify({"status": "success", "message": "Kolejność zaktualizowana"})

def get_categories():
    query = "SELECT id, name, position FROM file_categories ORDER BY position ASC;"
    params = ()
    got_data = msq.safe_connect_to_database(query, params)
    ready_list = [{'id': rekord[0] ,'name':rekord[1], 'position': rekord[2]} for rekord in got_data ]
    return ready_list

def get_fileBy_categories(category_id, route_name="dokumenty/", status_aktywnosci=False):
    if status_aktywnosci:
        query = f"SELECT id, name, file_name FROM files WHERE category_id=%s AND status_aktywnosci=%s;"
        params = (category_id, 1)
    else:
        query = f"SELECT id, name, file_name FROM files WHERE category_id=%s;"
        params = (category_id, )

    got_data = msq.safe_connect_to_database(query, params)

    # Poprawne łączenie ścieżek
    ready_list = [{
        "id": rekord[0],  # Dodanie ID pliku
        "name": rekord[1],
        "file_name": os.path.join(route_name, rekord[2])  # Używamy os.path.join dla poprawnego separatora
    } for rekord in got_data]
    return ready_list

@app.route('/admin/dokumenty')
def dokumenty():
    """Strona plików do pobrania."""
    if 'username' not in session:
        return redirect(url_for('index'))
    
    if not (session['userperm']['administrator'] == 1 or session['userperm']['super_user'] == 1):
        flash('Nie masz uprawnień do zarządzania tymi zasobami. Skontaktuj się z administratorem!', 'danger')
        return redirect(url_for('index'))
    
    categs = get_categories()
    categorized_files = []
    categories_names = []
    if categs:  # Jeśli istnieją kategorie
        for category in categs:
            category_id = category['id']
            file_list = get_fileBy_categories(category_id, status_aktywnosci=True)
            
            # Dodajemy słownik z kategorią i listą plików
            categorized_files.append({
                'category': category['name'],
                'file_list': file_list,
            })
            categories_names.append(category['name'])

    return render_template(
        "files_management.html", 
        categorized_files=categorized_files,  # Lista kategorii z plikami
        categories=categs  # Pełna lista kategorii z ID i name
    )

@app.route('/admin/aktualizuj_kolejnosc', methods=['POST'])
def update_category_order():
    """Aktualizacja kolejności kategorii."""
    data = request.get_json()
    new_order = data.get('order')  # Lista z ID kategorii w nowej kolejności
    # print(data, new_order)
    if not new_order or not isinstance(new_order, list):
        return jsonify({"status": "error", "message": "Nieprawidłowe dane"}), 400

    # Aktualizacja kolejności w bazie
    for index, category_id in enumerate(new_order):
        query = "UPDATE file_categories SET position = %s WHERE id = %s;"
        params = (index + 1, category_id)
        msq.insert_to_database(query, params)

    return jsonify({"status": "success", "message": "Kolejność zaktualizowana"})



@app.route('/admin/dodaj_kategorie', methods=['POST'])
def add_category():
    """Dodawanie nowej kategorii."""
    try:
        data = request.get_json()
        category_name = data.get('name')
        position = data.get('position', 0)  # Domyślna pozycja to 0

        if not category_name:
            return jsonify({"status": "error", "message": "Nazwa kategorii jest wymagana"}), 400

        query = "INSERT INTO file_categories (name, position) VALUES (%s, %s);"
        params = (category_name, position)
        msq.insert_to_database(query, params)

        return jsonify({"status": "success", "message": "Kategoria dodana pomyślnie"})
    except Exception as e:
        print(e)  # Logowanie błędu w konsoli serwera
        return jsonify({"status": "error", "message": "Błąd serwera"}), 500

@app.route('/admin/dodaj_plik', methods=['POST'])
def upload_file():
    """Dodawanie pliku do kategorii."""
    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "Brak pliku w zapytaniu"}), 400

    file = request.files['file']
    category_id = request.form.get('category_id')
    original_name = request.form.get('name')

    if not category_id or not original_name:
        return jsonify({"status": "error", "message": "Kategoria i nazwa pliku są wymagane"}), 400

    if file and allowed_file(file.filename):
        # Tworzenie unikatowej nazwy pliku
        base_name = secure_filename(original_name.replace(" ", "-").lower())  # Czytelny format nazwy
        year = time.strftime("%Y")  # Rok
        unix_suffix = str(int(time.time()))[-6:]  # Ostatnie 6 cyfr czasu Unix
        extension = file.filename.rsplit('.', 1)[-1].lower()  # Pobranie rozszerzenia pliku
        new_file_name = f"{base_name}-{year}-{unix_suffix}.{extension}"

        # Ścieżka do zapisu pliku
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], new_file_name)
        file.save(save_path)

        # Zapis do bazy danych
        query = """
            INSERT INTO files (name, file_name, category_id, status_aktywnosci) 
            VALUES (%s, %s, %s, %s);
        """
        params = (original_name, new_file_name, category_id, 1)
        msq.insert_to_database(query, params)

        return jsonify({"status": "success", "message": "Plik dodany pomyślnie", "file_name": new_file_name})
    else:
        return jsonify({"status": "error", "message": "Nieprawidłowy typ pliku"}), 400

@app.route('/admin/usun_plik', methods=['POST'])
def delete_file():
    """Usuwanie pliku."""
    data = request.get_json()
    file_name = data.get('file_name')

    if not file_name:
        return jsonify({"status": "error", "message": "Nazwa pliku jest wymagana"}), 400

    # Ścieżka do pliku
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], os.path.basename(file_name))  # Bezpieczne dołączanie nazwy pliku
    if os.path.exists(file_path):
        os.remove(file_path)
    else:
        return jsonify({"status": "error", "message": "Plik nie istnieje na serwerze"}), 404

    # Usunięcie rekordu z bazy danych
    query = "DELETE FROM files WHERE file_name = %s;"
    params = (os.path.basename(file_name),)  # Użycie tylko nazwy pliku (bez ścieżki)
    msq.delete_row_from_database(query, params)

    return jsonify({"status": "success", "message": "Plik został usunięty pomyślnie"})

@app.route('/admin/edytuj_nazwe_pliku', methods=['POST'])
def edit_file_name():
    """Edycja nazwy wyświetlanej pliku."""
    data = request.get_json()
    print("Otrzymane dane:", data)  # Logowanie danych

    file_id = data.get('file_id')
    new_name = data.get('new_name')

    if not file_id or not new_name:
        return jsonify({"status": "error", "message": "ID pliku i nowa nazwa są wymagane"}), 400

    # Aktualizacja nazwy w bazie danych
    query = "UPDATE files SET name = %s WHERE id = %s;"
    params = (new_name, file_id)
    msq.insert_to_database(query, params)

    return jsonify({"status": "success", "message": "Nazwa pliku została zaktualizowana pomyślnie"})

@app.route('/admin/edytuj_kategorie', methods=['POST'])
def edit_category():
    """Edycja nazwy kategorii."""
    data = request.get_json()
    category_id = data.get('category_id')
    new_name = data.get('new_name')

    if not category_id or not new_name:
        return jsonify({"status": "error", "message": "ID kategorii i nowa nazwa są wymagane"}), 400

    # Aktualizacja nazwy kategorii w bazie danych
    query = "UPDATE file_categories SET name = %s WHERE id = %s;"
    params = (new_name, category_id)
    msq.insert_to_database(query, params)

    return jsonify({"status": "success", "message": "Nazwa kategorii została zaktualizowana pomyślnie"})


@app.route('/admin/usun_kategorie', methods=['POST'])
def delete_category():
    """Usuwanie kategorii wraz z plikami."""
    data = request.get_json()
    category_id = data.get('category_id')

    if not category_id:
        return jsonify({"status": "error", "message": "ID kategorii jest wymagane"}), 400

    # Pobranie listy plików dla danej kategorii z pełną ścieżką systemową
    files = get_fileBy_categories(category_id)

    # Usunięcie plików fizycznie z serwera
    for file in files:
        file_path = file["file_name"]  # Ścieżka systemowa została już zbudowana w get_fileBy_categories
        if os.path.exists(file_path):
            os.remove(file_path)
        else:
            print(f"Plik {file_path} nie istnieje. Pomijam usunięcie.")

    # Usunięcie plików z bazy danych
    query_delete_files = "DELETE FROM files WHERE category_id = %s;"
    params_files = (category_id,)
    msq.delete_row_from_database(query_delete_files, params_files)

    # Usunięcie kategorii z bazy danych
    query_delete_category = "DELETE FROM file_categories WHERE id = %s;"
    params_category = (category_id,)
    msq.delete_row_from_database(query_delete_category, params_category)

    return jsonify({"status": "success", "message": "Kategoria i powiązane pliki zostały usunięte pomyślnie"})

# Dla Pacjenta
@app.route('/informacje-dla-pacjentow-stomatologicznych')
def for_patients():
    session['page'] = 'for_patients'
    pageTitle = 'Dla Pacjenta'

    categs = get_categories()
    categorized_files = []
    if categs:  # Jeśli istnieją kategorie
        for category in categs:
            category_id = category['id']
            file_list = get_fileBy_categories(category_id, status_aktywnosci=True)
            
            # Dodajemy słownik z kategorią i listą plików
            categorized_files.append({
                'category': category['name'],
                'file_list': file_list,
            })

    return render_template(
        'for_patients.html',
        categorized_files=categorized_files,  # Lista kategorii z plikami
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

# Strona główna
@app.route('/')
def index():
    session['page'] = 'index'
    pageTitle = 'Strona Główna'

    generator_teamDB_v = generator_teamDB()
    if len(generator_teamDB_v) > 3:
        generator_teamDB_v = generator_teamDB_v[:4]

    return render_template(
        'index.html',
        pageTitle=pageTitle,
        members=generator_teamDB_v
    )

@app.route('/api/register', methods=['POST'])
def register():
    # Pobranie danych z ImmutableMultiDict
    login = request.form.get('login')
    full_name = request.form.get('fullName')
    position = request.form.get('position')
    qualifications = request.form.get('qualifications')
    experience = request.form.get('experience')
    education = request.form.get('education')
    description = request.form.get('description')
    email = request.form.get('email')
    phone = request.form.get('phone')
    facebook = request.form.get('facebook')
    instagram = request.form.get('instagram')
    twitter = request.form.get('twitter')
    linkedin = request.form.get('linkedin')
    plain_password = request.form.get('password')

    # Role użytkownika
    roles = request.form.getlist('roles[]')  # Pobieranie listy ról
    is_admin = 1 if 'administrator' in roles else 0
    is_super_user = 1 if 'super_user' in roles else 0
    is_user = 1 if 'user' in roles else 0

    print(request.form)

    # Walidacja danych
    errors = validate_register_data(data=request.form, existing_users=generator_userDataDB())
    if errors:
        return jsonify({"errors": errors}), 400
    
    
    # Obsługa zdjęcia
    photo = request.files.get('photo')
    if photo and imghdr.what(photo) not in ['jpeg', 'png', 'gif']:
        return jsonify({"errors": ["Przesłany plik nie jest poprawnym obrazem."]}), 400
    
    photo_link = None
    if photo:
        # Generowanie unikalnego prefixu (5 ostatnich cyfr czasu UNIX)
        unix_prefix = str(int(time.time()))[-5:]

        # Pobierz nazwę pliku
        original_filename = secure_filename(photo.filename)
        extension = os.path.splitext(original_filename)[1]  # Pobierz rozszerzenie (.jpg, .png itp.)
        base_filename = os.path.splitext(original_filename)[0]  # Pobierz nazwę bez rozszerzenia

        # Połącz prefix z oryginalną nazwą
        unique_filename = f"{unix_prefix}_{base_filename}{extension}"

        # Ścieżka docelowa
        save_path = os.path.join("static", "img", "doctor", unique_filename)

        # Zapisz zdjęcie
        try:
            process_photo(photo, save_path)
        except Exception as e:
            return jsonify({"errors": ["Nie udało się zapisać przesłanego pliku."]}), 500

        domena_strony_www = 'https://www.duodentbielany.pl/'
        katalog_zdjecia = 'static/img/doctor/'
        photo_link = f'{domena_strony_www}{katalog_zdjecia}{unique_filename}'
    
    if phone:
        # Usuwamy wszystkie spacje i niepotrzebne znaki (opcjonalnie, np. "-", "(" lub ")")
        phone = ''.join(filter(str.isdigit, phone))  # Zostawiamy tylko cyfry

        # Dodajemy prefiks +48, jeśli go brakuje
        if not phone.startswith('48'):
            phone = f'48{phone}'
        phone = f'+{phone}'  # Dodajemy "+" przed numerem

    # Generowanie soli i haszowanie hasła
    salt = hash.generate_salt()
    hashed_password = hash.hash_password(plain_password, salt)

    # Ustawienie linku do avatara
    avatar = photo_link if photo_link else 'https://www.duodentbielany.pl/static/img/doctor/with-out-face-avatar.jpg'

    # Status użytkownika - domyślnie aktywny
    user_status = 1

    # Przygotowanie zapytania SQL
    zapytanie_sql = """
        INSERT INTO admins (
            login, name, stanowisko, kwalifikacje, doswiadczenie, wyksztalcenie, opis,
            email, password, salt, avatar, administrator, super_user, user,
            phone, facebook, instagram, twitter, linkedin, status_usera
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    # Dane do zapytania
    dane = (
        login.strip(), full_name.strip(), position.strip(), qualifications.strip(), experience.strip(), education.strip(), description.strip(),
        email.strip(), hashed_password, salt, avatar.strip(), is_admin, is_super_user, is_user,
        phone, facebook, instagram, twitter, linkedin, user_status
    )

    # Wstawianie danych do bazy
    if msq.insert_to_database(zapytanie_sql, dane):
        response = {"status": "success", "message": "Administrator został zapisany do bazy."}
        return jsonify(response), 200
    else:
        response ={"status": "error", "message": "Wystąpił błąd podczas zapisywania danych."}
        return jsonify(response), 400


# Poznaj nas bliżej
@app.route('/o-nas-twoja-przychodnia-stomatologiczna')
def about_us():
    session['page'] = 'about_us'
    pageTitle = 'Poznaj nas bliżej'

    generator_teamDB_v = generator_teamDB()
    if len(generator_teamDB_v) > 3:
        generator_teamDB_v = generator_teamDB_v[:4]

    return render_template(
        'about_us.html',
        pageTitle=pageTitle,
        members=generator_teamDB_v
    )

def treatments_db():
    zapytanie_sql = """
        SELECT 
            id,
            foto_home,
            icon,
            tytul_glowny,
            ready_route,
            opis_home,
            pozycja_kolejnosci
        FROM tabela_uslug
        ORDER BY pozycja_kolejnosci ASC
    """
    db_dump = msq.connect_to_database(zapytanie_sql)
    export = []

    for data in db_dump:
        theme = {
            "id": data[0],
            "foto_home": data[1],
            "icon": data[2],
            "tytul_glowny": data[3],
            "ready_route": data[4],
            "opis_home": data[5],
        }
        export.append(theme)

    return export

# Zabiegi - lista
@app.route('/zabiegi-stomatologiczne-kompleksowa-oferta')
def treatments():
    session['page'] = 'treatments'
    pageTitle = 'Zabiegi'

    treatments_items = treatments_db()

    return render_template(
        'treatments.html',
        pageTitle=pageTitle,
        treatments_items=treatments_items
    )

# Generate treatments_dict
treatments_dict = {item["ready_route"]: item["tytul_glowny"] for item in treatments_db()}

@app.route('/zabieg-stomatologiczny/<path:treatment_slug>')
def treatment_dynamic(treatment_slug):
    if treatment_slug in treatments_dict:
        pageTitle = treatments_dict[treatment_slug]
        session['page'] = treatment_slug
        page_data_interput = {'page_points_splx_section': ['Podpunkt 1', 'Podpunkt 2', 'Podpunkt 3']}
        return render_template(
            'treatment_details.html',
            pageTitle=pageTitle,
            nazwa_uslugi=treatments_dict[treatment_slug],
            page_data_interput=page_data_interput
        )
    else:
        abort(404)



# Zespół
@app.route('/poznaj-nasz-zespol-specjalistow-stomatologii')
def team():
    session['page'] = 'team'
    pageTitle = 'Zespół'

    generator_teamDB_v = generator_teamDB()

    return render_template(
        'team.html',
        pageTitle=pageTitle,
        members=generator_teamDB_v
    )

# Szczegóły członka zespołu
def team_memeber_router():
    generator_teamDB_v = generator_teamDB()
    generator_userDataDB_v = generator_userDataDB()
    theme_id = {}
    theme_name = {}
    theme_login = {}
    for memeber in generator_teamDB_v:
        user_name=memeber.get('EMPLOYEE_NAME', None)
        user_role=memeber.get('EMPLOYEE_ROLE', None)
        user_login=memeber.get('EMPLOYEE_LOGIN', None)
        if user_name and user_role and user_login:
            # Zamiana polskich znaków na zwykłe litery
            pre_name = bez_polskich_znakow(str(user_name).strip().replace(' ', '-').lower())
            pre_role = bez_polskich_znakow(str(user_role).strip().replace(' ', '-').lower())

            create_route = f'{pre_role}-{pre_name}'
            for admin in generator_userDataDB_v:
                if admin.get('login') == user_login:
                    theme_id[create_route] = admin.get('id')
                    theme_name[create_route] = admin.get('name')
                    theme_login[create_route] = admin.get('login')
                    break

    return {
            "by_id": theme_id,
            "by_name": theme_name,
            "by_login": theme_login
        }
@app.route('/zespol/<string:name_pracownika>')
def team_mambers(name_pracownika):
    DYNAMIC_team_memeber_dict = team_memeber_router()
    DYNAMIC_team_memeber_dict_id = DYNAMIC_team_memeber_dict.get('by_id', {})
    if name_pracownika in DYNAMIC_team_memeber_dict_id:
        idPracownika = DYNAMIC_team_memeber_dict_id[name_pracownika]
        member_data_prepared = [member_data for member_data in generator_userDataDB() if member_data['id'] == idPracownika]
        if member_data_prepared:
            member_data_prepared = member_data_prepared[0]
            del member_data_prepared['password']
            del member_data_prepared['salt']
            del member_data_prepared['contact']
            del member_data_prepared['uprawnienia']
            del member_data_prepared['email']
            del member_data_prepared['login']
            del member_data_prepared['id']
        else:
            member_data_prepared = {}
        ready_name = member_data_prepared['name']
        pageTitle = ready_name
        session['page'] = ready_name
        return render_template(
            'team_member.html',
            pageTitle=pageTitle,
            dane_pracownika=member_data_prepared
        )
    else:
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
@app.route('/kontakt-z-przychodnia-stomatologiczna', methods=['GET'])
def contact_page():
    session['page'] = 'kontakt'
    pageTitle = 'Kontakt z przychodnią stomatologiczną'
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