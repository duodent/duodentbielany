from flask import Flask, render_template, redirect, url_for, jsonify, session, request, send_from_directory, Response, abort, flash, current_app
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
import string
import re
import os
from flask_session import Session
import hashlib
import uuid
from sendEmailBySmtp import send_html_email
from end_1 import decode_integer, encode_string
import logging




# ========================================================================================= #
#  USTAWIENIA APLIKACJI
#  
#  Sekcja zawiera konfigurację aplikacji, w tym:
#  - Podstawowe ustawienia frameworka.
#  - Klucze API, konfigurację baz danych i inne zmienne środowiskowe.
#  - Ścieżki do katalogów statycznych i szablonów.
#  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -  
#  Zmienne i obiekty wykorzystywane w inicjalizacji aplikacji.
# ========================================================================================= #
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
UPLOAD_FOLDER_TREATMENTS = './static/img/services'
UPLOAD_FOLDER_BANNERS = './static/img/banners/'
UPLOAD_FOLDER_AVATARS = './static/img/doctor/'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'doc', 'docx', 'odt'}  # Rozszerzenia dozwolone
ALLOWED_EXTENSIONS_IMAGES = {'png', 'jpg', 'jpeg', 'gif'}

# Konfiguracja katalogu dla plików związanych z dokumnetami
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Konfiguracja katalogu dla plików związanych z zabiegami
app.config['UPLOAD_FOLDER_TREATMENTS'] = UPLOAD_FOLDER_TREATMENTS

# Konfiguracja katalogu dla plików związanych z banerami
app.config['UPLOAD_FOLDER_BANNERS'] = UPLOAD_FOLDER_BANNERS

# Konfiguracja katalogu dla plików związanych z banerami
app.config['UPLOAD_FOLDER_AVATARS'] = UPLOAD_FOLDER_AVATARS

# Ustawienie ilości elementów na stronę (nie dotyczy sesji)
app.config['PER_PAGE'] = 6

# Inicjalizacja obsługi sesji
Session(app)

















# ========================================================================================= #
#  ZMIENNE GLOBALNE
#  
#  Zmienna do poprawnego działania aplikacji:
#  - Zmienna przechowująca ścieżki dostępu.
#  - Globalne flagi i ustawienia aplikacji.
#  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -  
#  Ważne dla stabilności działania w trybie produkcyjnym i debugowania.
# ========================================================================================= #

# Główne separatatory dzielenia stringów na listy
spea_main = "#splx#"
spea_second = "#|||#"
ENDoneslot = "5875"

# Główne ikony aplikacji
iconer_changer_by_neme = {
    'flaticon-chair': 1,
    'flaticon-dental-implant': 2,
    'flaticon-dental-care': 3,
    'flaticon-tooth-1': 4,
    'flaticon-tooth-2': 5,
    'flaticon-tooth' : 6,
}

iconer_changer_by_id = {
    key: val for val, key in iconer_changer_by_neme.items()
}



















# ========================================================================================= #
#  FUNKCJE POMOCNICZE
#  
#  Zbiór funkcji wspierających działanie aplikacji, takich jak:
#  - Formatowanie danych wejściowych i wyjściowych.
#  - Walidacja parametrów.
#  - Operacje na plikach i ciągach znaków.
#  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -  
#  Ułatwiają ponowne wykorzystanie kodu w różnych częściach aplikacji.
# ========================================================================================= #

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def allowed_img_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS_IMAGES

def check_separator_take_list(sepa: str, string: str, shout_parts: int):
    """
    Funkcja dzieli string na listę na podstawie separatora.
    Jeśli liczba elementów jest mniejsza niż oczekiwana, uzupełnia brakujące puste elementy.
    Jeśli jest większa, przycina listę do wymaganej długości.
    """
    # print([sepa, string, shout_parts])
    if not isinstance(sepa, str) and not isinstance(string, str) and not isinstance(shout_parts, int):
        return []
    parts = string.split(sepa)
    if len(parts) == shout_parts:
        return parts
    elif len(parts) < shout_parts:
        return parts + [""] * (shout_parts - len(parts))
    else:  # len(parts) > shout_parts
        return parts[:shout_parts]

def generate_hash():
    """Generuje unikalny hash dla linku wizyty."""
    unique_id = str(uuid.uuid4())
    return hashlib.sha256(unique_id.encode()).hexdigest()

def is_valid_email(email):
    """Sprawdza, czy email jest w poprawnym formacie."""
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(email_regex, email) is not None

# Generate treatments_dict
def validatorZip(list1, list2):
    """
    Dopasowuje elementy dwóch list do par na podstawie długości krótszej listy.
    Pozostałe elementy są pomijane.
    """
    min_length = min(len(list1), len(list2))
    return list1[:min_length], list2[:min_length]

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

def getuserrole(useroneitem_data_from_generator_userDataDB):
    # ======================== dane (admins) ============================
    # Funkcja pomocnicza określająca najwyższy poziom uprawnień użytkownika.
    # Pobiera dane użytkownika z bazy danych (admins) i zwraca jeden z poziomów:
    # 'administrator', 'super_user', 'user', lub 'guest' (domyślnie).
    # Aby funkcja działała poprawnie, należy jako argument podać element z listy 
    # zwróconej przez generator_userDataDB(). Każdy element powinien być 
    # usystematyzowany zgodnie ze standardem aplikacji – zawierać odpowiednie 
    # klucze ('administrator', 'super_user', 'user') z wartościami typu int (0 lub 1).
    # ===================================================================

    if useroneitem_data_from_generator_userDataDB.get('uprawnienia',{}).get('administrator', 0):
        return 'administrator'
    elif useroneitem_data_from_generator_userDataDB.get('uprawnienia',{}).get('super_user', 0):
        return 'super_user'
    elif useroneitem_data_from_generator_userDataDB.get('uprawnienia',{}).get('user', 0):
        return 'user'
    else:
        return 'guest'
    
def getUserRoles(useroneitem_data_from_generator_userDataDB):
    # ======================== dane (admins) ============================
    # Funkcja pomocnicza określająca najwyższy poziom uprawnień użytkownika.
    # Pobiera dane użytkownika z bazy danych (admins) i zwraca jeden z poziomów:
    # 'administrator', 'super_user', 'user', lub 'guest' (domyślnie).
    # Aby funkcja działała poprawnie, należy jako argument podać element z listy 
    # zwróconej przez generator_userDataDB(). Każdy element powinien być 
    # usystematyzowany zgodnie ze standardem aplikacji – zawierać odpowiednie 
    # klucze ('administrator', 'super_user', 'user') z wartościami typu int (0 lub 1).
    # ===================================================================
    return {
        'administrator': useroneitem_data_from_generator_userDataDB.get('uprawnienia',{}).get('administrator', 0),
        'super_user': useroneitem_data_from_generator_userDataDB.get('uprawnienia',{}).get('super_user', 0),
        'user': useroneitem_data_from_generator_userDataDB.get('uprawnienia',{}).get('user', 0)
    }

def get_videos():
    # Pobieramy wszystkie filmy
    query_videos = "SELECT id, video_url, active FROM videos ORDER BY id ASC"
    videos = msq.connect_to_database(query_videos)

    # Pobieramy przypisane kolory do filmów
    query_colors = "SELECT video_id, color FROM video_eye_colors"
    video_colors = msq.connect_to_database(query_colors)

    # Tworzymy słownik przypisanych kolorów {video_id: [lista kolorów]}
    color_map = {}
    for color in video_colors:
        video_id, color_name = color
        if video_id not in color_map:
            color_map[video_id] = []
        color_map[video_id].append(color_name)

    # Konstruujemy finalną listę filmów z ich przypisanymi kolorami
    result = []
    for video in videos:
        video_id, video_url, active = video
        result.append({
            "id": video_id,
            "video_url": video_url,
            "colors": color_map.get(video_id, []),  # Jeśli film nie ma przypisanych kolorów, zwracamy pustą listę
            "active": active
        })

    return result

def extract_youtube_id(video_url):
    """
    Pobiera ID filmu YouTube z różnych formatów linków.
    Obsługuje:
    - https://www.youtube.com/watch?v=VIDEO_ID
    - https://youtu.be/VIDEO_ID
    - https://www.youtube.com/embed/VIDEO_ID
    - https://www.youtube.com/shorts/VIDEO_ID
    - iframe: <iframe src="https://www.youtube.com/embed/VIDEO_ID" ...></iframe>
    """
    regex_patterns = [
        r"(?:v=|youtu\.be\/|embed\/|shorts\/)([A-Za-z0-9_-]{11})",
        r'src="https:\/\/www\.youtube\.com\/embed\/([A-Za-z0-9_-]{11})"'  # Dla iframe
    ]

    for pattern in regex_patterns:
        match = re.search(pattern, video_url)
        if match:
            return match.group(1)

    return None  # Jeśli ID nie zostało znalezione

def extract_src_from_iframe(iframe_code):
    match = re.search(r'src="([^"]+)"', iframe_code)
    return match.group(1) if match else None









# ========================================================================================= #
#  FUNKCJE BAZODANOWE
#  
#  Funkcje odpowiedzialne za komunikację z bazą danych:
#  - Pobieranie danych.
#  - Aktualizacja i usuwanie rekordów.
#  - Obsługa transakcji.
#  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -  
#  Zapewniają integralność danych i optymalizację zapytań.
# ========================================================================================= #

#  Funkcja pobiera dane z bazy danych 
def take_data_where_ID(key, table, id_name, ID):
    if isinstance(ID, str):
        ID = f"'{ID}'"
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

def treatments_db(acvtity=False):

    where_query_acvtity = 'WHERE treatment_general_status = 1' if acvtity else ''

    zapytanie_sql = f"""
        SELECT 
            id,
            foto_home,
            icon,
            tytul_glowny,
            ready_route,
            opis_home,
            pozycja_kolejnosci
        FROM tabela_uslug
        {where_query_acvtity}
        ORDER BY pozycja_kolejnosci ASC;
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

def treatments_foto_db_by_id(id_treatment = None):
    zapytanie_sql = """
        SELECT 
            id,
            foto_home,
            foto_page_header,
            page_photo_content_links_splx_section_2,
            optional_1
        FROM tabela_uslug
        ORDER BY pozycja_kolejnosci ASC
    """
    db_dump = msq.connect_to_database(zapytanie_sql)
    export = []

    for data in db_dump:
            
        theme = {
            "id": data[0],
            "foto_home": data[1],
            "foto_page_header": data[2],
            "page_photo_content_links_splx_section_2": data[3],
            "page_photo_content_links_list_section_2": check_separator_take_list(spea_main, '' if data[3] is None else data[3], len(str(data[3]).split(spea_main))),
            "optional_1": data[4]
        }
        if isinstance(id_treatment, int) and data[0] == id_treatment:
            return theme
        export.append(theme)

    return export

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

####################################################
# Funkcja do aktualizacji danych w bazie
####################################################
def update_element_in_db(element_id, data_type, value):
    print("\n\n\n\n", element_id, data_type, value, "\n\n\n\n")
    # Dynamiczne zapytanie SQL w zależności od typu

    # {strona=tabela}-{sekcja=kolumna}-{id=numer}-{część=pozycja}-{wszystkich=ilość pozycji}
    # przykład: treatment-baner_h1_splx-1-1-3
        # tablea = treatment
        # kolumna = baner_h1_splx
        # numer = 1
        # pozycja 1 z 3
    
    element_id_split_part = editing_id_updater_reader(element_id)
    if 'status' in element_id_split_part:
        if not element_id_split_part['status']:
            return False
    else:
        return False
    

    if all(key in element_id_split_part for key in ['strona', 'sekcja', 'id_number', 'index', 'part', 'ofparts']):
        strona=element_id_split_part['strona']
        sekcja=element_id_split_part['sekcja']
        id_number=element_id_split_part['id_number']
        index=element_id_split_part['index']
        part=element_id_split_part['part']
        ofparts=element_id_split_part['ofparts']
    else:
        return False

    ready_string_splx = None
    table_db = None
    column_db = None
    id_db = None
    query = None
    params = None

    if data_type == 'text':
        ####################################################
        # Aktualizacja tekstu w tabela_uslug
        ####################################################
        if strona == 'treatment':
            ready_string_splx = None
            table_db = 'tabela_uslug'
            column_db = sekcja
            id_db = id_number

            # BANERS
            BANERS = ['baner_h1_splx', 'baner_h2_splx']
            if sekcja in BANERS:
                exactly_what = None
                for c in BANERS: 
                    if c == sekcja: exactly_what = c
                if exactly_what is None:
                    print("Problem Klucza")
                    return False
                
                splet_key = exactly_what.replace('splx', 'splet')
                
                cunet_list_db = None
                for data_b in treatments_db_all_by_route_dict().values():
                    if 'id' in data_b and splet_key in data_b:
                        if data_b['id'] == id_db:
                            cunet_list_db = data_b[splet_key]
                            break
                if isinstance(cunet_list_db, list):
                    if len(cunet_list_db) == ofparts:
                        cunet_list_db[index] = value
                        ready_string_splx = spea_main.join(cunet_list_db)

            # NORMALNY TEXT
            CLASSIC_TEXT = [
                'tytul_glowny', 'page_title_section_1', 'page_attached_worker_descriptions',
                'page_content_section_1', 'page_subcontent_section_1', 'page_subcontent_section_2',
                'page_title_section_3', 'page_content_section_3', 'page_title_section_4',
                'page_content_section_4', 'page_attached_worker_descriptions', 'page_price_table_title_section_5',
                'opis_home'
                ]
            if sekcja in CLASSIC_TEXT:
                exactly_what = None
                for c in CLASSIC_TEXT: 
                    if c == sekcja: exactly_what = c
                if exactly_what is None:
                    print("Problem Klucza")
                    return False
                ready_string_splx = value


            # TWORZENIE ZESTAWU ZAPYTANIA MySQL
            if ready_string_splx is not None and table_db is not None and column_db is not None and isinstance(id_db, int):
                if ready_string_splx=='':
                    ready_string_splx=None
                query = f"""
                        UPDATE {table_db}
                        SET {column_db} = %s
                        WHERE id = %s
                """
                params = (ready_string_splx, id_db)

        ####################################################
        # Aktualizacja tekstu w admins
        ####################################################
        if strona == 'team':
            ready_string_splx = None
            table_db = 'admins'
            column_db = sekcja
            id_db = id_number

            # NORMALNY TEXT
            CLASSIC_TEXT = [
                'name', 'stanowisko', 'kwalifikacje',
                'doswiadczenie', 'wyksztalcenie', 'email',
                'phone', 'facebook', 'instagram',
                'twitter', 'linkedin', 'opis'
            ]
            if sekcja in CLASSIC_TEXT:
                exactly_what = None
                for c in CLASSIC_TEXT: 
                    if c == sekcja: exactly_what = c
                if exactly_what is None:
                    print("Problem Klucza")
                    return False
                ready_string_splx = value


            # TWORZENIE ZESTAWU ZAPYTANIA MySQL
            if ready_string_splx is not None and table_db is not None and column_db is not None and isinstance(id_db, int):
                query = f"""
                        UPDATE {table_db}
                        SET {column_db} = %s
                        WHERE id = %s
                """
                params = (ready_string_splx, id_db)
        
        if strona == 'setting_company':
            ready_string_splx = None
            table_db = strona
            column_db = sekcja
            id_db = id_number

            # NORMALNY TEXT
            CLASSIC_TEXT = [
                "contact_address_homepage",
                "contact_address_contactpage",
                "contact_phone_general",
                "contact_email_general",
                "counter_treatment_per_week",
                "counter_team_in_employee",
                "counter_percent_of_satisfacted_consumer",
                "contact_bank_name",
                "contact_bank_account",
                "contact_bank_title",
                "contact_bank_guidelines_for_email"
            ]
            if sekcja in CLASSIC_TEXT:
                exactly_what = None
                for c in CLASSIC_TEXT: 
                    if c == sekcja: exactly_what = c
                if exactly_what is None:
                    print("Problem Klucza")
                    return False
                ready_string_splx = value

            DATETIME_STRING = ["counter_year_of_start"]
            if sekcja in DATETIME_STRING:
                exactly_what = None
                for c in DATETIME_STRING: 
                    if c == sekcja: exactly_what = c
                if exactly_what is None:
                    print("Problem Klucza")
                    return False

                try:
                    # Konwersja stringa na obiekt datetime
                    datetime_object = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
                    ready_string_splx = datetime_object
                except ValueError as e:
                    print(f"Błąd konwersji daty: {e}")
                    return False


            # TWORZENIE ZESTAWU ZAPYTANIA MySQL
            if ready_string_splx is not None and table_db is not None and column_db is not None and isinstance(id_db, int):
                query = f"""
                        UPDATE {table_db}
                        SET {column_db} = %s
                        WHERE id = %s
                """
                params = (ready_string_splx, id_db)

        if strona == 'system_setting':
            ready_string_splx = None
            table_db = strona
            column_db = sekcja
            id_db = id_number

            # NORMALNY TEXT
            CLASSIC_TEXT = [
                "config_smtp_username",
                "config_smtp_server",
                "config_smtp_port"                
            ]
            if sekcja in CLASSIC_TEXT:
                exactly_what = None
                for c in CLASSIC_TEXT: 
                    if c == sekcja: exactly_what = c
                if exactly_what is None:
                    print("Problem Klucza")
                    return False
                ready_string_splx = value
            
            # NORMALNY TEXT
            SE_DATA = ["config_smtp_password"]
            if sekcja in SE_DATA:
                exactly_what = None
                for c in SE_DATA: 
                    if c == sekcja: exactly_what = c
                if exactly_what is None:
                    print("Problem Klucza")
                    return False
                
                resultPs = encode_string(value, ENDoneslot)
                if "TK" in resultPs:
                    ready_string_splx = resultPs.get("TK", None)

            # TWORZENIE ZESTAWU ZAPYTANIA MySQL
            if ready_string_splx is not None and table_db is not None and column_db is not None and isinstance(id_db, int):
                query = f"""
                        UPDATE {table_db}
                        SET {column_db} = %s
                        WHERE id = %s
                """
                params = (ready_string_splx, id_db)

    elif data_type == 'switch':
        ####################################################
        # Aktualizacja stanów i statusów w tabela_uslug
        ####################################################
        if strona == 'treatment':
            ready_string_splx = None
            table_db = 'tabela_uslug'
            column_db = sekcja
            id_db = id_number

            # BANERS
            CLASSIC_INT = ['page_attached_worker_status', 'treatment_general_status']
            if sekcja in CLASSIC_INT:
                exactly_what = None
                for c in CLASSIC_INT: 
                    if c == sekcja: exactly_what = c
                if exactly_what is None:
                    print("Problem Klucza")
                    return False
                
                ready_string_splx = value

            # TWORZENIE ZESTAWU ZAPYTANIA MySQL
            if ready_string_splx is not None and table_db is not None and column_db is not None and isinstance(id_db, int):
                query = f"""
                        UPDATE {table_db}
                        SET {column_db} = %s
                        WHERE id = %s
                """
                params = (ready_string_splx, id_db)

        if strona == 'team':
            ready_string_splx = None
            table_db = 'admins'
            column_db = sekcja
            id_db = id_number

            # UPRAWNIENIA
            CLASSIC_INT = ['administrator', 'super_user', 'user']
            if sekcja in CLASSIC_INT:
                exactly_what = None
                for c in CLASSIC_INT: 
                    if c == sekcja: exactly_what = c
                if exactly_what is None:
                    print("Problem Klucza")
                    return False
                
                ready_string_splx = value

            # TWORZENIE ZESTAWU ZAPYTANIA MySQL
            if ready_string_splx is not None and table_db is not None and column_db is not None and isinstance(id_db, int):
                query = f"""
                        UPDATE {table_db}
                        SET {column_db} = %s
                        WHERE id = %s
                """
                params = (ready_string_splx, id_db)


    elif data_type == 'picker':
        if strona == 'treatment':
            ready_string_splx = None
            table_db = 'tabela_uslug'
            column_db = sekcja
            id_db = id_number

            CLASSIC_INT = [
                'page_attached_worker_id'
                ]
            if sekcja in CLASSIC_INT:
                exactly_what = None
                for c in CLASSIC_INT: 
                    if c == sekcja: exactly_what = c
                if exactly_what is None:
                    print("Problem Klucza")
                    return False
                
                ready_string_splx = value


            # Specyficzna zamiana na stringa dla ikony
            if sekcja == "icon":
                exactly_what = "icon"

                ready_string_splx = iconer_changer_by_id[value]

            # TWORZENIE ZESTAWU ZAPYTANIA MySQL
            if ready_string_splx is not None and table_db is not None and column_db is not None and isinstance(id_db, int):
                query = f"""
                        UPDATE {table_db}
                        SET {column_db} = %s
                        WHERE id = %s
                """
                params = (ready_string_splx, id_db)
        
    elif data_type == 'adder':
        if strona == 'treatment':
            ready_string_splx = None
            table_db = 'tabela_uslug'
            column_db = sekcja
            id_db = id_number

            TOADD_INT = [
                'page_attached_add_files'
                ]
            if sekcja in TOADD_INT:
                exactly_what = None
                for c in TOADD_INT: 
                    if c == sekcja: exactly_what = c
                if exactly_what is None:
                    print("Problem Klucza")
                    return False
                
                try: value = int(value)
                except ValueError:
                    print(f"Nieobsługiwany typ danych: {value}")
                    return False

                splet_key = exactly_what.replace('add', 'list')
                

                cunet_list_db = None
                for data_b in treatments_db_all_by_route_dict().values():
                    if 'id' in data_b and splet_key in data_b:
                        if data_b['id'] == id_db:
                            cunet_list_db = data_b[splet_key]
                            break
                if isinstance(cunet_list_db, list):
                    if value not in cunet_list_db:  # Sprawdź, czy wartość już nie istnieje na liście
                        cunet_list_db.append(value)
                    ready_string_splx = spea_main.join(map(str, cunet_list_db))
                    column_db = exactly_what.replace('add', 'splx')


            # TWORZENIE ZESTAWU ZAPYTANIA MySQL
            if ready_string_splx is not None and table_db is not None and column_db is not None and isinstance(id_db, int):
                query = f"""
                        UPDATE {table_db}
                        SET {column_db} = %s
                        WHERE id = %s
                """
                params = (ready_string_splx, id_db)

    elif data_type == 'remover':
        if strona == 'treatment':
            ready_string_splx = None
            table_db = 'tabela_uslug'
            column_db = sekcja
            id_db = id_number

            TOREMOVE_INT = [
                'page_attached_remove_files'
                ]
            if sekcja in TOREMOVE_INT:
                exactly_what = None
                for c in TOREMOVE_INT: 
                    if c == sekcja: exactly_what = c
                if exactly_what is None:
                    print("Problem Klucza")
                    return False
                
                splet_key = exactly_what.replace('remove', 'list')
                cunet_list_db = None
                for data_b in treatments_db_all_by_route_dict().values():
                    if 'id' in data_b and splet_key in data_b:
                        if data_b['id'] == id_db:
                            cunet_list_db = data_b[splet_key]
                            break

                if isinstance(cunet_list_db, list) and len(cunet_list_db) == ofparts:
                    if 0 <= index < len(cunet_list_db):  # Sprawdzenie zakresu
                        del cunet_list_db[index]
                        ready_string_splx = spea_main.join(map(str, cunet_list_db))
                        column_db = sekcja.replace('remove', 'splx')
                    else:
                        print("Index out of range")
                        return False

            # TWORZENIE ZESTAWU ZAPYTANIA MySQL
            if ready_string_splx is not None and table_db is not None and column_db is not None and isinstance(id_db, int):
                query = f"""
                        UPDATE {table_db}
                        SET {column_db} = %s
                        WHERE id = %s
                """
                params = (ready_string_splx, id_db)
            
            # zmiana zapytania na DELETE 
            TODELETE_INT = [
                'treatment_remove_page'
                ]
            if sekcja in TODELETE_INT:
                exactly_what = None
                for c in TODELETE_INT: 
                    if c == sekcja: exactly_what = c
                if exactly_what is None:
                    print("Problem Klucza")
                    return False
                ready_string_splx = True
                # TWORZENIE ZESTAWU ZAPYTANIA MySQL
                if ready_string_splx is not None and table_db is not None and isinstance(id_db, int):
                    query = f"""
                            DELETE FROM {table_db}
                            WHERE id = %s
                    """
                    params = (id_db,)
                    

    elif data_type == 'img':
        if strona == 'treatment':
            ready_string_splx = None
            table_db = 'tabela_uslug'
            column_db = sekcja
            id_db = id_number
            
            SPLX_PHOTOS = ['page_photo_content_links_splx_section_2']
            if sekcja in SPLX_PHOTOS:
                exactly_what = None
                for c in SPLX_PHOTOS: 
                    if c == sekcja: exactly_what = c
                if exactly_what is None:
                    print("Problem Klucza")
                    return False
                
                splet_key = exactly_what.replace('splx', 'list')
                
                cunet_list_db = None
                for data_b in treatments_db_all_by_route_dict().values():
                    if 'id' in data_b and splet_key in data_b:
                        if data_b['id'] == id_db:
                            cunet_list_db = data_b[splet_key]
                            break
                if isinstance(cunet_list_db, list):
                    if len(cunet_list_db) == ofparts:
                        cunet_list_db[index] = value
                        ready_string_splx = spea_main.join(cunet_list_db)

            SINGLE_PHOTOS = ['foto_page_header', 'optional_1', 'foto_home']
            if sekcja in SINGLE_PHOTOS:
                exactly_what = None
                for c in SINGLE_PHOTOS: 
                    if c == sekcja: exactly_what = c
                if exactly_what is None:
                    print("Problem Klucza")
                    return False
                ready_string_splx = value

            # TWORZENIE ZESTAWU ZAPYTANIA MySQL
            if ready_string_splx is not None and table_db is not None and column_db is not None and isinstance(id_db, int):
                query = f"""
                        UPDATE {table_db}
                        SET {column_db} = %s
                        WHERE id = %s
                """
                params = (ready_string_splx, id_db)
        
        if strona == 'team':
            ready_string_splx = None
            table_db = 'admins'
            column_db = sekcja
            id_db = id_number

            # AVATAR
            SINGLE_PHOTOS = ['avatar']
            if sekcja in SINGLE_PHOTOS:
                exactly_what = None
                for c in SINGLE_PHOTOS: 
                    if c == sekcja: exactly_what = c
                if exactly_what is None:
                    print("Problem Klucza")
                    return False
                
                ready_string_splx = value

            # TWORZENIE ZESTAWU ZAPYTANIA MySQL
            if ready_string_splx is not None and table_db is not None and column_db is not None and isinstance(id_db, int):
                query = f"""
                        UPDATE {table_db}
                        SET {column_db} = %s
                        WHERE id = %s
                """
                params = (ready_string_splx, id_db)

    elif data_type == 'url':
        query = "UPDATE elements SET url = ? WHERE id = ?"

    elif data_type == 'splx':
        if strona == 'treatment':
            ready_string_splx = None
            table_db = 'tabela_uslug'
            column_db = sekcja
            id_db = id_number
            
            SPLX_SINGLE_ITEM = ['html id tutaj']
            if sekcja in SPLX_SINGLE_ITEM:
                exactly_what = None
                for c in SPLX_SINGLE_ITEM: 
                    if c == sekcja: exactly_what = c
                if exactly_what is None:
                    print("Problem Klucza")
                    return False
                
                cunet_list_db = None
                for data_b in treatments_db_all_by_route_dict().values():
                    if 'id' in data_b and exactly_what in data_b:
                        if data_b['id'] == id_db:
                            cunet_list_db = data_b[exactly_what]
                            break
                if isinstance(cunet_list_db, str):
                    ready_string_splx = value
            
            SPLX_MULTI_ITEM = ['page_points_splx_section_1', 'page_price_table_content_splx_comma_section_5']
            if sekcja in SPLX_MULTI_ITEM:
                exactly_what = None
                for c in SPLX_MULTI_ITEM: 
                    if c == sekcja: exactly_what = c
                if exactly_what is None:
                    print("Problem Klucza")
                    return False
                
                splet_key = exactly_what.replace('splx', 'string')
                
                cunet_list_db = None
                for data_b in treatments_db_all_by_route_dict().values():
                    if 'id' in data_b and splet_key in data_b:
                        if data_b['id'] == id_db:
                            cunet_list_db = data_b[splet_key]
                            break
                if isinstance(cunet_list_db, list):
                    if len(cunet_list_db) == ofparts:
                        cunet_list_db[index] = value
                        ready_string_splx = spea_second.join(cunet_list_db)


            # TWORZENIE ZESTAWU ZAPYTANIA MySQL
            if ready_string_splx is not None and table_db is not None and column_db is not None and isinstance(id_db, int):
                query = f"""
                        UPDATE {table_db}
                        SET {column_db} = %s
                        WHERE id = %s
                """
                params = (ready_string_splx, id_db)

        if strona == 'setting_company':
            ready_string_splx = None
            table_db = strona
            column_db = sekcja
            id_db = id_number
            
            SPLX_SINGLE_ITEM = [
                "contact_transport_bus_splx",
                "contact_transport_train_splx",
                "contact_transport_metro_splx"
            ]
            if sekcja in SPLX_SINGLE_ITEM:
                exactly_what = None
                for c in SPLX_SINGLE_ITEM: 
                    if c == sekcja: exactly_what = c
                if exactly_what is None:
                    print("Problem Klucza")
                    return False
                
                ready_string_splx = value

            # TWORZENIE ZESTAWU ZAPYTANIA MySQL
            if ready_string_splx is not None and table_db is not None and column_db is not None and isinstance(id_db, int):
                query = f"""
                        UPDATE {table_db}
                        SET {column_db} = %s
                        WHERE id = %s
                """
                params = (ready_string_splx, id_db)
    else:
        print(f"Nieobsługiwany typ danych: {data_type}")
        return False

    # Wykonanie zapytania SQL
    if table_db and column_db and id_db and query and params:
        try:
            print(f"Pomyślnie zaktualizowano {column_db} w {table_db}, id={id_db}")
            return msq.insert_to_database(query, params)
        except Exception as e:
            print(f"Błąd wykonania zapytania SQL: {e}")
            return False

    print(f"Nie udało się zaktualizować danych dla element_id: {element_id}")
    return False

####################################################
# Funkcja do systematyzacji danych z bazy
####################################################
def treatments_db_all_by_route_dict(pick_element=False, route_string=''):
    """
    Pobiera wszystkie usługi z bazy danych i zwraca słownik, w którym kluczami są wartości kolumny `ready_route`,
    a wartościami słowniki reprezentujące wiersze z tabeli `tabela_uslug`.
    Jeśli pick_element=True, zwraca jedynie element o podanym `route_string`.
    """
    zapytanie_sql = """
        SELECT 
            *
        FROM tabela_uslug
        ORDER BY pozycja_kolejnosci ASC
    """

    try:
        # Połączenie z bazą danych i wykonanie zapytania
        db_dump = msq.connect_to_database(zapytanie_sql)
        export_dict = {}

        # Iteracja przez wyniki zapytania
        for data in db_dump:

            # Wypunktowania sekcja 1
            page_points_string_section_1_db = data[13]
            if isinstance(page_points_string_section_1_db, str) and spea_second in str(page_points_string_section_1_db):
                page_points_string_section_1_1, page_points_string_section_1_2 = str(page_points_string_section_1_db).split(spea_second)[:2]
                page_points_string_section_1_1_len = len(page_points_string_section_1_1.split(spea_main))
                if not page_points_string_section_1_1_len: page_points_string_section_1_1_len=1
                page_points_string_section_1_2_len = len(page_points_string_section_1_2.split(spea_main))
                if not page_points_string_section_1_2_len: page_points_string_section_1_2_len=1
                page_points_list_section_1 = [
                    check_separator_take_list(spea_main, page_points_string_section_1_1, page_points_string_section_1_1_len),
                    check_separator_take_list(spea_main, page_points_string_section_1_2, page_points_string_section_1_2_len),
                ]
                page_points_string_section_1 = [
                    page_points_string_section_1_1, page_points_string_section_1_2
                ]
            else:
                page_points_list_section_1 = [[],[]]
                page_points_string_section_1 = ['', '']

            # Cennik usług
            page_price_table_content_string_comma_section_5_db = data[22]
            if isinstance(page_price_table_content_string_comma_section_5_db, str) and spea_second in str(page_price_table_content_string_comma_section_5_db):
                page_price_table_content_string_comma_section_5_1, page_price_table_content_string_comma_section_5_2 = str(page_price_table_content_string_comma_section_5_db).split(spea_second)[:2]
                page_price_table_content_string_comma_section_5_1_len = len(page_price_table_content_string_comma_section_5_1.split(spea_main))
                if not page_price_table_content_string_comma_section_5_1_len: page_price_table_content_string_comma_section_5_1_len=1
                page_price_table_content_string_comma_section_5_2_len = len(page_price_table_content_string_comma_section_5_2.split(spea_main))
                if not page_price_table_content_string_comma_section_5_2_len: page_price_table_content_string_comma_section_5_2_len=1
                page_price_table_content_list_comma_section_5 = [
                    check_separator_take_list(spea_main, page_price_table_content_string_comma_section_5_1, page_price_table_content_string_comma_section_5_1_len),
                    check_separator_take_list(spea_main, page_price_table_content_string_comma_section_5_2, page_price_table_content_string_comma_section_5_2_len),
                ]
                page_price_table_content_string_comma_section_5 = [
                    page_price_table_content_string_comma_section_5_1, page_price_table_content_string_comma_section_5_2
                ]
            else:
                page_price_table_content_list_comma_section_5 = [[],[]]
                page_price_table_content_string_comma_section_5 = ['', '']
            
            # Dołaczony prcownik
            if data[23]:
                page_attached_worker_id_sql = f'WHERE id = {data[23]} AND status_usera = 1 AND user = 1'
                try: page_attached_worker_photo_name, page_attached_worker_photo_link = msq.connect_to_database(f'SELECT name, avatar FROM admins {page_attached_worker_id_sql};')[0]
                except IndexError: page_attached_worker_photo_name, page_attached_worker_photo_link = (None, None)
            else:
                page_attached_worker_photo_name, page_attached_worker_photo_link = (None, None)

            # Pliki
            if isinstance(data[26], str):
                page_attached_list_files_split = str(data[26]).split(spea_main)
                page_attached_list_files = []
                page_attached_object_files = []
                for c in page_attached_list_files_split:
                    try: 
                        c=int(c)
                        page_attached_list_files.append(c)
                    except ValueError: continue
                    
                    page_attached_object_files_sql = f'WHERE id = {c}'
                    try: 
                        page_attached_object_files_dump = msq.connect_to_database(f'SELECT id, name, file_name FROM files {page_attached_object_files_sql};')[0]
                        if len(page_attached_object_files_dump)==3:
                            page_attached_object_files_dict = {
                                'id': page_attached_object_files_dump[0], 
                                'name': page_attached_object_files_dump[1], 
                                'file_name': page_attached_object_files_dump[2]
                                }
                            page_attached_object_files.append(page_attached_object_files_dict)
                    except IndexError: continue
            else:
                page_attached_list_files = []
                page_attached_object_files = []

            # Tworzenie słownika dla pojedynczego rekordu
            theme = {
                "id": data[0],
                "foto_home": data[1],
                "icon": data[2],
                "tytul_glowny": data[3],
                "ready_route": data[4],
                "opis_home": data[5],
                "pozycja_kolejnosci": data[6],
                "baner_h1_splx": data[7],
                # Dzielenie banera na listę
                "baner_h1_splet": check_separator_take_list(spea_main, '' if data[7] is None else data[7], 3),
                "baner_h2_splx": data[8],
                "baner_h2_splet": check_separator_take_list(spea_main, '' if data[8] is None else data[8], 3),
                "page_hashtag_section": data[9],
                "foto_page_header": data[10],
                "page_title_section_1": data[11],
                "page_content_section_1": data[12],
                "page_points_splx_section_1": data[13],
                "page_points_string_section_1": page_points_string_section_1,
                "page_points_list_section_1": page_points_list_section_1,
                "page_subcontent_section_1": data[14],
                "page_photo_content_links_splx_section_2": data[15],
                # Dzielenie foto na listę
                "page_photo_content_links_list_section_2": check_separator_take_list(spea_main, '' if data[15] is None else data[15], 2),
                "page_subcontent_section_2": data[16],
                "page_title_section_3": data[17],
                "page_content_section_3": data[18],
                "page_title_section_4": data[19],
                "page_content_section_4": data[20],
                "page_price_table_title_section_5": data[21],
                "page_price_table_content_splx_comma_section_5": data[22],
                # Dzielenie wypunktowania na kolumny stringów
                "page_price_table_content_string_comma_section_5": page_price_table_content_string_comma_section_5,
                # Dzielenie wypunktowania na kolumny list
                "page_price_table_content_list_comma_section_5": page_price_table_content_list_comma_section_5,
                "page_attached_worker_id": data[23],
                "page_attached_worker_photo_name": page_attached_worker_photo_name,
                "page_attached_worker_photo_link": page_attached_worker_photo_link,
                "page_attached_worker_descriptions": data[24],
                "page_attached_worker_status": data[25],
                "page_attached_splx_files": data[26],
                # Dzielenie załączone na listę
                "page_attached_list_files": page_attached_list_files,
                "page_attached_object_files": page_attached_object_files,
                "page_attached_treatments": data[27],
                "page_attached_contact": data[28],
                "page_attached_status": data[29],
                "page_attached_gallery_splx": data[30],
                "treatment_general_status": data[31],
                "optional_1": data[32],
                "optional_2": data[33],
                "optional_3": data[34],
                "data_utworzenia": data[35],
            }

            # Dodanie rekordu do eksportowanego słownika
            export_dict[data[4]] = theme

        if not pick_element:
            return export_dict
        else:
            if route_string in export_dict:
                return export_dict[route_string]
            else:
                print(f"Wystąpił błąd! Podany route '{route_string}' nie istnieje w dumpie z bazy.")
                return {}

    except Exception as e:
        print(f"Wystąpił błąd: {e}")
        return {}

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

def calculate_statistics():
    
    company_setting = get_company_setting()
    # Tymczasowe zmienne prototypowe
    tygodniowa_statystyka_uslug = company_setting.get('zabiegow_na_tydzien', 1) # 120  # Liczba usług wykonanych w tygodniu
    data_rozpoczecia_dzialalnosci = company_setting.get('rok_rozpoczecia', datetime(1989, 5, 3)) # datetime(1989, 5, 20)  # Data rozpoczęcia działalności
    liczba_pracownikow = len(generator_teamDB())  # Aktualna liczba pracowników
    zadeklarowani_pracownicy = company_setting.get('ponad_zespol', 0) # 10  # Członkowie zespołu z poza strony www
    procent_zadowolonych_klientow = company_setting.get('procent_klientow', 1) # 75  # Zadeklarowany procent zadowolonych klientów (w %)

    # Wyliczenia
    zrealizowane_uslugi = tygodniowa_statystyka_uslug * 52  # Zrealizowane usługi w skali roku
    lata_doswiadczenia = datetime.now().year - data_rozpoczecia_dzialalnosci.year
    if datetime.now().month < data_rozpoczecia_dzialalnosci.month or (
        datetime.now().month == data_rozpoczecia_dzialalnosci.month and datetime.now().day < data_rozpoczecia_dzialalnosci.day
    ):
        lata_doswiadczenia -= 1  # Uwzględnienie niepełnego roku

    czlonkowie_zespolu = liczba_pracownikow + zadeklarowani_pracownicy  # Liczba członków zespołu
    zadowoleni_klienci = int((procent_zadowolonych_klientow / 100) * zrealizowane_uslugi)  # Liczba zadowolonych klientów

    # Tworzenie słownika
    statystyki = {
        "zrealizowane_uslugi": zrealizowane_uslugi,
        "lata_doswiadczenia": lata_doswiadczenia,
        "czlonkowie_zespolu": czlonkowie_zespolu,
        "zadowoleni_klienci": zadowoleni_klienci,
    }

    return statystyki

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

def get_company_setting():
    got_data_setting_company = take_data_where_ID("*", 'setting_company', 'id', 1)[0]
    got_data_system_setting = take_data_where_ID("config_smtp_username, config_smtp_server, config_smtp_port", 'system_setting', 'id', 1)[0]

    export = {
        "config_smtp_username": got_data_system_setting[0],
        "config_smtp_server": got_data_system_setting[1],
        "config_smtp_port": got_data_system_setting[2],

        "contact_address_homepage": got_data_setting_company[1],
        "contact_address_contactpage": got_data_setting_company[2],
        "contact_phone_general": got_data_setting_company[3],
        "contact_email_general": got_data_setting_company[4],
        "contact_transport_bus_splx": got_data_setting_company[5],
        "contact_transport_bus_list": str(got_data_setting_company[5]).split(spea_main),
        "contact_transport_train_splx": got_data_setting_company[6],
        "contact_transport_train_list": str(got_data_setting_company[6]).split(spea_main),
        "zabiegow_na_tydzien": got_data_setting_company[8],
        "rok_rozpoczecia": got_data_setting_company[9], # datetime(1989, 5, 20),
        "ponad_zespol": got_data_setting_company[10],
        "procent_klientow": got_data_setting_company[11],
        "contact_bank_name": got_data_setting_company[12],
        "contact_bank_account": got_data_setting_company[13],
        "contact_bank_title": got_data_setting_company[14],
        "contact_bank_guidelines_for_email": got_data_setting_company[15]
    }
    return export

def insertPassDB(password, salt, user_id):
    """
    Aktualizuje hasło i sól użytkownika w bazie danych.
    
    :param password: Hasło do zapisania w bazie (już zahashowane).
    :param salt: Sól do zapisania w bazie.
    :param user_id: ID użytkownika, którego dane mają być zaktualizowane.
    :return: True, jeśli aktualizacja powiodła się, False w przeciwnym razie.
    """
    zapytanie_sql = '''
        UPDATE admins 
        SET password = %s, 
            salt = %s
        WHERE id = %s;
    '''
    dane = (password, salt, user_id)
    return msq.insert_to_database(zapytanie_sql, dane)

def opion_db():
    # Zapytanie SQL do pobrania danych
    zapytanie_sql = """
        SELECT 
            id, 
            opinion,
            author,
            avatar,
            role,
            sort_order
        FROM opinions
        ORDER BY sort_order ASC
    """
    # Pobranie danych z bazy
    db_dump = msq.connect_to_database(zapytanie_sql)

    # Przygotowanie listy wyników
    export = [
        {
            "id": data[0],
            "opinion": data[1],
            "author": data[2],
            "avatar": data[3],
            "role": data[4],
            "sort_order": data[5],
        }
        for data in db_dump
    ]

    # Lista liter alfabetu (nie jest to konieczne, można użyć `string.ascii_uppercase` bezpośrednio)
    alphabet = set(string.ascii_uppercase)

    # Generowanie avatarów, jeśli brak danych
    for opinion in export:
        if not opinion['avatar']:  # Tylko jeśli avatar jest pusty
            variant = random.choice(['dark_on_light', 'light_on_dark'])  # Losowy wariant
            author_first_letter = (opinion['author'] or 'X')[0].upper()  # Pierwsza litera autora lub 'X'

            # Wybór avatara
            avatar_letter = author_first_letter if author_first_letter in alphabet else 'X'
            opinion['avatar'] = f"https://duodentbielany.pl/static/img/opion_avatars/{avatar_letter}_{variant}.png"

    return export

def get_visit_data(link_hash):
    try: 
        data_of_visit = take_data_where_ID("*", 'appointment_requests', 'link_hash', link_hash)[0]
    
        formated_visit_dict = {
            'id': data_of_visit[0],
            'name': data_of_visit[1],
            'email': data_of_visit[2],
            'phone': data_of_visit[3],
            'patient_type': data_of_visit[4],
            'visit_date': data_of_visit[5],
            'consent': data_of_visit[6],
            'status': data_of_visit[7],
            'created_at': data_of_visit[8],
            'in_progress_date': data_of_visit[9],
            'in_progress_description': data_of_visit[10],
            'in_progress_flag': data_of_visit[11],
            'verified_date': data_of_visit[12],
            'verified_description': data_of_visit[13],
            'verified_flag': data_of_visit[14],
            'confirmed_date': data_of_visit[15],
            'confirmed_description': data_of_visit[16],
            'confirmed_flag': data_of_visit[17],
            'cancelled_date': data_of_visit[18],
            'cancelled_description': data_of_visit[19],
            'cancelled_flag': data_of_visit[20],
            'error_date': data_of_visit[21],
            'error_description': data_of_visit[22],
            'error_flag': data_of_visit[23],
            'link_hash': data_of_visit[24]
        }
        return formated_visit_dict
    except IndexError: 
        return {}

def set_youtube_links(mode='by_color', yt_color='green'):
    # Pobranie filmów przypisanych do poszczególnych kolorów
    query = """
        SELECT color, video_url FROM video_eye_colors
        INNER JOIN videos ON video_eye_colors.video_id = videos.id
    """
    color_videos = msq.connect_to_database(query)

    # Przypisanie linków do słownika
    youtube_links = {'green': None, 'red': None, 'blue': None}

    for color, video_url in color_videos:
        if color in youtube_links:
            youtube_links[color] = video_url

    # Obsługa różnych trybów zwracania danych
    if mode == 'by_color':
        return youtube_links.get(yt_color, None)
    elif mode in ['tuple', 'by_tuple']:
        return tuple(youtube_links[color] for color in ['green', 'red', 'blue'])
    elif mode == 'by_dict':
        return youtube_links
    return None








# ========================================================================================= #
#  FUNKCJE OPERACYJNE
#  
#  Logika biznesowa aplikacji:
#  - Algorytmy przetwarzania danych.
#  - Zasady autoryzacji i uwierzytelniania.
#  - Operacje na modelach biznesowych.
#  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -  
#  Rdzeń działania aplikacji, ściśle powiązany z endpointami.
# ========================================================================================= #
# Funkcja pomocnicza do generowania losowego hasła
def generate_random_password(length=12):
    """
    Generuje losowe hasło o podanej długości.
    Zawiera litery, cyfry i znaki specjalne.
    """
    

    characters = string.ascii_letters + string.digits + '!@#$%^&*()-_=+[]{}|;:\'",.<>/?`~'
    return ''.join(random.choice(characters) for _ in range(length))

def equalizatorSaltPass(user_id, verification_data, set_password=None):
    """
    Weryfikuje i/lub aktualizuje hasło użytkownika z użyciem soli.

    :param user_id: ID użytkownika, którego hasło ma zostać zaktualizowane.
    :param verification_data: Dane do weryfikacji (np. stare hasło lub inne kryteria).
    :param set_password: Nowe hasło (jeśli podane), w przeciwnym razie zostanie wygenerowane nowe hasło.
    :return: Komunikat o sukcesie lub błędzie.
    """
    # Pobierz aktualną sól i hasło użytkownika z bazy
    try:
        salt_old = take_data_where_ID('salt', 'admins', 'id', user_id)[0][0]
        password_old = take_data_where_ID('password', 'admins', 'id', user_id)[0][0]
    except IndexError:
        return {'status': False, 'message': 'Problem z ID usera'}
    
    if verification_data is not None:
        # Weryfikacja starego hasła
        verificated_old_password = hash.hash_password(verification_data, salt_old)
        if verificated_old_password != password_old:
            return {'status': False, 'message': 'Nieprawidłowe stare hasło'}
    
    # Wygenerowanie nowego hasła i soli (jeśli set_password is None)
    if set_password is None:
        new_password = hash.generate_random_password()  # Funkcja generująca nowe losowe hasło
    else:
        new_password = set_password
    
    # Hasło musi spełniać określone kryteria
    if len(new_password) < 8:
        return {'status': False, 'message': 'Hasło musi mieć co najmniej 8 znaków'}
    if not any(char.isupper() for char in new_password):
        return {'status': 'error', 'message': 'Hasło musi zawierać co najmniej jedną wielką literę'}
    if not any(char in '!@#$%^&*()-_=+[]{}|;:\'",.<>/?`~' for char in new_password):
        return {'status': False, 'message': 'Hasło musi zawierać co najmniej jeden znak specjalny'}

    # Generowanie nowej soli i haszowanie nowego hasła
    salt_new = hash.generate_salt()
    hashed_password = hash.hash_password(new_password, salt_new)
    
    # Aktualizacja w bazie danych
    if insertPassDB(hashed_password, salt_new, user_id):
        return {'status': True, 'message': 'Hasło zostało pomyślnie zaktualizowane', 'new_password': new_password}
    else:
        return {'status': False, 'message': 'Nie udało się zaktualizować hasła w bazie danych'}

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

def process_photo(photo, save_path):
    try:
        # Otwórz obraz
        img = Image.open(photo)

        # Sprawdzenie orientacji obrazu (portretowa)
        width, height = img.size
        if width > height:
            print("Zdjęcie nie jest w orientacji portretowej.")
            return False

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
        return True
    except Exception as e:
        print(f"Error processing photo: {e}")
        return False

def editing_id_updater_reader(element_id):
    element_id_split_part = element_id.split("-")
    export_dict = {'status': False}
    if len(element_id_split_part) != 5:
        return export_dict
    try:
        strona=element_id_split_part[0]
        sekcja=element_id_split_part[1]
        id_number=int(element_id_split_part[2])
        part=int(element_id_split_part[3])
        index=part-1
        ofparts=int(element_id_split_part[4])
        export_dict={
            'status': True,
            'strona': strona, 
            'sekcja': sekcja, 
            'id_number': id_number, 
            'index': index, 
            'part': part, 
            'ofparts': ofparts, 
            }
    except (IndexError, ValueError):
        export_dict = {'status': False}
    return export_dict

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

def direct_by_permision(session, permission_sought=None):
    """
    Zwraca poziom uprawnień użytkownika na podstawie sesji.
    
    :param session: dict - obiekt sesji zawierający informacje o użytkowniku.
    :param permission_sought: str - nazwa konkretnego uprawnienia do sprawdzenia.
    :return: int - poziom uprawnień (4 - Administrator, 3 - Super User, 2 - Pracownik, 0 - Brak uprawnień).
    """
    if not session.get('username', False):
        # Użytkownik niezalogowany
        return 0

    userperm = session.get('userperm', {})

    if permission_sought:
        # Jeśli określono konkretne uprawnienie
        return userperm.get(permission_sought, 0)

    # Sprawdzenie poziomu ogólnego uprawnienia
    if userperm.get('administrator', 0) == 1:
        return 4  # Administrator
    elif userperm.get('super_user', 0) == 1:
        return 3  # Super user
    elif userperm.get('user', 0) == 1:
        return 2  # Pracownik
    else:
        return 0  # Brak dodatkowych uprawnień

def get_user_role(session):
    if direct_by_permision(session, permission_sought='administrator'):
        return "administrator"
    elif direct_by_permision(session, permission_sought='super_user'):
        return "super_user"
    elif direct_by_permision(session, permission_sought='user'):
        return "user"
    return "guest"

def firstConntactMessage(email_address, procedure, extra_data=None):
    # Przykładowe dane bazowe
    subject = ""
    html_body = ""

    # Obsługa różnych procedur
    if procedure == "appointment":
        subject = "Status Rezerwacji Wizyty - Wniosek przyjęty do realizacji!"
        html_body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
                <div style="text-align: center; margin-bottom: 20px;">
                    <img src="https://duodentbielany.pl/static/img/logotyp_duodent_bielany_solidfill_light.png" alt="Duodent Bielany Logo" style="width: 350px; height: auto;">
                </div>
                <h1 style="color: #24363f;">Witaj!</h1>
                <p>
                    Dziękujemy za złożenie wniosku o rezerwację wizyty w naszej placówce stomatologicznej Duodent. 
                    Państwa zgłoszenie zostało przyjęte do realizacji i obecnie trwa proces rejestracji.
                </p>
                <p>
                    Nasz zespół recepcyjny wkrótce skontaktuje się z Państwem w celu dopełnienia niezbędnych formalności oraz ustalenia szczegółów wizyty, 
                    takich jak godzina spotkania we wskazanym dniu. Prosimy o cierpliwość, zwykle kontaktujemy się w ciągu 24 godzin.
                </p>
                <p>
                    Jeśli mają Państwo pilne pytania lub chcą dokonać dodatkowych ustaleń, zapraszamy do kontaktu telefonicznego z naszą recepcją 
                    pod numerem <strong style="color: #d60000;">790 777 350</strong>. 
                </p>
                <p>
                    Jesteśmy do Państwa dyspozycji w godzinach otwarcia przychodni, a nasz zespół z przyjemnością udzieli wszelkich informacji i pomocy.
                </p>
                <p style="font-size: 12px; color: #686d71;">
                    <strong style="color: #d60000;">UWAGA:</strong> Wysłanie wniosku o rezerwację <strong style="color: #24363f;">nie gwarantuje jeszcze potwierdzenia terminu wizyty</strong>. 
                    Gwarantuje rozpoczęcie procesu rejestracji. Prosimy czekać na kontakt z naszej strony.
                </p>
                <p>
                    Pozdrawiamy serdecznie,<br>
                    <strong>Zespół Duodent</strong>
                </p>
                <p style="font-size: 12px; color: #686d71; margin-top: 30px; border-top: 1px solid #ccc; padding-top: 10px;">
                    Ten e-mail został wygenerowany automatycznie, ale można odpowiadać na tę wiadomość. W przypadku pytań prosimy o kontakt pod 
                    adresem e-mail <a href="mailto:arkuszowa@duodent.com.pl" style="color: #24363f;">arkuszowa@duodent.com.pl</a>.
                </p>
                <p style="font-size: 12px; color: #d60000; margin-top: 10px;">
                    <strong>UWAGA!</strong> Jeśli to nie Ty rejestrowałeś(-aś) wizytę w naszej przychodni, prosimy o niezwłoczny kontakt 
                    telefoniczny pod numerem <strong>790 777 350</strong> lub mailowy na adres 
                    <a href="mailto:arkuszowa@duodent.com.pl" style="color: #24363f;">arkuszowa@duodent.com.pl</a>.
                </p>
            </body>
        </html>
        """
    elif procedure == "general_inquiry":
        subject = "Dziękujemy za kontakt!"
        html_body = f"""
        <html>
            <body>
                <div style="text-align: center; margin-bottom: 20px;">
                    <img src="https://duodentbielany.pl/static/img/logotyp_duodent_bielany_solidfill_light.png" alt="Duodent Bielany Logo" style="width: 350px; height: auto;">
                </div>
                <h1 style="color: #24363f;">Witaj!</h1>
                <p>Dziękujemy za przesłanie zapytania. Odpowiemy na nie w możliwie najszybszym czasie.</p>
                <p>Jeśli potrzebujesz szybkiego kontaktu, skorzystaj z naszego numeru telefonu: <strong>790 777 350</strong>.</p>
                <p>Pozdrawiamy,<br>Zespół Duodent</p>
                <p style="font-size: 12px; color: #686d71; margin-top: 30px; border-top: 1px solid #ccc; padding-top: 10px;">
                    Ten e-mail został wygenerowany automatycznie ale można odpowiadać na tę wiadomość. W przypadku pytań prosimy o kontakt pod 
                    adresem e-mail <a href="mailto:arkuszowa@duodent.com.pl" style="color: #24363f;">arkuszowa@duodent.com.pl</a>.
                </p>
            </body>
        </html>
        """
    elif procedure == "password_is_changed":
        if extra_data is None:
            print(f"Procedura: {procedure} wymaga podania wartości extra_data, która obecnie jest ustawiona na: {extra_data}")
            return False
        subject = "Zmiana hasła w aplikacji Duodent Bielany"
        html_body = f"""
        <html>
            <body>
                <div style="text-align: center; margin-bottom: 20px;">
                    <img src="https://duodentbielany.pl/static/img/logotyp_duodent_bielany_solidfill_light.png" 
                        alt="Duodent Bielany Logo" style="width: 350px; height: auto;">
                </div>
                <h1 style="color: #24363f;">Witaj!</h1>
                <p>Twoje hasło do aplikacji Duodent Bielany zostało zmienione. Poniżej znajdziesz nowe hasło do logowania:</p>
                <p><strong>Nowe hasło:</strong> {extra_data}</p>
                <p style="color: red;">Jeżeli potrzebujesz swój login skontaktuj się z <a href="mailto:admin@duodent.com.pl" style="color: #24363f;">administratorem systemu: admin@duodent.com.pl</a></p>
                <p>W razie jakichkolwiek problemów z logowaniem skorzystaj z naszego numeru telefonu: <strong>790 777 350</strong></p>
                <p>Pozdrawiamy,<br>Zespół Duodent</p>
                <p style="font-size: 12px; color: #686d71; margin-top: 30px; border-top: 1px solid #ccc; padding-top: 10px;">
                    Ten e-mail został wygenerowany automatycznie, ale można odpowiadać na tę wiadomość. 
                    W przypadku pytań prosimy o kontakt pod adresem e-mail 
                    <a href="mailto:admin@duodent.com.pl" style="color: #24363f;">admin@duodent.com.pl</a>.
                </p>
            </body>
        </html>
        """
    else:
        print(f"Nieznana procedura: {procedure}")
        return False

    # Wywołaj funkcję wysyłania e-maila HTML
    try:
        send_html_email(subject, html_body, email_address)
        print(f"Powiadomienie wysłane do {email_address} dla procedury {procedure}.")
        return True
    except Exception as e:
        print(f"Błąd wysyłania powiadomienia: {e}")
        return False

class LoginForm(FlaskForm):
    username = StringField('Nazwa użytkownika', validators=[DataRequired()])
    password = PasswordField('Hasło', validators=[DataRequired()])
    submit = SubmitField('Zaloguj się')

















# ========================================================================================= #
#  ENDPOINTY SYSTEMOWE
#  
#  Endpointy wykorzystywane wewnętrznie przez system:
#  - Zarządzanie sesjami użytkowników.
#  - Monitorowanie stanu aplikacji.
#  - Automatyczne zadania systemowe.
#  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -  
#  Obsługiwane przez role systemowe, bez dostępu dla użytkowników końcowych.
# ========================================================================================= #

@app.template_filter('smart_truncate')
def smart_truncate(content, length=400):
    if len(content) <= length:
        return content
    else:
        # Znajdujemy miejsce, gdzie jest koniec pełnego słowa, nie przekraczając maksymalnej długości
        truncated_content = content[:length].rsplit(' ', 1)[0]
        return f"{truncated_content}..."

@app.template_filter('linebreaksbr')
def linebreaksbr(value):
    if not isinstance(value, str):
        return value
    return value.replace('\n', '<br />')

# ERROR 404
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html', pageTitle='Strona nie znaleziona'), 404

# ERROR 500
@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html', pageTitle='Błąd serwera'), 500

@app.context_processor
def inject_shared_variable():

    treatmentFooter = treatments_db(True)
    company_setting = get_company_setting()
    if len(treatmentFooter) >= 3:
        treatmentFooter = treatmentFooter[:3]

    if ',' in company_setting.get('contact_address_contactpage',''):
        contact_address_contactpage_city = company_setting.get('contact_address_contactpage', ' , ').split(',')[0].strip()
        contact_address_contactpage_street = company_setting.get('contact_address_contactpage', ' , ').split(',')[1].strip()
    else:
        contact_address_contactpage_city = None
        contact_address_contactpage_street = None

    youtube_links = set_youtube_links('by_dict')  # Pobieramy wszystko na raz
    return {
        'userName': session.get("username", 'NotLogin'),
        'treatmentMenu': {item["ready_route"]: item["tytul_glowny"] for item in treatments_db(True)},
        'treatmentFooter': treatmentFooter,
        'companyStats': calculate_statistics(),
        'contact_address_homepage': company_setting.get('contact_address_homepage'),
        'contact_address_contactpage': company_setting.get('contact_address_contactpage'),
        'contact_address_contactpage_city': contact_address_contactpage_city,
        'contact_address_contactpage_street': contact_address_contactpage_street,
        'contact_phone_general': company_setting.get('contact_phone_general'),
        'contact_phone_general_thin': company_setting.get('contact_phone_general', '').replace(' ', ''),
        'contact_phone_general_no48': company_setting.get('contact_phone_general', '').replace('+48', '').strip(),
        'contact_email_general': company_setting.get('contact_email_general'),
        'contact_transport_bus_list': company_setting.get('contact_transport_bus_list'),
        'contact_transport_train_list': company_setting.get('contact_transport_train_list'),
        'contact_bank_name': company_setting.get('contact_bank_name'),
        'contact_bank_account': company_setting.get('contact_bank_account'),
        'contact_bank_title': company_setting.get('contact_bank_title'),
        'contact_bank_guidelines_for_email': company_setting.get('contact_bank_guidelines_for_email'),
        # Nowe zmienne z filmami przypisanymi do kolorów
        'youtube_green': youtube_links.get('green', ''),
        'youtube_red': youtube_links.get('red', ''),
        'youtube_blue': youtube_links.get('blue', '')
    }

@app.context_processor
def utility_processor():
    """
    Dodaje `os.path.exists` i `current_app.static_folder` do kontekstu Jinja2.
    """
    return dict(
        os=os,
        current_app=current_app
    )
















# ========================================================================================= #
#  ENDPOINTY KATALOGÓW
#  
#  Obsługa publicznych katalogów i list:
#  - Przeglądanie zasobów.
#  - Filtrowanie i wyszukiwanie.
#  - Eksport danych do plików.
#  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -  
#  Publicznie dostępne dla użytkowników końcowych.
# ========================================================================================= #

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

















# ========================================================================================= #
#  ENDPOINTY ADMINISTRATORA
#  
#  Funkcjonalności dostępne tylko dla administratorów:
#  - Zarządzanie użytkownikami i danymi.
#  - Dodawanie, edytowanie i usuwanie zasobów.
#  - Generowanie raportów.
#  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -  
#  Wymagają autoryzacji i podwyższonych uprawnień.
# ========================================================================================= #

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

@app.route('/admin/manage-password', methods=['POST'])
def manage_password():
    """
    Endpoint do zarządzania hasłami użytkowników w systemie.
    Obsługuje role: administrator, super_user i pracownik.
    """
    if 'username' not in session:
        return jsonify({'status': 'error', 'message': 'Musisz być zalogowany, aby uzyskać dostęp do tej funkcji.'}), 403

    form_data = request.form.to_dict()
    user_id = form_data.get('user_id', None)
    old_password = form_data.get('old_password', None)
    new_password = form_data.get('new_password', None)
    repeat_password = form_data.get('repeat_password', None)
    generate_password = form_data.get('generate_password', '').lower() in ['true', 'on']
    own_user_id = form_data.get('own_user_id', None)

    if user_id is None and own_user_id is not None:
        user_id = own_user_id


    print(form_data)
    print(generate_password)

    try: email = take_data_where_ID('email', 'admins', 'id', user_id)[0][0]
    except IndexError: return jsonify({'status': 'error', 'message': 'Id nie przeszło weryfikacji.'}), 400
    # Pobranie uprawnień
    user_permissions = {
        'admin': direct_by_permision(session, permission_sought='administrator'),
        'super_user': direct_by_permision(session, permission_sought='super_user'),
        'user': direct_by_permision(session, permission_sought='user'),
    }

    # Logika dla administratora
    if user_permissions['admin']:
        if generate_password:
            result = equalizatorSaltPass(user_id, None, set_password=None)
        elif new_password and new_password == repeat_password:
            result = equalizatorSaltPass(user_id, None, set_password=new_password)
        else:
            return jsonify({'status': 'error', 'message': 'Hasła nie są identyczne lub nie podano danych.'}), 400

        if result['status']:
            
            if firstConntactMessage(email, "password_is_changed", extra_data=result.get('new_password')):
                return jsonify({'status': 'success', 'message': 'Hasło zmienione i wysłano e-mail.'})
            else:
                return jsonify({'status': 'error', 'message': 'Hasło zmienione, ale e-mail nie został wysłany.'})
        else:
            return jsonify({'status': 'error', 'message': result['message']}), 400

    # Logika dla super użytkownika
    elif user_permissions['super_user']:
        if generate_password:
            result = equalizatorSaltPass(user_id, verification_data=None, set_password=None)
        elif new_password and new_password == repeat_password and own_user_id != user_id:
            result = equalizatorSaltPass(user_id, verification_data=None, set_password=new_password)
        elif new_password and new_password == repeat_password and own_user_id == user_id:
            result = equalizatorSaltPass(user_id, verification_data=old_password, set_password=new_password)
        else:
            return jsonify({'status': 'error', 'message': 'Hasła nie są identyczne lub nie podano danych.'}), 400

        if result['status']:
            
            if firstConntactMessage(email, "password_is_changed", extra_data=result.get('new_password')):
                return jsonify({'status': 'success', 'message': 'Hasło zmienione i wysłano e-mail.'})
            else:
                return jsonify({'status': 'error', 'message': 'Hasło zmienione, ale e-mail nie został wysłany.'})
        else:
            return jsonify({'status': 'error', 'message': result['message']}), 400

    # Logika dla pracownika
    elif user_permissions['user']:
        if str(user_id) != str(session.get('user_data',{}).get('id')):
            return jsonify({'status': 'error', 'message': 'Pracownik może zmieniać hasło tylko dla siebie.'}), 403

        result = equalizatorSaltPass(user_id, verification_data=None, set_password=None)

        if result['status']:
            
            if firstConntactMessage(email, "password_is_changed", extra_data=result.get('new_password')):
                return jsonify({'status': 'success', 'message': 'Hasło zmienione i wysłano e-mail.'})
            else:
                return jsonify({'status': 'error', 'message': 'Hasło zmienione, ale e-mail nie został wysłany.'})
        else:
            return jsonify({'status': 'error', 'message': result['message']}), 400

    # Brak uprawnień
    return jsonify({'status': 'error', 'message': 'Brak odpowiednich uprawnień.'}), 403

@app.route('/admin/team-stomatologia')
def team_stomatologia():
    """Strona zespołu stomatologia."""
    if 'username' not in session:
        return redirect(url_for('index'))
    
    if not (session['userperm']['administrator'] == 1 or session['userperm']['super_user'] == 1):
        flash('Nie masz uprawnień do zarządzania tymi zasobami. Skontaktuj się z administratorem!', 'danger')
        return redirect(url_for('index'))

    preparoator_team_dict = preparoator_team('user', 3)


    return render_template(
            "team_management_stomatologia.html", 
            members=preparoator_team_dict['collections'], 
            photos_dict=preparoator_team_dict['employee_photo_dict']
            )

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
        treatments_items=treatments_db(False)
    )

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

@app.route('/admin/ustawienia-aplikacji')
def ustawienia_aplikacji():
    """Ustawienia Strony Duodent BIelany."""
    
    # Sprawdzanie uprawnień
    # ========================================================
    # 🌟 Model implementacji uprawnień - Rekomendacja 🌟
    # Ten kod jest czytelny, modułowy i łatwy w rozbudowie.
    # Każdy poziom uprawnień ma jasno określoną logikę.
    # Użycie funkcji `direct_by_permision` zapewnia elastyczność.
    # Idealne do zastosowania w wielu endpointach systemu!
    # ========================================================
    if session.get('username', False):
        if not (
                direct_by_permision(session, permission_sought='administrator')\
                    # or direct_by_permision(session, permission_sought='super_user')
            ):  # Brak uprawnień
            return redirect(url_for('index'))
    else:
        # Użytkownik niezalogowany
        return redirect(url_for('index'))


    return render_template(
            "setting_company.html", 
            companyData=get_company_setting(),
            adminTrue=True
            )

    
@app.route('/admin/password-managment', methods=['GET'])
def password_managment():
    """Ustawienia haseł administratorów."""

    # Sprawdzanie uprawnień
    if 'username' not in session:
        flash("Musisz być zalogowany, aby uzyskać dostęp do tego zasobu.", 'danger')
        return redirect(url_for('index'))
    
    user_role = None

    # Pobierz najwyższą rolę użytkownika
    if direct_by_permision(session, permission_sought='administrator'):
        user_role = "administrator"
    elif direct_by_permision(session, permission_sought='super_user'):
        user_role = "super_user"
    elif direct_by_permision(session, permission_sought='user'):
        user_role = "user"
    else:
        flash("Brak uprawnień do dostępu do tego zasobu.", 'danger')
        return redirect(url_for('index'))
    
    userDataDB = generator_userDataDB()

    superuser_worker_select = []
    for uData in userDataDB:
        insertRekord = {
                'id': uData.get('id'),
                'name': uData.get('name'),
                'role': getuserrole(uData),
                'roles': getUserRoles(uData),
                'login': uData.get('login')
            }
        superuser_worker_select.append(insertRekord)


    # Przygotowanie struktur do weryfikacji
    users_data = {}
    permTempDict = {}

    for un in userDataDB:
        permTempDict[un['login']] = un['uprawnienia']
        users_data[un['login']] = {
            'id': un['id'],
            'name': un['name'],
            'stanowisko': un['stanowisko'],
            'opis': un['opis'],
            'email': un['email'],
            'avatar': un['avatar'],
            'contact': un['contact'],
            'login': un['login']

        }

    own_user_data = users_data.get(session.get('username',''), {})
    own_userperm = permTempDict.get(session.get('username',''), {})
    {
    'id': session.get('user_data',{}).get('id'),
    'name': session.get('user_data',{}).get('name'),
    'avatar': session.get('user_data',{}).get('avatar'),
    'login': session.get('user_data',{}).get('avatar'),
    
    }


    # Renderowanie szablonu z rolą użytkownika
    return render_template(
        "rootipa.html",
        user_role=user_role,
        superuser_worker_select=superuser_worker_select,
        own_user_data=own_user_data,
        own_userperm=own_userperm
    )

@app.route('/admin/opinie', methods=['GET'])
def opinion_managment():
    """Zarządzanie opiniami"""
    # Sprawdzanie uprawnień
    # ========================================================
    # 🌟 Model implementacji uprawnień - Rekomendacja 🌟
    # Ten kod jest czytelny, modułowy i łatwy w rozbudowie.
    # Każdy poziom uprawnień ma jasno określoną logikę.
    # Użycie funkcji `direct_by_permision` zapewnia elastyczność.
    # Idealne do zastosowania w wielu endpointach systemu!
    # ========================================================
    if session.get('username', False):
        if not (
                direct_by_permision(session, permission_sought='administrator')\
                    or direct_by_permision(session, permission_sought='super_user')
            ):  # Brak uprawnień
            return redirect(url_for('index'))
    else:
        # Użytkownik niezalogowany
        return redirect(url_for('index'))
    
    # Pobieranie opinii z bazy danych
    get_opion_db = opion_db()
    
    return render_template(
        "opion_managment.html",
        opinions=get_opion_db
    )


@app.route('/admin/zarzadzanie-filmami', methods=['GET'])
def admin_manage_videos():
    # Sprawdzanie uprawnień
    # ========================================================
    # 🌟 Model implementacji uprawnień - Rekomendacja 🌟
    # Ten kod jest czytelny, modułowy i łatwy w rozbudowie.
    # Każdy poziom uprawnień ma jasno określoną logikę.
    # Użycie funkcji `direct_by_permision` zapewnia elastyczność.
    # Idealne do zastosowania w wielu endpointach systemu!
    # ========================================================
    if session.get('username', False):
        if not (direct_by_permision(session, permission_sought='administrator')
                or direct_by_permision(session, permission_sought='super_user')):
            return redirect(url_for('index'))
    else:
        return redirect(url_for('index'))
    
    return render_template('youtube_managment.html', videos=get_videos())




@app.route('/api/add-video', methods=['POST'])
def add_video():
    if session.get('username', False):
        if not direct_by_permision(session, permission_sought='administrator') and not direct_by_permision(session, permission_sought='super_user'):
            return jsonify({"success": False, "message": "Brak wymaganych uprawnień!"}), 403
    else:
        return jsonify({"success": False, "message": "Brak wymaganych uprawnień!"}), 403

    data = request.json
    iframe_code = data.get("iframeCode")

    # print("Odebrany iframe:", iframe_code)  # 🔍 Debug w konsoli serwera

    if not iframe_code:
        return jsonify({"success": False, "message": "Brak kodu iframe!"}), 400

    # Wyciągamy `src` z iframe
    video_url = extract_src_from_iframe(iframe_code)

    if not video_url:
        return jsonify({"success": False, "message": "Nie udało się wyodrębnić linku z iframe!"}), 400

    try:
        # Sprawdzamy, czy film już istnieje w bazie
        query_check = "SELECT COUNT(*) FROM videos WHERE video_url = %s"
        result = msq.safe_connect_to_database(query_check, (video_url,))

        print("Wynik SELECT:", result)  # 🔍 Debug w konsoli serwera

        if result and int(result[0][0]) > 0:  # **Zapewniamy konwersję na int**
            print("❌ Film już istnieje, blokujemy dodanie!")  # **Nowy debug**
            return jsonify({"success": False, "message": "Film już istnieje w bazie!"}), 409

        # Jeśli link nie istnieje, dodajemy go do bazy
        query_insert = "INSERT INTO videos (video_url) VALUES (%s)"
        msq.insert_to_database(query_insert, (video_url,))

        return jsonify({"success": True, "message": "Film dodany pomyślnie!"})
    except Exception as e:
        return jsonify({"success": False, "message": f"Błąd bazy danych: {str(e)}"}), 500



@app.route('/api/delete-video', methods=['DELETE'])
def delete_video():
    # Sprawdzanie uprawnień
    if session.get('username', False):
        if not (direct_by_permision(session, permission_sought='administrator')
                or direct_by_permision(session, permission_sought='super_user')):
            return jsonify({"success": False, "message": "Brak wymaganych uprawnień!"}), 403
    else:
        return jsonify({"success": False, "message": "Brak wymaganych uprawnień!"}), 403

    data = request.json
    video_url = data.get("videoUrl")  # Oczekujemy `videoUrl`, nie `id`

    if not video_url:
        return jsonify({"success": False, "message": "Brak URL filmu!"}), 400

    try:
        query = "DELETE FROM videos WHERE video_url = %s"
        msq.safe_connect_to_database(query, (video_url,))
        return jsonify({"success": True, "message": "Film usunięty!"})
    except Exception as e:
        return jsonify({"success": False, "message": f"Błąd bazy danych: {str(e)}"}), 500


@app.route('/api/set-active-video', methods=['POST'])
def set_active_video():
    if session.get('username', False):
        if not (direct_by_permision(session, permission_sought='administrator')
                or direct_by_permision(session, permission_sought='super_user')):
            return jsonify({"success": False, "message": "Brak wymaganych uprawnień!"}), 403
    else:
        return jsonify({"success": False, "message": "Brak wymaganych uprawnień!"}), 403

    data = request.json
    video_id = data.get("videoId")
    color = data.get("color")

    print(f"🔍 Otrzymano żądanie: videoId={video_id}, color={color}")

    if not video_id or not color:
        print("⚠️ Błąd: Brak wymaganych danych!")
        return jsonify({"success": False, "message": "Brak wymaganych danych!"}), 400

    try:
        # **1️⃣ Usuwamy wcześniejsze przypisanie dla tego koloru**
        query_reset = "DELETE FROM video_eye_colors WHERE color = %s"
        result_reset = msq.safe_connect_to_database(query_reset, (color,))
        print(f"🗑 Usunięto stare przypisanie dla koloru {color}. Wynik: {result_reset}")

        # **2️⃣ Przypisujemy nowy film do koloru**
        query_insert = "INSERT INTO video_eye_colors (video_id, color) VALUES (%s, %s)"
        result_insert = msq.safe_connect_to_database(query_insert, (video_id, color))
        print(f"✅ Przypisano film {video_id} do {color}. Wynik: {result_insert}")

        return jsonify({"success": True, "message": "Aktywny film został zmieniony!"})

    except Exception as e:
        print(f"❌ Błąd bazy danych: {e}")
        return jsonify({"success": False, "message": f"Błąd bazy danych: {e}"}), 500
















# ========================================================================================= #
#  ENDPOINTY API
#  
#  Programowalne punkty dostępu:
#  - JSON REST API dla aplikacji mobilnych i zewnętrznych integracji.
#  - Autoryzacja tokenowa i OAuth.
#  - Struktura odpowiedzi zgodna z najlepszymi praktykami.
#  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -  
#  Umożliwiają komunikację z aplikacją z poziomu innych systemów.
# ========================================================================================= #

# API do obsługi formularza i danych JSON
@app.route('/api/kontakt', methods=['POST'])
def contact_api():
    if request.is_json:
        # Obsługa danych JSON
        data = request.get_json()
        name = data.get('name')
        email = data.get('email')
        subject = data.get('subject')
        message = data.get('message')
        consent = data.get('consent')

        if not consent:
            return jsonify({
                "status": "error",
                "message": "Musisz wyrazić zgodę na przetwarzanie danych osobowych."
            }), 400

        # Zapytanie SQL
        query = """
            INSERT INTO contact_messages (name, email, subject, message, consent)
            VALUES (%s, %s, %s, %s, %s);
        """
        params = (name, email, subject, message, consent)

        # Wstawienie danych do bazy
        try:
            if msq.insert_to_database(query, params): # Przykładowa funkcja w Twoim module bazy danych
                if firstConntactMessage(email, "general_inquiry"):
                    # Wywołaj funkcję wysyłania e-maila HTML
                    subject = f"Nowa wiadomość ze strony kontaktowej od - {name}"
                    html_body = f"""
                        <html>
                            <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
                                <h1 style="color: #24363f;">Nowa wiadomość ze strony kontaktowej</h1>
                                <p>
                                    Otrzymaliśmy nową wiadomość ze strony kontaktowej Duodent Bielany. Poniżej znajdują się szczegóły zgłoszenia:
                                </p>
                                <table style="border-collapse: collapse; width: 100%; margin-top: 20px;">
                                    <tr style="background-color: #f9f9f9;">
                                        <th style="border: 1px solid #ccc; padding: 10px; text-align: left;">Opis</th>
                                        <th style="border: 1px solid #ccc; padding: 10px; text-align: left;">Dane</th>
                                    </tr>
                                    <tr>
                                        <td style="border: 1px solid #ccc; padding: 10px;">Imię i nazwisko</td>
                                        <td style="border: 1px solid #ccc; padding: 10px;">{name}</td>
                                    </tr>
                                    <tr style="background-color: #f9f9f9;">
                                        <td style="border: 1px solid #ccc; padding: 10px;">Adres e-mail</td>
                                        <td style="border: 1px solid #ccc; padding: 10px;">{email}</td>
                                    </tr>
                                    <tr>
                                        <td style="border: 1px solid #ccc; padding: 10px;">Temat wiadomości</td>
                                        <td style="border: 1px solid #ccc; padding: 10px;">{subject}</td>
                                    </tr>
                                    <tr style="background-color: #f9f9f9;">
                                        <td style="border: 1px solid #ccc; padding: 10px;">Treść wiadomości</td>
                                        <td style="border: 1px solid #ccc; padding: 10px;">{message}</td>
                                    </tr>
                                </table>
                                <p style="margin-top: 20px;">
                                    Prosimy o jak najszybsze zapoznanie się z wiadomością i kontakt z nadawcą, jeśli wymaga tego sytuacja.
                                </p>
                                <p>
                                    Odpowiedź można wysłać bezpośrednio na adres e-mail nadawcy: 
                                    <a href="mailto:{email}" style="color: #24363f;">{email}</a>.
                                </p>
                                <p style="font-size: 12px; color: #686d71; margin-top: 30px; border-top: 1px solid #ccc; padding-top: 10px;">
                                    Wiadomość wygenerowana automatycznie przez system kontaktowy Duodent.
                                </p>
                            </body>
                        </html>
                    """
                    email_address = msq.connect_to_database(f'SELECT config_smtp_username FROM system_setting;')[0][0]
                    try:
                        send_html_email(subject, html_body, email_address)
                        print(f"Powiadomienie wysłane do {email_address} dla procedury general_inquiry.")
                        return jsonify({
                            "status": "success",
                            "message": "Dziękujemy za kontakt!",
                            "data": {
                                "name": name,
                                "email": email,
                                "subject": subject,
                                "message": message
                            }
                        }), 200
                    except Exception as e:
                        print(f"Błąd wysyłania powiadomienia: {e}")
                        return jsonify({"status": "error", "message": "Błąd podczas rejestracji"}), 400
                    
                else:
                    return jsonify({"status": "error", "message": "Błąd podczas rejestracji"}), 400
                    
            else:
                return jsonify({
                    "status": "error",
                    "message": "Ups, coś poszło nie tak 😞"
                }), 500
        except Exception as e:
            return jsonify({
                "status": "error",
                "message": f"Błąd serwera: {str(e)}"
            }), 500
    else:
        # Obsługa formularza HTML
        return jsonify({
            "status": "error",
            "message": "Nieprawidłowy format danych."
        }), 400


@app.route('/api/umow-wizyte', methods=['POST'])
def book_appointment_api():
    if request.is_json:
        data = request.get_json()
        name = data.get('name')
        email = data.get('email')
        phone = data.get('phone')
        patient_type = data.get('patient_type')
        visit_date = data.get('visit_date')
        consent = data.get('consent')

        if not consent:
            return jsonify({"status": "error", "message": "Musisz wyrazić zgodę na przetwarzanie danych osobowych."}), 400

        # Walidacja danych
        if not consent:
            return jsonify({"status": "error", "message": "Musisz wyrazić zgodę na przetwarzanie danych osobowych."}), 400

        if not name or not email or not phone or not patient_type or not visit_date:
            return jsonify({"status": "error", "message": "Wszystkie pola są wymagane."}), 400

        if not is_valid_email(email):
            return jsonify({"status": "error", "message": "Nieprawidłowy adres email."}), 400

        # Generowanie unikalnego linku
        generated_hash = generate_hash()

        # Zapytanie SQL
        query = """
            INSERT INTO appointment_requests (name, email, phone, patient_type, visit_date, consent, status, link_hash)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
        """
        params = (name, email, phone, patient_type, visit_date, consent, "in_progress", generated_hash)

        try:
            if msq.insert_to_database(query, params):
                if firstConntactMessage(email, "appointment"):
                    # Wywołaj funkcję wysyłania e-maila HTML
                    subject = f"Nowy wniosek o rejestrację wizyty - {name}"
                    html_body = f"""
                        <html>
                            <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
                                <h1 style="color: #24363f;">Nowy wniosek o rejestrację wizyty</h1>
                                <p>
                                    Otrzymaliśmy nowy wniosek o rejestrację wizyty w placówce Duodent Bielany. Szczegóły zgłoszenia znajdują się poniżej:
                                </p>
                                <table style="border-collapse: collapse; width: 100%; margin-top: 20px;">
                                    <tr style="background-color: #f9f9f9;">
                                        <th style="border: 1px solid #ccc; padding: 10px; text-align: left;">Opis</th>
                                        <th style="border: 1px solid #ccc; padding: 10px; text-align: left;">Dane</th>
                                    </tr>
                                    <tr>
                                        <td style="border: 1px solid #ccc; padding: 10px;">Imię i nazwisko</td>
                                        <td style="border: 1px solid #ccc; padding: 10px;">{name}</td>
                                    </tr>
                                    <tr style="background-color: #f9f9f9;">
                                        <td style="border: 1px solid #ccc; padding: 10px;">Adres e-mail</td>
                                        <td style="border: 1px solid #ccc; padding: 10px;">{email}</td>
                                    </tr>
                                    <tr>
                                        <td style="border: 1px solid #ccc; padding: 10px;">Numer telefonu</td>
                                        <td style="border: 1px solid #ccc; padding: 10px;">{phone}</td>
                                    </tr>
                                    <tr style="background-color: #f9f9f9;">
                                        <td style="border: 1px solid #ccc; padding: 10px;">Data wizyty</td>
                                        <td style="border: 1px solid #ccc; padding: 10px;">{visit_date}</td>
                                    </tr>
                                    <tr>
                                        <td style="border: 1px solid #ccc; padding: 10px;">Typ pacjenta</td>
                                        <td style="border: 1px solid #ccc; padding: 10px;">{patient_type}</td>
                                    </tr>
                                </table>
                                <p style="margin-top: 20px;">
                                    Prosimy o jak najszybsze skontaktowanie się z pacjentem w celu ustalenia szczegółów wizyty i jej potwierdzenia.
                                </p>
                                <p style="font-size: 12px; color: #686d71; margin-top: 30px; border-top: 1px solid #ccc; padding-top: 10px;">
                                    Wiadomość wygenerowana automatycznie przez system rejestracji Duodent.
                                </p>
                            </body>
                        </html>
                    """
                    email_address = msq.connect_to_database(f'SELECT config_smtp_username FROM system_setting;')[0][0]
                    try:
                        send_html_email(subject, html_body, email_address)
                        print(f"Powiadomienie wysłane do {email_address} dla procedury appointment.")
                        return jsonify({"status": "success", "message": "Rezerwacja przyjęta! Skontaktujemy się w celu ustalenia szczegółów."}), 200
                    except Exception as e:
                        print(f"Błąd wysyłania powiadomienia: {e}")
                        return jsonify({"status": "error", "message": "Błąd podczas rejestracji"}), 400
                    
                else:
                    return jsonify({"status": "error", "message": "Błąd podczas rejestracji"}), 400
            else:
                return jsonify({"status": "error", "message": "Ups, coś poszło nie tak. Spróbuj ponownie."}), 500
        except Exception as e:
            return jsonify({"status": "error", "message": f"Błąd serwera: {str(e)}"}), 500
    else:
        return jsonify({"status": "error", "message": "Nieprawidłowy format danych."}), 400

@app.route('/api/get-role', methods=['GET'])
def get_role_api():
    try:
        if session:
            user_role = get_user_role(session)
            return jsonify({"role": user_role})
        else:
            return jsonify({"role": 'user_alert'}), 401  # Brak autoryzacji
    except Exception as e:
        return jsonify({"error": str(e)}), 500  # Błąd serwera


@app.route('/api/search-treatment', methods=['POST'])
def search_treatment():
    try:
        # Pobranie danych z żądania
        data = request.get_json()

        # Walidacja danych wejściowych
        if not data or 'query' not in data:
            return jsonify({"error": "Brak zapytania w żądaniu"}), 400

        query = data['query'].strip().lower()
        if not query:
            return jsonify({"error": "Zapytanie nie może być puste"}), 400

        # Pobranie danych do przeszukania
        treatments_data = treatments_db_all_by_route_dict(False)
        if not treatments_data:
            return jsonify({"error": "Baza danych jest pusta"}), 500

        # Analiza wyników
        stats = {}
        for route, details in treatments_data.items():
            stats[route] = 0
            for value in details.values():
                if isinstance(value, str):
                    for word in query.split():
                        if word in value.lower():
                            stats[route] += 1

        # Wybór najlepszego wyniku
        best_match = max(stats, key=stats.get)
        best_score = stats[best_match]
        best_match_exp = f"/zabieg-stomatologiczny/{best_match}"

        from pprint import pprint
        pprint(stats)

        # Jeśli brak trafień, zwróć domyślny route
        if best_score == 0:
            return jsonify("/zabiegi-stomatologiczne-kompleksowa-oferta"), 200

        return jsonify(best_match_exp), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/add-opinion', methods=['POST'])
def add_opinion():
    """
    Endpoint do dodawania opinii.
    """

    # Pobieranie danych z żądania
    data = request.get_json()
    
    # Walidacja danych
    opinion = data.get('content')
    author = data.get('author')
    avatar = data.get('avatar') # Avatar może być pusty
    role = data.get('role')

    if not role: role='Użytkownik'
    if not avatar: avatar=None

    # Walidacja pól wymaganych
    if not opinion or not author:
        return jsonify({'success': False, 'message': 'Pola "content" i "author" są wymagane.'}), 400

    # Zapisywanie do bazy danych
    sql_query = """
            INSERT INTO opinions (opinion, author, avatar, role)
            VALUES (%s, %s, %s, %s)
        """
    params = (opinion, author, avatar, role)
    if msq.insert_to_database(sql_query, params):
        return jsonify({'success': True, 'message': 'Opinia została pomyślnie dodana.'}), 201
    else:
        return jsonify({'success': False, 'message': 'Wystąpił błąd podczas dodawania opinii.'}), 500

@app.route('/admin/usun-opinie', methods=['DELETE'])
def delete_opinion():
    data = request.get_json()
    opinion_id = data.get('id')

    if not opinion_id:
        return jsonify({"status": "error", "message": "Nie podano ID opinii"}), 400

    query = "DELETE FROM opinions WHERE id = %s;"
    if msq.insert_to_database(query, (opinion_id,)):
        return jsonify({"status": "success", "message": "Opinia została usunięta"})
    else:
        print(f'Błąd podczas usuwania opinii!')
        return jsonify({"status": "error", "message": "Nie udało się usunąć opinii"}), 500













# ========================================================================================= #
#  ENDPOINTY OPERACYJNE
#  
#  Punkty dostępu związane z operacjami na danych:
#  - Przetwarzanie danych w tle.
#  - Obsługa masowych importów i eksportów.
#  - Interakcja z systemami zewnętrznymi.
#  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -  
#  Kluczowe dla integracji i optymalizacji procesów biznesowych.
# ========================================================================================= #
@app.route('/admin/get-picker-options', methods=['GET'])
def get_picker_options():
    # Pobierz ID elementu z parametrów zapytania
    element_id = request.args.get('id')

    try:
        page_attached_worker_sql = f'WHERE status_usera = 1 AND user = 1'
        page_attached_worker = msq.connect_to_database(f'SELECT id, name FROM admins {page_attached_worker_sql};')

        page_treatments_id_sql = f'WHERE treatment_general_status = 1'
        page_treatments_id = msq.connect_to_database(f'SELECT id FROM tabela_uslug {page_treatments_id_sql};')

        page_attached_files_sql = f'WHERE status_aktywnosci = 1'
        page_attached_files = msq.connect_to_database(f'SELECT id, name FROM files {page_attached_files_sql};')
    except Exception as e:
        print(f"Błąd połączenia z bazą danych: {e}")
        return jsonify({"error": f"Błąd połączenia z bazą danych: {e}"}), 404
    
    OPTIONS_DATA = {}
    getTreatments_db_all_by_id_dict = {val['id']: val['page_attached_list_files'] for val in treatments_db_all_by_route_dict().values()}

    for treatments_id in page_treatments_id:
        OPTIONS_DATA[f"treatment-page_attached_worker_id-{treatments_id[0]}-1-1"] = [
            {"id": ident, "description": name} for ident, name in page_attached_worker
        ]

        OPTIONS_DATA[f"treatment-page_attached_add_files-{treatments_id[0]}-1-1"] = []
        for ident, name in page_attached_files:
            if treatments_id[0] in getTreatments_db_all_by_id_dict:
                if ident not in getTreatments_db_all_by_id_dict[treatments_id[0]]:
                    ready_record = {"id": ident, "description": name}
                    OPTIONS_DATA[f"treatment-page_attached_add_files-{treatments_id[0]}-1-1"].append(ready_record)

        OPTIONS_DATA[f"treatment-icon-{treatments_id[0]}-1-1"] = [
            {"id": ident, "description": name} for ident, name in iconer_changer_by_id.items()
        ]


    # print(OPTIONS_DATA)
    # Dane do wysłania
    {
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

    # Sprawdź, czy istnieją dane dla danego ID
    if element_id in OPTIONS_DATA:
        return jsonify({"options": OPTIONS_DATA[element_id]})
    else:
        return jsonify({"error": "Opcje nie znalezione"}), 404


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

@app.route('/admin/kolejnosc-opini', methods=['POST'])
def update_opinion_order():
    """Aktualizacja kolejności opini."""
    data = request.get_json()
    new_order = data.get('order')  # Lista z ID kategorii w nowej kolejności
    # print(data, new_order)
    if not new_order or not isinstance(new_order, list):
        return jsonify({"status": "error", "message": "Nieprawidłowe dane"}), 400

    # Aktualizacja kolejności w bazie
    for index, category_id in enumerate(new_order):
        query = "UPDATE opinions SET sort_order = %s WHERE id = %s;"
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


@app.route('/admin/edytuj-wybrany-element', methods=['POST'])
def edit_element():
    # Obsługa JSON
    if request.is_json:
        data = request.json
        element_id = data.get('id')
        data_type = data.get('type')
        value = data.get('value')
    else:
        if 'file' not in request.files:
            return jsonify({'error': 'Błąd podczas aktualizacji'}), 500
        
        file = request.files['file']
        element_id = request.form.get('id')
        data_type = request.form.get('type')
        value = None

        if not file or not element_id or data_type != 'img':
            return jsonify({'error': 'Nieprawidłowe dane'}), 400
        
        if file and not allowed_img_file(file.filename):
            return jsonify({'error': 'Nieprawidłowy plik obrazu'}), 400

    if not element_id or not data_type:
        return jsonify({'error': 'Brak wymaganych danych'}), 400

    # Obsługa typów danych
    if data_type == 'text':
        # Walidacja i przypisanie ID z selektora
        if not isinstance(value, str):
            return jsonify({'error': 'Nieprawidłowy format dla text'}), 400

    if data_type == 'splx':
        # Zapis jako string z separatorami w bazie
        if not isinstance(value, str):
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

    # Obsługa różnych typów operacji w zależności od data_type
    if data_type == 'switch':
        try:
            value = int(value)  # Próba konwersji value na liczbę całkowitą
        except:
            return jsonify({'error': 'Nieprawidłowy format wymagana liczba int'}), 400
        
        # Walidacja typu value (powinno być int)
        if not isinstance(value, int):
            return jsonify({'error': 'Nieprawidłowy format dla int'}), 400  

    if data_type == 'remover':
        # Walidacja typu element_id (powinien być string)
        if value is not None or not isinstance(element_id, str):
            return jsonify({'error': 'Nieprawidłowy format dla remover'}), 400
        
        TODELETE_INT = [
            'treatment_remove_page'
        ]
        
        # Sprawdzenie, czy element_id zawiera frazę z listy TODELETE_INT
        if any(a in element_id for a in TODELETE_INT):
            # Rozbij element_id na części składowe
            element_id_split_part = editing_id_updater_reader(element_id)
            
            # Walidacja obecności klucza 'status' i jego wartości
            if 'status' in element_id_split_part:
                if not element_id_split_part['status']:
                    return jsonify({'error': 'id error 0'}), 500
            else:
                return jsonify({'error': 'id error 1'}), 500

            # Walidacja obecności wymaganych kluczy w element_id_split_part
            if all(key in element_id_split_part for key in ['strona', 'sekcja', 'id_number', 'index', 'part', 'ofparts']):
                strona = element_id_split_part['strona']
                sekcja = element_id_split_part['sekcja']
                id_number = element_id_split_part['id_number']
                index = element_id_split_part['index']
                part = element_id_split_part['part']
                ofparts = element_id_split_part['ofparts']
            else:
                return jsonify({'error': 'id error 2'}), 500

            # Logika usuwania danych, jeśli strona i sekcja są zgodne
            if strona == 'treatment' and sekcja in TODELETE_INT:
                # Pobierz dane o zdjęciach z bazy
                allPhotoKeys = treatments_foto_db_by_id(id_number)
                if not allPhotoKeys:
                    return jsonify({'error': 'No photo data found'}), 404

                for key, val in allPhotoKeys.items():
                    if val:  # Jeśli wartość istnieje, przetwarzaj dalej
                        file_paths = []

                        # Obsługa różnych formatów danych (pojedynczy plik lub lista)
                        if isinstance(val, str) and spea_main not in val:
                            # Pojedynczy plik
                            file_paths = [val]
                        elif isinstance(val, list):
                            # Lista plików
                            file_paths = val

                        # Ustal katalog docelowy na podstawie klucza z dictitem
                        if key in ['optional_1']:
                            folder = app.config['UPLOAD_FOLDER_BANNERS']
                        else:
                            folder = app.config['UPLOAD_FOLDER_TREATMENTS']

                        # Usuń każdy plik znajdujący się w file_paths
                        for file_name in file_paths:
                            file_path = os.path.join(folder, file_name)
                            if os.path.exists(file_path):
                                try:
                                    os.remove(file_path)
                                    print(f"Usunięto plik: {file_path}")
                                except Exception as e:
                                    print(f"Błąd przy usuwaniu {file_path}: {e}")
                            else:
                                print(f"Plik nie istnieje: {file_path}")

    if data_type == 'img':
        element_id_split_part = editing_id_updater_reader(element_id)
        if 'status' in element_id_split_part:
            if not element_id_split_part['status']:
                return jsonify({'error': 'id error 0'}), 500
        else:
            return jsonify({'error': 'id error 1'}), 500
        
        if all(key in element_id_split_part for key in ['strona', 'sekcja', 'id_number', 'index', 'part', 'ofparts']):
            strona=element_id_split_part['strona']
            sekcja=element_id_split_part['sekcja']
            id_number=element_id_split_part['id_number']
            index=element_id_split_part['index']
            part=element_id_split_part['part']
            ofparts=element_id_split_part['ofparts']
        else:
            return jsonify({'error': 'id error 2'}), 500
        
        # Pobieram ostatni dane obrazu
        thisPhotoData = None
        file_path_to_delete = None
        filename = None
        filepath = None
        ####################################################
        # Aktualizacja pliku w UPLOAD_FOLDER_TREATMENTS
        ####################################################
        if strona == 'treatment':
            allPhotoKeys = treatments_foto_db_by_id(id_number)
            #Usatawiam Katalog zapisu dla treatment
            expected_folders = ['optional_1']
            if sekcja in expected_folders:
                UPLOAD_FOLDER_TREATMENTS_IMG = app.config['UPLOAD_FOLDER_BANNERS']
            else:
                UPLOAD_FOLDER_TREATMENTS_IMG = app.config['UPLOAD_FOLDER_TREATMENTS']
            if str(sekcja).count('splx'):
                key_sekcja = str(sekcja).replace('splx', 'list')
                thisPhotoData_list = allPhotoKeys[key_sekcja]
                thisPhotoData = thisPhotoData_list[index]
            else:
                thisPhotoData = allPhotoKeys[sekcja]

        if strona == 'team':

            try:
                ava_query = f'SELECT {sekcja} FROM admins WHERE id={id_number};'
                old_fotoNameofAvatar = msq.connect_to_database(ava_query)[0][0]
            except IndexError:
                old_fotoNameofAvatar = None

            if isinstance(old_fotoNameofAvatar, str):
                if old_fotoNameofAvatar.count('/'):
                    old_fotoNameofAvatar_oryginal = old_fotoNameofAvatar
                    old_fotoNameofAvatar = old_fotoNameofAvatar.split('/')[-1]
                    thisPhotoData = None if old_fotoNameofAvatar == 'with-out-face-avatar.jpg' else old_fotoNameofAvatar
                else:
                    thisPhotoData = None
            
            expected_folders = []
            if sekcja in expected_folders:
                "Opcja otworzona w celu skalowania aplikacji! w przypadku innych katalogów"
                pass
            else:
                UPLOAD_FOLDER_TREATMENTS_IMG = app.config['UPLOAD_FOLDER_AVATARS']

        
        if thisPhotoData:
            file_path_to_delete = os.path.join(UPLOAD_FOLDER_TREATMENTS_IMG, thisPhotoData) 

        if file:
            filename = f"{random.randrange(100001, 799999)}_{secure_filename(file.filename)}"
            filepath = os.path.join(UPLOAD_FOLDER_TREATMENTS_IMG, filename)
        
        # jeżli był obraz to kasujemy z serwera
        if thisPhotoData and file_path_to_delete:
            print(thisPhotoData)
            
            # Sprawdzenie, czy plik istnieje, i usunięcie go
            if os.path.exists(file_path_to_delete):
                try:
                    os.remove(file_path_to_delete)
                    print(f"Usunięto plik: {file_path_to_delete}")
                except Exception as e:
                    print(f"Błąd podczas usuwania pliku: {file_path_to_delete}, {e}")

        # Zapis nowego pliku
        if filename and filepath:
            if strona == 'treatment':
                try:                
                    # Zapis pliku
                    file.save(filepath)
                    value = filename
                    print(f"Zapisano plik: {filepath}")
                except Exception as e:
                    return jsonify({'error': f'Błąd zapisu pliku: {str(e)}'}), 500
                
            if strona == 'team':
                domena_strony_www = 'https://www.duodentbielany.pl/'
                katalog_zdjecia = 'static/img/doctor/'
                photo_link = f'{domena_strony_www}{katalog_zdjecia}{filename}'

                # Zapisz zdjęcie
                try:
                    if process_photo(file, filepath):
                        # podmieniam zdjęcie w workers_team
                        print(old_fotoNameofAvatar_oryginal)
                        if old_fotoNameofAvatar_oryginal and isinstance(old_fotoNameofAvatar_oryginal, str):
                            try: 
                                query_sel_workers_team = f"""
                                    SELECT id FROM workers_team WHERE EMPLOYEE_PHOTO='{old_fotoNameofAvatar_oryginal}';
                                """
                                id_in_workers_team = msq.connect_to_database(query_sel_workers_team)[0][0]
                            except IndexError: id_in_workers_team = None
                            if id_in_workers_team:
                                query_upd_workers_team = """
                                    UPDATE workers_team
                                    SET EMPLOYEE_PHOTO = %s
                                    WHERE id = %s
                                """
                                params_upd_workers_team = (photo_link, id_in_workers_team)
                                if not msq.insert_to_database(query_upd_workers_team, params_upd_workers_team):
                                    print('Nie znaleziono zdjęcia do podmiany w workers_team')
                                else:
                                    print('Zdjęcie zostało podmienione w workers_team!')

                    else: return jsonify({"errors": ["Nie udało się zapisać przesłanego pliku."]}), 500
                except Exception as e:
                    return jsonify({"errors": ["Nie udało się zapisać przesłanego pliku."]}), 500

                value = photo_link

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


@app.route("/admin/confirm_visit", methods=["POST"])
def confirm_visit():
    """ Zatwierdza wizytę w bazie (daemon ją wykryje i doda przypomnienia) """
    
    data = request.json
    visit_id = data.get("visit_id")
    confirmed_date = data.get("confirmed_date")
    confirmed_time = data.get("confirmed_time")

    if not all([visit_id, confirmed_date, confirmed_time]):
        return jsonify({"status": "error", "message": "Brak wymaganych danych"}), 400

    full_datetime = f"{confirmed_date} {confirmed_time}:00"
    
    print(f"🔄 Aktualizuję wizytę ID {visit_id} na status 'confirmed', data: {full_datetime}")

    # 🔹 Aktualizacja wizyty w bazie
    update_query = "UPDATE appointment_requests SET status = %s, confirmed_date = %s, confirmed_flag = 0 WHERE id = %s"
    success = msq.insert_to_database(update_query, ("confirmed", full_datetime, visit_id))

    if success:
        print(f"✅ Wizyta {visit_id} została pomyślnie zatwierdzona w bazie.")
        return jsonify({"status": "success", "message": "Wizyta zatwierdzona! Demon zajmie się przypomnieniami."})
    else:
        print(f"❌ Błąd podczas zatwierdzania wizyty {visit_id}.")
        return jsonify({"status": "error", "message": "Nie udało się zatwierdzić wizyty."}), 500


@app.route("/admin/cancel_visit", methods=["POST"])
def cancel_visit():
    """ Anuluje wizytę w bazie danych """
    try:
        data = request.json
        visit_id = data.get("visit_id")
        cancel_note = data.get("cancel_note")

        if not visit_id or not cancel_note:
            return jsonify({"status": "error", "message": "Brak wymaganych danych"}), 400

        print(f"🚫 Anulowanie wizyty ID {visit_id} z powodem: {cancel_note}")

        # 🔹 Aktualizacja bazy danych
        success = msq.insert_to_database(
            "UPDATE appointment_requests SET status = 'cancelled', cancelled_description = %s, cancelled_flag = 0 WHERE id = %s",
            (cancel_note, visit_id)
        )

        if success:
            print(f"✅ Wizyta {visit_id} została anulowana.")
            return jsonify({"status": "success", "message": "Wizyta została anulowana."})
        else:
            print(f"❌ Błąd podczas anulowania wizyty {visit_id}.")
            return jsonify({"status": "error", "message": "Nie udało się anulować wizyty."}), 500

    except Exception as e:
        print(f"❌ Błąd w /admin/cancel_visit: {str(e)}")
        return jsonify({"status": "error", "message": f"Błąd serwera: {str(e)}"}), 500



@app.route("/admin/reschedule_visit", methods=["POST"])
def reschedule_visit():
    """ Przekłada wizytę na nowy termin """
    try:
        data = request.json
        visit_id = data.get("visit_id")
        new_date = data.get("new_date")
        new_time = data.get("new_time")

        if not visit_id or not new_date or not new_time:
            return jsonify({"status": "error", "message": "Brak wymaganych danych"}), 400

        new_datetime = f"{new_date} {new_time}:00"
        logging.info(f"📅 Przekładanie wizyty ID {visit_id} na {new_datetime}")

        # 🔹 Pobranie oryginalnej wizyty
        original_visit = msq.safe_connect_to_database(
            "SELECT name, email, phone, patient_type, consent, link_hash FROM appointment_requests WHERE id = %s", (visit_id,)
        )

        if not original_visit:
            logging.error(f"❌ Nie znaleziono wizyty ID {visit_id}.")
            return jsonify({"status": "error", "message": "Nie znaleziono wizyty w bazie."}), 404

        original_visit = original_visit[0]  # Pobieramy pierwszy rekord

        logging.info(f"🔎 Znaleziono wizytę ID {visit_id}: {original_visit}")

        # 🔹 Sprawdzenie poprawności danych
        valid_patient_types = ["adult", "child", "senior"]  # Dostosuj do bazy
        if original_visit[3] not in valid_patient_types:
            logging.error(f"❌ Niepoprawny `patient_type`: {original_visit[3]}")
            return jsonify({"status": "error", "message": "Niepoprawny typ pacjenta."}), 400

        consent_value = original_visit[4] if original_visit[4] is not None else 1  # Domyślnie 1

        # 🔹 Przenosimy wizytę na nowy termin (kopiujemy dane)
        copy_success = msq.insert_to_database(
            """
            INSERT INTO appointment_requests 
            (name, email, phone, patient_type, visit_date, consent, status, confirmed_date, link_hash) 
            VALUES (%s, %s, %s, %s, %s, %s, 'confirmed', %s, %s)
            """,
            (
                original_visit[0],  # name
                original_visit[1],  # email
                original_visit[2],  # phone
                original_visit[3],  # patient_type
                new_date,
                consent_value,
                new_datetime,
                generate_hash(),  # link_hash
            )
        )

        if not copy_success:
            logging.error(f"❌ Błąd przy kopiowaniu wizyty ID {visit_id}.")
            return jsonify({"status": "error", "message": "Nie udało się utworzyć nowej wizyty."}), 500

        # 🔹 Oznaczamy starą wizytę jako anulowaną
        cancel_note = data.get("cancel_note")
        if cancel_note is None:
            cancel_note = "Wizyta przełożona"
        cancel_note = str(cancel_note).strip()

        cancel_success = msq.insert_to_database(
            "UPDATE appointment_requests SET status = 'cancelled', cancelled_description = %s, cancelled_flag = 0 WHERE id = %s",
            (cancel_note, visit_id)
        )

        if cancel_success:
            logging.info(f"✅ Wizyta ID {visit_id} przełożona na {new_datetime}.")
            return jsonify({"status": "success", "message": "Wizyta została przełożona."})
        else:
            logging.error(f"❌ Błąd przy anulowaniu starej wizyty ID {visit_id}.")
            return jsonify({"status": "error", "message": "Nowa wizyta została utworzona, ale nie udało się anulować starej."}), 500

    except Exception as e:
        logging.error(f"❌ Błąd w /admin/reschedule_visit: {str(e)}")
        return jsonify({"status": "error", "message": f"Błąd serwera: {str(e)}"}), 500












# ========================================================================================= #
#  ENDPOINTY STATYCZNE
#  
#  Obsługa plików statycznych:
#  - Grafiki, arkusze CSS, skrypty JavaScript.
#  - Serwowanie treści niezmiennych przez aplikację.
#  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -  
#  Dostosowane do wymagań wydajnościowych (cache i kompresja).
# ========================================================================================= #


# Strona główna
@app.route('/')
def index():
    session['page'] = 'index'
    pageTitle = 'Strona Główna'

    generator_teamDB_v = generator_teamDB()
    if len(generator_teamDB_v) > 2:
        generator_teamDB_v = generator_teamDB_v[:3]

    get_opinion = opion_db()

    return render_template(
        'index.html',
        pageTitle=pageTitle,
        members=generator_teamDB_v,
        opinions=get_opinion
    )

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

# Zabiegi - lista
@app.route('/zabiegi-stomatologiczne-kompleksowa-oferta')
def treatments():
    session['page'] = 'treatments'
    pageTitle = 'Zabiegi'

    treatments_items = treatments_db(True)

    return render_template(
        'treatments.html',
        pageTitle=pageTitle,
        treatments_items=treatments_items
    )



# Poznaj nas bliżej
@app.route('/o-nas-twoja-przychodnia-stomatologiczna')
def about_us():
    session['page'] = 'about_us'
    pageTitle = 'Poznaj nas bliżej'

    generator_teamDB_v = generator_teamDB()
    if len(generator_teamDB_v) > 2:
        generator_teamDB_v = generator_teamDB_v[:3]

    return render_template(
        'about_us.html',
        pageTitle=pageTitle,
        members=generator_teamDB_v
    )


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


# konkurs walentynkowy
@app.route('/regulamin-konkursu-walentynkowego')
def contest_valentain_rules():
    session['page'] = 'contest_valentain_rules'
    pageTitle = 'Zasady konkursu walentynkowego'
    return render_template(
        'valentine_rules.html',
        pageTitle=pageTitle
    )

from collections import defaultdict
def parse_instagram_comments(raw_text):
    comments_dict = defaultdict(tuple)

    if isinstance(raw_text, str):
        lines = raw_text.split()
    else:
        return {}
    
    author = None

    for line in lines:
        line = line.strip()
        
        # Sprawdzamy, czy linia wygląda jak nazwa użytkownika (autor komentarza)
        if re.match(r'^[a-zA-Z0-9._]+$', line):
            author = line
        elif author and line.startswith('@'):
            # Pobieramy oznaczone osoby
            mentions = tuple(re.findall(r'@[\w.]+', line))
            if mentions:
                comments_dict[author] = mentions
    
    return dict(comments_dict)

def parse_facebook_comments(text):
    comments = defaultdict(tuple)
    
    # Rozdzielamy tekst na wpisy na podstawie typowego układu nazwiska + treść
    entries = re.split(r'\n(?=[A-ZŻŹĆĄŚĘŁÓŃ][a-zżźćńółęąś]+\s[A-ZŻŹĆĄŚĘŁÓŃ][a-zżźćńółęąś]+)', text)

    for entry in entries:
        lines = entry.strip().split("\n")
        
        if len(lines) < 2:
            continue  # Pomijamy puste lub niewłaściwe wpisy
        
        author = lines[0].strip()  # Pierwsza linia to autor
        content = " ".join(lines[1:])  # Reszta to treść komentarza

        # Wyszukiwanie oznaczonych osób (imiona i nazwiska, oddzielone spacjami)
        tagged_people = re.findall(r'\b[A-ZŻŹĆĄŚĘŁÓŃ][a-zżźćńółęąś]+(?:\s[A-ZŻŹĆĄŚĘŁÓŃ][a-zżźćńółęąś]+)+\b', content)

        comments[author] = tuple(tagged_people)

    return dict(comments)



komentarze_instagram = """x_xkamil_x_x
@_magda_koziel @mil3nk44_ @ellaa_babuttt
4 d
4 polubień
Odpowiedz
mozdzonek.m
@prasula.m @aniachodniewicz @dominik_chodniewicz
4 d
3 polubień
Odpowiedz
a_u_r_e_ola
@brzozosko @kamila.andrk @wadolkowskabeata
4 d
2 polubień
Odpowiedz
a_u_r_e_ola
@elarosik @yana.vyv @slonecznapatka_art
4 d
2 polubień
Odpowiedz
anulaaa_s
@soffiia94 @karolina_strachota @madallenne‼️❤️🥰
4 d
5 polubień
Odpowiedz
fylyp121
@tomaszewskaad @mater_domini @wiczka63
4 d
4 polubień
Odpowiedz
tomaszewskaad
@tomaszewsk_aa @ela.t0m @w.iikaa 🔥
4 d
4 polubień
Odpowiedz
mo.nika_legeza
@szabatmariola @myszaka @marcela_legeza
4 d
2 polubień
Odpowiedz
jedzurakinga
@jvllym @o.l.q.a.k @klaudiaa.km
4 d
2 polubień
Odpowiedz
wika_1210
@kewinsobon @blaszkiewicz.anna @kasiasobon 🦷🦷
4 d
3 polubień
Odpowiedz
harelikava_tatsiana
@mskireeva @skachkova_tanja @irunia.bogomozejko
4 d
4 polubień
Odpowiedz
jedzurakinga
@sylwia_zj @dominika.bres @dori_s96
4 d
1 polubienie
Odpowiedz
sylwia_zj
@zygmuntmagdalena @jedzurakinga @iska_xd
4 d
2 polubień
Odpowiedz
salaterka223
@olalegeza @marcela_legeza @black_sapphire530i
4 d
1 polubienie
Odpowiedz
sakowska
@maciek3083 @sakovska.m @joanna_melzacka 🫶🏻
4 d
3 polubień
Odpowiedz
adamowskangelika
@lubcio_96 @oliiwk_aaa @adamowska.edytaa 🔥
4 d
1 polubienie
Odpowiedz
juljakartuszynska
@__f_a_u_s_t__ @julia.cyrzan @xlittlewhitelie
4 d
2 polubień
Odpowiedz
angelinasamus
@mateusz_dybiec @anzelikamelnik @julka.julita.b
3 d
1 polubienie
Odpowiedz
juliett_michalowska
@szy_bar @adriana_michalowska @adammichalowski
3 d
3 polubień
Odpowiedz
julka.julita.b
@daria.l @monikakobla @ewelina8820
3 d
2 polubień
Odpowiedz
m.chmielnicki
@sakovska.m @sakowska @maciek3083
3 d
1 polubienie
Odpowiedz
frelinii
@claudia_alicjaa @jezkatarzyna @marlenkamc 🫶🏼
3 d
2 polubień
Odpowiedz
adriana_michalowska
@bozena_michalowska @arekmichalowski68 @juliett_michalowska
3 d
1 polubienie
Odpowiedz
dawid.szulta
@szulta.m @a_s_i_a_517 @julia.m32
3 d
2 polubień
Odpowiedz
marlenkamc
@frelinii @jezkatarzyna @claudia_alicjaa
3 d
2 polubień
Odpowiedz
claudia_alicjaa
@evella_92 @frelinii @_ag.g 🫧🍬
3 d
2 polubień
Odpowiedz
agata_krynicka
@monika_monaliza26 @aga.biczak @malgorzatapee
3 d
1 polubienie
Odpowiedz
ka.tarzyna886
@kamilavolska @agnieszka.wolska71 @wmarzec
3 d
1 polubienie
Odpowiedz
agataszymikowska
@sarapoblocka @agatamiszke @olakorda
3 d
1 polubienie
Odpowiedz
bednasia
@jankovska1 @echojnvckv @jankowski2634
3 d
1 polubienie
Odpowiedz
chiquitka
@materla_x @natalqap @olamatejkowska chodźcie, czas na mycie zębów!
3 d
4 polubień
Odpowiedz
anna.jeziorowska80
@mariusz_s_e @robert_szopa @skintherapy_barbara_kociuba
3 d
1 polubienie
Odpowiedz
daintylandii
@karolinaarobaak
@dominika_fl.orek
@egorecka
🤪
3 d
2 polubień
Odpowiedz
anulaaa_s
@wiczka63 @harelikava_tatsiana @kamilacza 🙌🥰🙌
3 d
4 polubień
Odpowiedz
harelikava_tatsiana
@marta_mrn @p.ola_96 @gavrilovets_margarita
3 d
3 polubień
Odpowiedz
lololololooooolll
@sebolek.airsofter @koniec_komplikacji @kasiaa_wer 😁
3 d
2 polubień
Odpowiedz
hipa6970
@piotrpaweladamski
3 d
2 polubień
Odpowiedz
kamilavolska
@weeglewska @martyna_g00 @marta.obarzanek
3 d
3 polubień
Odpowiedz
kasiaa_wer
@weronna @batubat1993 @ludwiniak.official
3 d
1 polubienie
Odpowiedz
p_parys
@sagfdl @wozky99 @martynaczygabrysia pomożecie mi wygrać mordeczki szczoteczkę
3 d
2 polubień
Odpowiedz
sakovska.m
@sakowska @joanna_melzacka @m.chmielnicki
3 d
1 polubienie
Odpowiedz
xlittlewhitelie
@julia.cyrzan @juljakartuszynska @oliwiia.l
2 d
1 polubienie
Odpowiedz
a_u_r_e_ola
@luq_as86 @alpejski_dzik @pieniaknowak
1 d
1 polubienie
Odpowiedz
a_u_r_e_ola
@czarnamamba1989 @amandababalija @masny_tata
1 d
1 polubienie
Odpowiedz
joanna_melzacka
@sakowska @gabiiszyszka @maciek3083
1 d
1 polubienie
Odpowiedz
anulaaa_s
@aaannaa_s @mstrachotka @beata.kxyz.56 ❤️❤️❤️❤️❤️❤️❤️❤️❤️❤️❤️❤️❤️❤️❤️❤️❤️❤️❤️❤️❤️❤️❤️❤️❤️
1 d
4 polubień
Odpowiedz
higienistka_by
@eliza.strakhanova @astap_mystery @zhenya_akhremko
1 d
1 polubienie
Odpowiedz
alpazc_atyde
@czapla__paulina @dominika_czapla @edyta_makeup
1 d
3 polubień
Odpowiedz
dominika_czapla
@edyta_makeup @patrryk.majcherr @czapla__paulina
1 d
3 polubień
Odpowiedz
polinowi
@dziekanskab @iga2478 @miroslawdziekanski
1 d
1 polubienie
Odpowiedz
sokolowsskaa
@lyubascher @00sebekchlebek @xxnatininaxx 😍
1 d
Odpowiedz
karolina_strachota
@patka952 ⭐ @irinav_u ⭐ @soffiia94 ⭐
1 d
2 polubień
Odpowiedz
czapla__paulina
@dominika_czapla @edyta_makeup @kamilacza
1 d
2 polubień
Odpowiedz
halina_karpinska_nieruchomosci
@rzebka @busybeesangielski @ms_lioness44
1 d
1 polubienie
Odpowiedz
julia_mroz1
@itz_natiss_ @mini_szczuroslaw @p.slimakowa czyste zęby to szczęśliwe zęby 😉
1 d
1 polubienie
Odpowiedz
londonparissss
@ivona.rudnicka @lizziejo5 @tatikow102
1 d
Odpowiedz
mozdzonek.m
@ewiny_ogrodek @wanessa__g @cristiano
1 d
Odpowiedz
roseblue900
@jadwiga_galycz @bluewomen.flowers @mateusz_galycz 🤍🤍🤍♥️
1 d
2 polubień
Odpowiedz
pilatowicz_
@robertpilatowicz @paulkaf89 @przerwa.kamila
1 d
Odpowiedz
ejsnerx
@kaligua9 @dopierpala @geraltcatposting zapraszam Waszą trójkę ❤️🔥
1 d
1 polubienie
Odpowiedz
plotherapy_
@kiniu_siaa @defugda @krzysiek_warszawa
1 d
Odpowiedz
kiniu_siaa
@defugda @plotherapy_ @jasiu1916pozdro
1 d
Odpowiedz
anna_holcka
@anna.krawczyk.35 , @kasia_leg_ , @kwiatoryna ❤️😍❤️😍🔥🔥🔥🔥🔥
20 godz.
1 polubienie
Odpowiedz
kobackakatarzyna
@kobackiprzemek @dymkowska.j @dymkowski_seweryn
19 godz.
Odpowiedz
paulina.malmur.fizjo
@katarzynagawdzik7 @albotalbom @marzenagujska
19 godz.
Odpowiedz
dymkowska.j
@kobackakatarzyna @dymkowski_seweryn @kobackiprzemek
19 godz.
Odpowiedz
karo.linaa005
@sochockanatalia @sylwia.sochocka @a.nc1x
19 godz.
2 polubień
Odpowiedz
czerwoneszpile
@mama_majeczki__ @patrycja_zaborowska_ @weraajopek ❣️
19 godz.
Odpowiedz
ola_manolaaa
@kacha_poleca @agaaww12 @its_spider 🔥🔥🔥
19 godz.
Odpowiedz
sochockanatalia
@karo.linaa005 , @sylwia.sochocka , @a.nc1x ❤️
19 godz.
2 polubień
Odpowiedz
ann.ka62
Zachęcam do udziału @brylantmc @aanetakon @zycietowygrana 💛💛💛
18 godz.
Odpowiedz
_dorcia1980
@daniel.oli.maja @majewska7008 @raspberry.x3
18 godz.
Odpowiedz
justynarub
@just.just.g @joanna.lelek30 @marzenajanaczyk1
18 godz.
Odpowiedz
justynarub
@justgabr @olkkun @lexus_is_250____
18 godz.
Odpowiedz
szeherezadka
🪥Szczoteczka soniczna, mały skarb w dłoni,
Z uśmiechem na twarzy, zęby jak diamenty broni.
Wibruje delikatnie, jak muzyka w sercu,
Czyści każdy ząb, nie zostawia w nim smutku.
Bąbelki wody tańczą, pasta się rozpryskuje,
Szczoteczka w akcji, wszystkie bakterie zgładzi.
W rytmie dźwięków sonicznych, codziennie rano,
Z dbałością o uśmiech, czyni cuda znane.
Niech każdy z nas pamięta, jak ważna to sztuka,
By zęby były zdrowe, a uśmiech – jak z bajka.
Szczoteczka soniczna, przyjaciel nasz wierny,
Z nią każdy dzień zaczynamy, w blasku porannym! @fantastyczna_5 @palovve90 @ala_niemczyk
18 godz.
Odpowiedz
majewska7008
@oliwi3r_tkd @majkrzakewelina @mama_tymcia_i_antosia
18 godz.
Odpowiedz
defugda
@jasiu1916pozdro @kiniu_siaa @henrykplota
18 godz.
Odpowiedz
myszojshimi
@madziulkakadziulka @_smieszek_kreqzolek_ @wika_xm 🔥
18 godz.
Odpowiedz
dwertos
@bvrtosz__ @xwiktorivowo @kid0745
18 godz.
Odpowiedz
balumbalum_pyszak
@joanna.staniszewska.77 @anna_sieczkowska @ania.kowalsky @ryba_czyta 🔥
18 godz.
Odpowiedz
martul12
😍 @majaopu @opolskip @_marizac_
18 godz.
2 polubień
Odpowiedz
agaaww12
@kwi3tnia.k @bebka0 @bebuszka_ ❤
18 godz.
Odpowiedz
bebka0
@bebuszka_ @karol.loko @agaaww12
18 godz.
Odpowiedz
agatshia
@pavelito_1 @malgorzatatl @margaretquaa 🥳🥳🥳
18 godz.
1 polubienie
Odpowiedz
margaretquaa
Zapraszam serdecznie @ne_ss_yy_ @alena_video_uk @nergalitka
17 godz.
Odpowiedz
malgorzatatl
@edyta.edzka @dzasta_b @dipestoagnes
17 godz.
3 polubień
Odpowiedz
natka0097_lm
Zapraszam do udziału!❤️ @kamilarynska @galaazkaa @sadfoxsoul ❤️❤️❤️
17 godz.
1 polubienie
Odpowiedz
plysiek
@bartek.szmuc @_matis___ @jel.onek ❤️❤️❤️
17 godz.
Odpowiedz
hanabiranoyouni
Ulala, jaką to piękna walentynkowa gra ❤️ uśmiecham się na samą myśl o tym, że może te super nagrodę dostanę właśnie ja? @rum3k @dovelamiadolcevita @iwannaflyawayyy
17 godz.
Odpowiedz
karolinakaspro
@sylwia.ruczynskakaliszak @jol_bug @alicja_podeszwa
16 godz.
Odpowiedz
ulia92022
@angelu_ov @vik.a1130 @gluecksstern7
16 godz.
Odpowiedz
ulia92022
@lindiknata @alynadub @inna_solonskaya
16 godz.
Odpowiedz
majkrzakewelina
@heyah_22 @majewska6150 @agni_zie
16 godz.
Odpowiedz
bebuszka_
@m.macieek @_gocha__ @agaaww12
16 godz.
1 polubienie
Odpowiedz
gabrysqaj
@karola0815 @_iamoliwia @szym_ekk
16 godz.
1 polubienie
Odpowiedz
itwas_may_
@the_czarny_family @w_zalewska_z @jasiulkove ❤️
15 godz.
Odpowiedz
itwas_may_
❤️ @karinakinia @_nataliaprzepiera_ @julietta.novak
15 godz.
Odpowiedz
itwas_may_
Zapraszam @mama_zuzuleo @szczesliwa_mama_90 @clauudiaaa97 😍😍
15 godz.
Odpowiedz
itwas_may_
Świetny konkurs @gracjanek_bamboo.junior @ewelinka_alanek @fit_matka_polka
15 godz.
Odpowiedz
xxallema
Biorę udział 🩷🎀 w zabawie i do tego samego zachęcam @janeeyre2018 @xxbarmell @kawkazeesmietanka
15 godz.
3 polubień
Odpowiedz
michellakej
Zapraszam @asiaasiaasia3737 @itchyfoodblog @cyklokot
15 godz.
Odpowiedz
milenaszubert
🪥🪥🪥🪥Zapraszam @marta_si_marta @piotrszubert @e_szubert
15 godz.
Odpowiedz
milenaszubert
🪥🪥🪥🪥Zapraszam @magic.hair.joanna.olejnik @malinowyolejwiki @surmakatarzyna
15 godz.
Odpowiedz
milenaszubert
🪥🪥🪥🪥Zapraszam @agullka88 @anna.kopec90 @justyna.mp
15 godz.
Odpowiedz
milenaszubert
🪥🪥🪥🪥Zapraszam @odnowajoannakowalska @kosmetikstudio_ewitta @marta.szajek.8
15 godz.
Odpowiedz
marakuja1212
@dolce.tinctura @mi_rolina @sophie_beagle_queen ❤️
15 godz.
Odpowiedz
its_spider
@agaaww12 @ola_manolaaa @spider_86
15 godz.
Odpowiedz
viktorvolkov
@cukrowakuchnia @di.anochka.v @ka.milo4ka.v
14 godz.
Odpowiedz
amelialozg
@vatashee @kasiaamikolajczykk @odas.793 😘
14 godz.
1 polubienie
Odpowiedz
kobackiprzemek
@kobackakatarzyna @dymkowska.j @dymkowski_seweryn
14 godz.
Odpowiedz
britney__perry
@kok_ardka97 @xwencel @karpiukgabriela
14 godz.
Odpowiedz
mifeks1983
Gram dla żony ❤️ Moja ukochana codziennie zaskakuje mnie swoim podejściem do życia, rozwiązywaniem problemów, pozytywną aurą, która ją otacza. Mimo problemów na drodze, nie zbacza z niej, wręcz przeciwnie, dzielnie im się przeciwstawia i jak tygrysica walczy o dobro swoje oraz swojej rodziny. Ukochana jest dla mnie, jak anioł, cierpliwa, stanowcza, zdecydowana w swoich postanowieniach. Ona poprawia moje złe samopoczucie, jak wróżka przegania czarne chmury nad moją głową i powoduje, że wychodzi słońce. Zawsze są dwa wyjścia z każdej sytuacji, a ona jest znakomitym tego przykładem, wybiera te najlepsze dla naszej rodziny.:)
Jest ona, jak księżyc, rozjaśnia mi codzienną drogę, jak psycholog nakieruje mnie zawsze na prawidłową drogę życia. Moja ukochana to pani domu, mama i wspaniała żona, która dba o to, aby nasze wspólne życie przebiegało swoim stabilnym rytmem, pełnym szczęśliwych momentów, niespodzianek i wrażeń. Wspólne rozmowy są ukojeniem dla duszy, natchnieniem do działania, a sekrety jej powierzone, są schowane w jej sercu, jak w skarbcu, do którego nikt nie ma dostępu. 
Żona lubi celebrować rodzinne tradycje, wspólne posiłki całej naszej rodziny, a zajmowanie się małą córeczką jest dla niej niesamowitą przygodą życia. Dzięki córeczce spełnia się ona, jako mama, macierzyństwo jest jej powołaniem, a każdy dzień to nowa kartka, na której zapisujemy swoje życie. Ona wie, jak zapełnić te kartki, urozmaicić je, dodać im blasku, dziecięcej radości, przyjemności i słonecznych promieni. 
Moja ukochana to przyjaciółka, wierny kompan do żartów, do wspólnej pasji podróżowania i zwiedzania nieznanych zakątków kraju. Jest ona pocieszycielką w trudnych chwilach i „lekarzem” przeganiającym choroby domowymi miksturami. Z nią życie jest o wiele słodsze, ciekawsze, urozmaicone. Jest ona inspiracją dla mnie, motywacją do walki z problemami, miłością i sensem mojego życia. 🔥 @kaminskawioleta1985 @uparciuszek @e.kupczak
14 godz.
Odpowiedz
podrozowiec
Zapraszam @wrazliwka @mifeks1983 @skarbik25
14 godz.
Odpowiedz
nuurcia
Zdecydowanie @karo_nawrocka 🔥 @izabelanurek @julianurek1234 🔥🔥
14 godz.
Odpowiedz
nuurcia
@magdallenamalgorzata @_malkontent @k_meczykowska 🔥❤️🔥
14 godz.
Odpowiedz
nuurcia
@wikkaas @hankaczarnecka @kolorowooka ❤️🔥❤️
14 godz.
Odpowiedz
lusiak91
@iwona_masztarowska__ @monikaaaadp @moniiaaaa2804 😍
13 godz.
Odpowiedz
lusiak91
Zapraszam ❣️
@catmia_gallery
@klaudia_kozak93
@jolantanorek 😍
13 godz.
Odpowiedz
natalia.tomkiewicz
@doktorswap @blondizehej @maciek567
13 godz.
Odpowiedz
m.piwonia
@maariibb
@becia_now
@paczkowska825
13 godz.
Odpowiedz
m.piwonia
@bl0ndpanidomu
@mamaa_zuzi
@hortensja.78
13 godz.
Odpowiedz
m_o_n_i_k_a_ewa
Świetne rozdanie ❤️ Zapraszam do @singdays58 @do_travel_too @taka.ja27 ❤️
13 godz.
Odpowiedz
martasaputa
@wolos.joanna @anna.sawicz @lusie_pracownia ☺️😄🍀💯
13 godz.
Odpowiedz
kupiec.marcin
Z ogromną przyjemnością akces do konkursu zgłaszam i do zabawy i współzawodnictwa zapraszam: @91_mat_lan @napierala.slawek @omadzik
13 godz.
Odpowiedz
krystyna.krysiunia
Zapraszam: @joannakoniuszy @martabartkowiak28 @bastek.82
13 godz.
Odpowiedz
mamamikusia89
Zapraszam @agg198720 @gochercia @xvanillaxx
12 godz.
Odpowiedz
bl0ndpanidomu
Zapraszam @ann_kkowa @m.piwonia @karolinaa_fotografia 🤍
11 godz.
Odpowiedz
bl0ndpanidomu
Zapraszam @taak_warto_zyc @ancyk_37 @oniszczuuk 🤍
11 godz.
Odpowiedz
bl0ndpanidomu
Zapraszam @k.golebiewska9 @zanciaax @skrzydla_motyla 🤍
11 godz.
Odpowiedz
martynabee_
@czarnowlosa2023 @kasiuniaa.a_ @mamazuzanity ❤️❤️
11 godz.
Odpowiedz
martynabee_
@iza_sarna @patrysiaaaa96880 @iwona_masztarowska__ ❤️❤️❤️
11 godz.
1 polubienie
Odpowiedz
ann_kkowa
Zapraszam @detektyw_mama @bl0ndpanidomu @oniszczuuk 😁
11 godz.
Odpowiedz
hi.panorama
Zapraszam @oczami_katarzyny, @malgorzatakulik_, @patrysiaaaa96880
11 godz.
Odpowiedz
jutrobedziemyszczesliwi
Super
@detektyw_mama
@zycie_postaremu
@idziemka
11 godz.
Odpowiedz
jutrobedziemyszczesliwi
Super
@monikaoperacz
@kamiii_2406
@zielone_okulary20
11 godz.
Odpowiedz
daniel.oli.maja
@majkrzakewelina @majewska6150 @oliwi3r_tkd ❤️
11 godz.
Odpowiedz
instytut.glosu.i.mowy
@aleksandra.nawrockaa @nuurcia @angelika.n20 ❤️
11 godz.
1 polubienie
Odpowiedz
angelika.n20
@aleksandra.nawrockaa @jacek.n30 @red_is_bad2
11 godz.
Odpowiedz
czytam.powiesci
@sara1kot @polskalasem @persenfona 💌
11 godz.
Odpowiedz
kawkazeesmietanka
Cudowne rozdanie. Oznaczam @janeeyre2018 @wiktoriia95 @pamela_lta
11 godz.
1 polubienie
Odpowiedz
xxbarmell
Piękna zabawa 🦷 - @marysiamomot @nm_kocham @milkmoxha 🙏🏻
11 godz.
1 polubienie
Odpowiedz
damianmoroz
@__keeejti @hania.on.board @djsylviaa
11 godz.
Odpowiedz
polskalasem
@nat__kub @masurian_blissgirl @beatakardzis
11 godz.
Odpowiedz
do_travel_too
Wow.
Super.
Biorę udział.
Zapraszam do wspólnej zabawy
❣️ @ameliaasztemborska
❣️ @andzelove
❣️ @skorpionikbalonik
10 godz.
Odpowiedz
sasiiixx
Lubię/kocham swój wybielony uśmiech, a do zabawy zapraszam @jayjayniejestspoko @agnieszka.kruk.718 @pavelurbanko
10 godz.
1 polubienie
Odpowiedz
do_travel_too
Wow.
Super.
Biorę udział.
Zapraszam do wspólnej zabawy
❣️ @bozena.lemanczyk
❣️ @hela_superdog
❣️ @m_o_n_i_k_a_ewa
10 godz.
Odpowiedz
do_travel_too
Wow.
Super.
Biorę udział.
Zapraszam do wspólnej zabawy
❣️ @maggie81iewa
❣️ @singdays58
❣️ @izabela_2722
10 godz.
Odpowiedz
pamela_lta
Miłość to uśmiech, dlatego jak relacja musi być zdrowy 💕 @milkmoxha @kawkazeesmietanka @nm_kocham
10 godz.
1 polubienie
Odpowiedz
marti.nikaa
🦷✨
@agnieszka.dabrowskaa @dora.thecocker @kamil.bogus
10 godz.
3 polubień
Odpowiedz
n.lezuchowska
@mil0sz__ @jan_lezuchowski @pati_musial
9 godz.
Odpowiedz
hope__nope
❤️❤️❤️ @liten_mane @kacper.zielinke @hej.to.ula
9 godz.
Odpowiedz
gawlowskamariola
@lizuraewa @karwoskizzr @gawlowskalidia
9 godz.
2 polubień
Odpowiedz
natalia_swic
@mm.dobrowolska
@ladyofthegarden.eva
@klebowskadorota
9 godz.
1 polubienie
Odpowiedz
ksenia_wrzosek
@szewaszew @kajamamnaimie @kasiapisz
9 godz.
Odpowiedz
"""



komentarze_facebook = """Małgorzata Sawka
Mocno trzymam kciuki za wygraną 👍
Poza tym serdecznie zapraszam
I do świetnego konkursu namawiam
🙂Martita Stawicka
🙂Dawid Dabioch
🙂Marta Budnicka
Może być zdjęciem przedstawiającym tekst „Zprzyjemnością biorę udział w zabawie Gram o super nagrodę Jeżeli wygram to będzie rewelacyjniet”

    8 godz.

    Odpowiedz
    Send message
    Ukryj


Andrzej Gdanski
Duodent Przychodnia Lekarska o nas bardzo dba!
Fantastyczne rozdanie dzisiaj więc ma!
Po soniczną szczoteczkę jak Usain Bolt gnam!
Jeżeli wygram? Czyste zęby mam!
Marius Dys
Anna Stolarz
Oliwia Kołacz

    13 godz.

    Odpowiedz
    Send message
    Ukryj
    Edytowano

Sylwia Ramos
Mięta
Zapraszam .… Wyświetl więcej
Heart Love GIF

    3 dni

    Odpowiedz
    Send message
    Ukryj

Monika Krynicka
Lecimy z tymi ZĘBAMI! Filip Krynicki Iga Jarząbska Karolina Kms

    3 dni

    Odpowiedz
    Send message
    Ukryj

Paulina Karolinka
Gram i zapraszam Monika Bartecka-Brudny. Jakub Kuba. Polakowska Monika

    3 dni

    Odpowiedz
    Send message
    Ukryj

Marta Martucha
Maciej Bobrowski Kinga Kosciewicz Franek Bobrowski

    4 dni

    Odpowiedz
    Send message
    Ukryj

Małgorzata Cee
Z przyjemnością zapraszam moich przyjaciół z Bielan: Agata Królikowska i Adam Ka oraz sąsiadkę z Woli Magdalena Sokołowska, a także siostrę Ewka Kwiatkowska ❤

    3 dni

    Odpowiedz
    Send message
    Ukryj

Krzysztof Szpejna
I ja się chętnie dołączę do konkursu, jako wierny pacjent 😁
Zapraszam: Ewa Karnkowska, Kinga Wołek, Edyta Derezińska Wołek

    3 dni

    Odpowiedz
    Send message
    Ukryj

Agnieszka Pyć
Poproszę 🙏🙏🙏
Idealny prezencik
❤️… Wyświetl więcej
Może być zdjęciem przedstawiającym 1 osoba, serce i tekst

    8 godz.

    Odpowiedz
    Send message
    Ukryj

Magdalena Kozłowska
  ·
Paulina Woźniak Sławka Migas Magdalena Zabagło Cudowna nagroda!!! 💖💖💖💖💖💖💖💖💖💖💖💖💖💖💖💖💖💖💖
Z radością powitała bym te wspaniałe nagrody. Bardzo chcę wziąć udział w zabawie, zaraz w dobry nastrój się wprawie.
Mówią że miłość to kwiat który pachnie najpiękniej i trzeba go traktować umiejętnie.
Do szczęścia nie jest potrzebne wygodne życie, lecz zakochane serce. O miłości, która jak gwiazdy na niebie – czasem skryta za chmurami, ale zawsze świecąca w sercu. Razem odkrywamy jej blask, rozjaśniając każdy dzień.
Wierzę, że poczucie szczęścia to mój wybór, więc korzystam z każdej okazji, aby się uśmiechać i brać udział w zabawie. .
Taka nagroda jest naprawdę strzałem w dziesiątkę i chciałabym, żeby moja odpowiedź także taka była.
Iż jeżeli mi się uda z miłą chęcią reprezentować będę wygraną polecając wam na Instagramie również na Facebooku.
Dzisiaj o jego fantastyczną zabawę gram. Ochoty na nagrodę coraz bardziej nabieram. Wszystkie warunki zostały spełnione. Niech nagroda leci w moja stronę. Bo zawsze warto swoich sił próbować.
Taka nagroda byłby nie tylko wspaniałym prezentem, ale także spełnieniem moich marzeń. Piękne są w życiu marzenia, choć spełnienia jest piękniejsze.
Trzeba walczyc, duża konkurencja. Za to rośnie w zabawie frekwencja. Kończę więc monolog, kciuki w mig zaciskam. Może szczęście mrugnie w moją stronę.
CZYSTA RADOŚĆ WYGRYWANIA!
Wyników wypatruję, a Was mocno ściskam!
Duodent Przychodnia Lekarska

    3 dni

    Odpowiedz
    Send message
    Ukryj

Barbara Jajko
Zapraszam Magdalena ZabagłoMarta DobrzyńskaBożenna RokickaElżbieta Kania

    4 dni

    Odpowiedz
    Send message
    Ukryj

Katarzyna Dębicka
💚💚💚💚💚💚💚💚
Edyta Wojciechowska Bożena Brodka Stasia Sucholas
💚💚💚💚💚💚💚
Duodent Przychodnia Lekarska
Konkursem swym nęci Na pewno wiele osób zachęci I Ja do konkursu się zgłosiłam Bo super nagroda mnie skusiła ☺️

    2 dni

    Odpowiedz
    Send message
    Ukryj

Tomasz Ewski
Zgłaszam się i zapraszam
Beata Wąsik
Kasia Kulczyńska
Patrycja Kaczmarek
Beata Pełka
Karol Ka
🎁

    4 dni

    Odpowiedz
    Send message
    Ukryj

Ewunia Paola
Gram próbując szczęścia
Barbara Jajko
Kama Sied
Martyna Woj

    1 dzień

    Odpowiedz
    Send message
    Ukryj

Dawid Szaboranin
Zapraszam z serducha całego
do tego rozdania walentynkowego 💘
ulubione me walentynki:
💞 Mona Plaszczyk-Gromczyk 💞
💞 Marta Woźniak 💞
💞 Sandra Suwalska 💞
💞 Agata Szychalska 💞
💞 Aneta Stańczyk Kuśmierska 💞
💞 Kinga Wyrwał 💞
💞 Alicja Stolarska 💞
..., aby miały zawsze wesołe minki 😍👄.
❤️🧡💛💚🩵💙🩷💜
*Akceptuję warunki regulaminu 🥰🍀.

    18 godz.

    Odpowiedz
    Send message
    Ukryj

Natalia Skrzyniarz
Monika Stano
Emilia Stano
Dawid Skrzyniarz

    3 dni

    Odpowiedz
    Send message
    Ukryj

Aleksandra Deputat
Paulina Zawadzka Sebastian Wieczorek Piotr Deputat

    3 dni

    Odpowiedz
    Send message
    Ukryj

Justyna Lech Gajek
Biorę udział 😍super nagrody 🥰zapraszam Sylwia Łukawska, Edyta Patrzałek, Monika Opala

    3 dni

    Odpowiedz
    Send message
    Ukryj

Magdalenka Uroda
BIORĘ UDZIAŁ 🌸 ZAPRASZAM
Dorota Szybiak
Ewa Wojtaszewska
Olga Ruszkowska

    3 dni

    Odpowiedz
    Send message
    Ukryj

Oles Lukasz
Biore udział
Anna Sok
Anna Tomasiuk
Elżbieta Kiełbasa
Elżbieta Świtulska
Emila Kejna
Magdalena Kozłowska
Sloboda Justyna
Edyta Pohl
Kozłowska
Edyta

    3 dni

    Odpowiedz
    Send message
    Ukryj

Kinga Kosciewicz
Marzena Gujska Marta Martucha Alicja Stettner

    4 dni

    Odpowiedz
    Send message
    Ukryj

Joanna Czardyban
Zgłaszam się z nadzieją
🍀🍀🍀🍀🍀
Zapraszam
Jolanta Nowostawska ,
Anna Gogler ,
Aneta Kocemba .

    3 dni

    Odpowiedz
    Send message
    Ukryj

Alicja Stettner
Konrad Stępień Anita Kudelska Dorota Skubisz

    1 dzień

    Odpowiedz
    Send message
    Ukryj

Marzena Gujska
Paulina Malmur Agnieszka Wawrzeniecka Agnieszka Markiewicz

    3 dni

    Odpowiedz
    Send message
    Ukryj

Krysia Bryzik
❤️😊❤️😊❤️😊❤️😊❤️😊
Jeszcze nieśmiało, ostatniego dnia, rzutem na taśmę - oj tak, zabiegane mamy tak mają, oto cała ja właśnie. 💁‍♀️
Liczę na łut szczęścia, zgłaszając się do rozdania i spełniając po kolei wszystkie jego zadania. 🎯
Oczywiście lajkuję, udostępniam, obserwuję i za szansę na tę super nagrodę bardzo dziękuję. 😊
Zostawiam też ciepłe serca pełne miłości - niech przyniosą tutaj dużo nowych fanów i gości! ❤️
Zapraszam: Anna Segeth, Halina Dudek, Beata Okrój
❤️😊❤️😊❤️😊❤️😊❤️😊

    1 dzień

    Odpowiedz
    Send message
    Ukryj

Klaudia Piwek
Zgłaszam się 🙋‍♀️
Zapraszam Beata Pełka, Iwona Rozalia Portaśińska, Beata Ledwoń

    1 dzień

    Odpowiedz
    Send message
    Ukryj

Edward Warszawski
Dołączam i zapraszam:
Jolanta Warszawska
Honorata Januszewska
Katarzyna Bialecka
🍀

    8 godz.

    Odpowiedz
    Send message
    Ukryj

Zaborowscy Michał Paulina
Gram
Zapraszam
Patrycja Tarasek
Ana Błękit
Paulina Wojciechowska

    14 godz.

    Odpowiedz
    Send message
    Ukryj

Dorota Skubisz
Roma Sajnog, Joanna Karczmarczyk, Magdalena Wasilewska

    1 dzień

    Odpowiedz
    Send message
    Ukryj

Anna Fijałkowska
biorę udział💚❤zapraszam MOnika JAnkowiak MoJa Dance,Barbara Teclaw,Daria Wiśniewska,Maria Teresa Nowicka

    1 dzień

    Odpowiedz
    Send message
    Ukryj

Tomasz Kaźmierczak
Witam serdecznie.
Biorę udział w konkursie, do zabawy zapraszam: Karol Kaźmierczak Ewa Świnoga Agnieszka Bremer Izabela Zawisza Ala Krzywda .

    3 dni

    Odpowiedz
    Send message
    Ukryj

Mariusz Paździora
biore udziała i zapraszam Barbara Paździora Tomasz Garbacz Robert Wójcik

    1 dzień

    Odpowiedz
    Send message
    Ukryj

Aleksandra Trafisz
❤️🌹❤️Biorę udział w konkursie ❤️🌹❤️zapraszam
Oksana Petruniv
Iza Bella
Bożena Dąbrowska
🩷🌹🩷🌹🩷🌹🩷🌹🩷🌹🩷

    22 godz.

    Odpowiedz
    Send message
    Ukryj

Barbara Nowak
zapraszam do zabawy Violetta Murzyn Violetta Murzyn Maciek Mce

    1 dzień

    Odpowiedz
    Send message
    Ukryj

Agnieszka Wąsowska
Zapraszam do zabawy. Marta Gajewska , Beata Matejek , Monika Chmielińska 🍀🍀🍀🍀🍀🍀🍀🍀
Kocham siebie za to że jestem wyjątkowa 🤗

    9 godz.

    Odpowiedz
    Send message
    Ukryj
    Edytowano

Bernadeta Bomba
Oznaczam Agnieszka SuRyl Monika Karpik Ula Łydek

    3 dni

    Odpowiedz
    Send message
    Ukryj

Dorota Ewa Szweda
BIORĘ UDZIAŁ I ZAPRASZAM
Bożena Dąbrowska Paula Odrobina Daria Michalec

    14 godz.

    Odpowiedz
    Send message
    Ukryj

Kazek Krzysztof
Z okazji Walentynek kochanie każdego dnia roku,
życzę Ci kochanie szczęścia i miłości na każdym kroku.
Samych sukcesów i pomyślności,
niech na Twojej twarzy uśmiech zawsze gości❤️
By to o czym marzysz,się w końcu spełniło,
by w życiu osobistym i w pracy się powodziło.
Wytrwałości i spełnienia marzeń,
życia ze mną pełnego wrażeń!
Życzy Ci Twój kochający mąż,
kochający niezmiennie tak samo wciąż❤️
Dziękuję Ci za wspaniałego syna i córeczkę
miej dla nas cierpliwości choć jeszcze troszeczkę!
Obiecuję,że będę w nocy częściej do córeczki wstawać,
widzę,że jesteś zmęczona pracą,obowiązkami i jeszcze jej małej trzeba cały czas radę dawać!
Jesteś taka kochana,niezastąpiona matka,żona i najlepsza przyjaciółka moja,
tyle dla mnie znaczy cała dobroć i miłość Twoja❤️
Dzięki Tobie w naszym domu czuję się wyjątkowo i wspaniale,
to dzięki Tobie-tworzysz atmosferę-działaj kochanie tak dalej!
Alicja dziękuje,że wspaniałą mamę ma,
która wszystko co najlepsze jej da❤️
Piotruś twierdzi,że lepszej mamy nie mógł wymarzyć,
która wszystkim co najlepsze chce Go obdarzyć!
Życzenia do Ciebie krótko podsumuję,
za każdy dzień z Tobą i dziećmi ślicznie dziękuję,
życzę Ci wielu zdrowych i szczęśliwych lat z nami,
Kazek z naszymi dzieciakami❤️
Kochamy Cię,jesteś dla nas wszystkim❤️ zapraszam Jadwiga Kasia Wierzba Maria Teresa Nowicka Anna Sok

    2 dni

    Odpowiedz
    Send message
    Ukryj

Agnieszka Rutkowska
Biorę udział w zabawie
Zapraszam
Karolina Jod
Beata Marta
Monika Kołodziejczyk
Monika Monia Kalista
Izabela Szybalska
Iza Izabela

    2 dni

    Odpowiedz
    Send message
    Ukryj
    Edytowano

Przemek Pe
Magdalena Kwiecień Sandra Malina Zuzia Kamratowska

    21 godz.

    Odpowiedz
    Send message
    Ukryj
    Edytowano

Fred Graf
@wyróżnienie Szykuje się dobra zabawa 😍

    4 dni

    Odpowiedz
    Send message
    Ukryj

Katarzyna Bajda
Filip Bajda Eliza Bajda Ewa Szyszka
Gramy🤗

    10 godz.

    Odpowiedz
    Send message
    Ukryj

Karolina Kowalewska
Rafał Kowalewski Patrycja Szczuka Natalia Choińska 🙂

    4 dni

    Odpowiedz
    Send message
    Ukryj

Iwona Skorek
Dominika Bober
Iza Sarna
Sylwia Zielińska
Szczoteczka soniczna zęby
czyści, myje i pielęgnuje,
codziennie ją oczywiście zastosuję.
Dla zębów jest ona zaprojektowana,
zastosuję ją także do dziąseł masowania. 🙂
Dzięki niej zęby będą idealnie czyściutkie,
Wyglądać będą, jak nowiutkie.
Zapewni mi ona skuteczne czyszczenie,
Dla moich zębów to marzeń spełnienie.
Ta szczoteczka łagodne włosie posiada,
Za czyste zęby i dziąsła odpowiada.
Jest wyjątkowa, szczotkowanie
nią będzie przyjemnością,
używać jej będę z wielką radością. 🙂
Bakterie i płytkę nazębną usuwa dokładnie,
A do tego wygląda ona ładnie.
Zęby i dziąsła poleruje ona doskonale,
Wszędzie w jamie ustnej szczoteczka
zrobi „porządek”, bakterie znikają,
Do trudno dostępnych miejsc
dociera, użytkownicy ją kochają. 🙂

    2 dni

    Odpowiedz
    Send message
    Ukryj

Monika Monia Kalista
Super konkurs. Skuszę się na nie Nagroda marzenie Więc warto grać o jej spełnienie Gram z przyjemnością i na wyniki czekam z niecierpliwością Cudowna nagroda do wygrania Więc zgłaszam się bez wahania Świetnie Bosko Wspaniale Gdybym wygrała byłoby doskonale. Fajnie, że tutaj trafiłam Świetny konkursik zobaczyłam. Super konkurs organizujecie Świetną.Biorę udział be konkursie tym Może los dopisze i wygram w nim nagrodę prezentujecie Szczęśliwcę nią obdarujecie O super nagrodę z przyjemnością gram Bo właśnie na nią mega chrapkę mam Byłabym szczęśliwa i zadowolona. Takim prezentem wręcz zachwycona Taka nagroda wywołałaby uśmiech na mej twarzy oraz Bo przecież każda duży i mały o takim marzy Ale bym frajdę miała Gdybym takie cudo w prezencie dostała Radości nie byłoby końca, bo ta nagroda jest imponująca Nie pozostaje mi nic innego jak tylko zgłosić swój udział w konkursie tym Koleżanko kolego Może mi nie uwierzycie Ale tym magicznym prezentem niesamowitą niespodziankę mi sprawicie❤❤❤ Kciuki trzymamy I do zabawy zapraszamy
Zofia Alicja Stepien
Marta Kalista
Anna Kwapisz

    3 dni

    Odpowiedz
    Send message
    Ukryj

Pat Ka
Wiśniewscy Alicja Tadek Patt Ka Bartek Bartek

    4 dni

    Odpowiedz
    Send message
    Ukryj

Anna Wartalska
Iwona Wartalska
Monika Kotala
Agnieszka Wawrzyniak
💋

    11 godz.

    Odpowiedz
    Send message
    Ukryj

Stanisław Grocholski
Biorę udział i zapraszam Krysia Buś Janina Mrozek Janina Stanowska

    18 godz.

    Odpowiedz
    Send message
    Ukryj

Edward Warszawski
Duodent Przychodnia Lekarska Czy nagrody będą wysyłane, czy może tylko odbiór osobisty?

    13 godz.

    Odpowiedz
    Send message
    Ukryj

Beata Włodarczyk
Iwona Zielińska Zofia Włodarczyk Marcin Włodarczyk dbamy o zęby i uśmiech 😀 a Duodent Przychodnia Lekarska zawsze polecam, nawet jak nie wygrywam 🌸

    3 dni

    Odpowiedz
    Send message
    Ukryj

Paulcia Paulinka
BIORĘ UDZIAŁ SPEŁNIONE WARUNKI
Beata Szlagor Nowak
Margaretta Jańczak-Zarycka
Ewelina Kotas

    1 dzień

    Odpowiedz
    Send message
    Ukryj

Kinga Jędzura
Julia Mędak Dorota Józwik Sylwia Jaworska

    2 dni

    Odpowiedz
    Send message
    Ukryj

Monika Legęza
Mariola Szabat Anna Myszak Marcela Legęza

    4 dni

    Odpowiedz
    Send message
    Ukryj

Ola Katarzyna Król
Brzozo Ska Natalia Kozłowska Kamil Pe

    1 dzień

    Odpowiedz
    Send message
    Ukryj

Ola Katarzyna Król
Ela Rosik Ewelina Borkowska Kasia Łuniewska

    4 dni

    Odpowiedz
    Send message
    Ukryj

Aneta Stalinska
Zapraszam serdecznie do wzięcia udziału w konkursie Beata Sonnek Katarzyna Biel Anna Mak ♥️🫶♥️
GIF

    20 godz.

    Odpowiedz
    Send message
    Ukryj

Judyta Pati
Marcelina Starska Anna Tomaszewska Ewa Brańska

    21 godz.

    Odpowiedz
    Send message
    Ukryj

Marlena Staropiętka
Paweł Staropiętka Sebastian Zmorski Paulina Liberska

    3 dni

    Odpowiedz
    Send message
    Ukryj

Ola Katarzyna Król
Magdalena Nogal Dominika Urbańska Anka Lech

    4 dni

    Odpowiedz
    Send message
    Ukryj

Stanisław Małgorzata Kieta
Ewa Madeja
Stasiu Kieta
Magdalena Kieta

    13 godz.

    Odpowiedz
    Send message
    Ukryj

Łukasz Kijek
Kacper Kijoch Alan Zychowicz Oskar Krzemiński

    17 godz.

    Odpowiedz
    Send message
    Ukryj

Ewa Ewa
Helena Jabłońska Paweł Jerzy Florek Mirosław Kotasiński

    20 godz.

    Odpowiedz
    Send message
    Ukryj

Justyna Bacławska
Adam Bacławski Rafał Boguszewski Diana Kostrzewa

    10 godz.

    Odpowiedz
    Send message
    Ukryj

Piotr Wojciechowski
Maciej Pach Patrycja Boczek Bartek Pe

    20 godz.

    Odpowiedz
    Send message
    Ukryj

Barbara Paździora
Zofia Korzeniowska-Wójcik Bernadeta Brusik Mariusz Paździora

    1 dzień

    Odpowiedz
    Send message
    Ukryj

Justyna Zejfert
Kamil Zejfert Joanna Olszewska Paulina Luvvka 🥰

    2 dni

    Odpowiedz
    Send message
    Ukryj

Magdalena Sakowska
Joanna Melzacka
Maria Sakowska
Klaudia Sakowska

    3 dni

    Odpowiedz
    Send message
    Ukryj

Anto Miny
Agnieszka Kowalczuk
Agata Negowska
Renata Nowak

    2 dni

    Odpowiedz
    Send message
    Ukryj

Arkadiusz Potek
Izabela Balowska Natalia Slaska Kacper Student

    21 godz.

    Odpowiedz
    Send message
    Ukryj

Joanna Melzacka
Maria Sakowska Magdalena Sakowska Klaudia Sakowska

    1 dzień

    Odpowiedz
    Send message
    Ukryj

Maria Sakowska
Joanna Melzacka Magdalena Sakowska Klaudia Sakowska

    2 dni

    Odpowiedz
    Ukryj

Natalia Rutkowska
Kinga Murszewska
Klaudia Czarnecka
Adrianna Kawczyńska
💜

    4 dni

    Odpowiedz
    Send message
    Ukryj

Ela Grudnik
Bożena, Dariusz, Anna

    15 godz.

    Odpowiedz
    Send message
    Ukryj

Kinga Jędzura
Klaudia Marcinkowska Olga Kowalewska Dominika Breś

    2 dni

    Odpowiedz
    Send message
    Ukryj

Ania Dudkowiak
Monika Szczypczynska Monika Zaborowska Renata Kulka

    2 dni

    Odpowiedz
    Send message
    Ukryj

Adrianna Fliszewska
Rafał Fajfer Krzysztof Fliszewski Aleksandra Fliszewska

    3 dni

    Odpowiedz
    Send message
    Ukryj

Sandra Malina
Adrianna Przystawska Anna Koltek Anna Koczera-Milasz

    21 godz.

    Odpowiedz
    Send message
    Ukryj

Małgorzata Warmbier
Ewa Warmbier Magdalena Kwiatkowska Michał Kwiatkowski

    2 dni

    Odpowiedz
    Send message
    Ukryj

Halinka De
Karolina Magdalena Matysiak
Marta Kawa
Pomysłowy Sławomir

    1 dzień

    Odpowiedz
    Send message
    Ukryj

Filip Nowakowski
Dominika Nowakowska Wiktoria Nowakowska Dominik Nowakowski

    21 godz.

    Odpowiedz
    Send message
    Ukryj

Dominika Nowakowska
Alicja Tomaszewska
Elżbieta Tomaszewska
Wiktoria Traczyńska-Sala 🦷 ✨

    21 godz.

    Odpowiedz
    Send message
    Ukryj

Natalia Kostro
  ·
Ania Kostro Jadwiga Kostro Nikola Zieleń Magdalena Luna 👄

    2 dni

    Odpowiedz
    Send message
    Ukryj

Daria Cieszyńska-Bladowska
Ludwik Cieszyński
Oliwia Recław
Kinga Rapacz

    1 dzień

    Odpowiedz
    Send message
    Ukryj

Sandra P-ka
Mariusz Malecki Dorota Chraścina Anita Karbownik

    21 godz.

    Odpowiedz
    Send message
    Ukryj

Ewa Kawczyńska
Zdzislawa Burzycka Magda Lena Sadzyńska Paweł Jerzy Florek

    21 godz.

    Odpowiedz
    Send message
    Ukryj

Danusia Kujawska
Natalia Pirańska Anna Gorajek Monika Złotowska

    1 dzień

    Odpowiedz
    Send message
    Ukryj

Józef Durka
Jakub Białkowski
Mateusz Durka
Sebastian Durka

    16 godz.

    Odpowiedz
    Send message
    Ukryj

Joanna Asia
🥳 Oleksandr Zehria , Grażyna Jabłecka , Natalia Kaczmarek

    1 dzień

    Odpowiedz
    Send message
    Ukryj

Dorota Ł. Szopa
Biorę udział 🎈
Dopisuję się do rozdania!
Tak, tak!
Mega zabawa!
Rewelacja 🎯
Doskonała wręcz zabawa! 🌞
Z radością i przyjemnością wielką zgłoszenie swoje zostawiam 🎈
A Was
serdecznie zapraszam
Anna Lewińska
Mariusz Szopa
Janina Luszcz
✅✅✅✅✅✅✅✅✅
Może być zdjęciem przedstawiającym kwiat

    10 godz.

    Odpowiedz
    Send message
    Ukryj

Margaretta Jańczak-Zarycka
❣😻💞🍾💐🎉🎉🎉
Z WIELKĄ PRZYJEMNOŚCIĄ BIORĘ UDZIAŁ😍 POLECAM STRONĘ I ZAPRASZAM DO WSPÓLNEJ ZABAWY 🍀🌟💚
Mocno trzymam kciuki za uśmiech losu! 🍀
Hela Staszyńska
Marta Potrzebka
Izabela Klejdysz
Może być zdjęciem przedstawiającym serce i kwiat

    2 dni

    Odpowiedz
    Send message
    Ukryj

Magdalena Magdalena
Zapraszam Katarzyna Flak Aleksandra Zwierko Mateusz Łukasz ❤️
Takie zestawy to super sprawa,
Bo piękny uśmiech to podstawa.
Bardzo chciałabym wygrać
I móc o swój uśmiech lepiej zadbać.
A przy tym radości sprawi mi wiele,
Gdy z kimś z Was wygraną się podzielę 😍😍😍

    4 dni

    Odpowiedz
    Send message
    Ukryj
    Edytowano

Bogdan Czerwiński
Z przyjemnością gram zapraszam Martyna Papuszka Iwona Celińska Martyna Koszatniczka
Może być zdjęciem przedstawiającym serce, deser i tekst

    1 dzień

    Odpowiedz
    Send message
    Ukryj

Kwiatek Łukasz
Biorę udział w zabawie i dla walentynki swojej gram. Może wielki cud Nas spotka i prezentem od państwa obdaruję mojego kotka.
Chyba z zachwytu by oszalała i mnie z całych sił wyściskała 😁😁😁 a może i buziakiem obdarowała 😁😁😁
Wszyscy grają i prezenty zgarniają może i mi się tutaj uda choć nie wierzę jeszcze w cuda 🙈
Trzymam zatem mocno kciuki może i do mnie u państwa los się uśmiechnie i uszczęśliwię żoneczkę 🥰
Zapraszam
Iwona Kwiatek Sylwia Kwiatek Joanna Kardasz Duodent Przychodnia Lekarska

    1 dzień

    Odpowiedz
    Send message
    Ukryj

Beata Szczawińska
Pragnę wygrać ♥️ SZCZOTECZKI 🤍 , to moje marzenie,
Niech los się uśmiechnie i spełni pragnienie.
W sercu mam nadzieję, wielką wiarę w duszy
Że mój wierszyk Duodent Przychodnia Lekarska serce skruszy.
Próbuję, działam, daję z siebie wszystko,
By osiągnąć cel i sięgnąć tak blisko.
Niech moje starania uszczęśliwią mnie
Bo z całego serca wygrać bardzo chce
Wierszem to piszę, by szczęście przywołać,
By państwa zachwycić i los swój wywołać.
Nagrodo, już czekam — przyjdź do mnie czym prędzej,
Spełnij me marzenie, daj radość w tym pędzie!
Zapraszam
Stanislaw Wydra
Beata Jagielska
Arleta Seroczynska
Beatka Sz Seroczyńska
Beata Wąsik
Wiesław Szczawinski
Może być zdjęciem przedstawiającym 2 osoby i kwiat

    2 dni

    Odpowiedz
    Send message
    Ukryj

Paulina Mianowska
Biorę udział
Zapraszam do zabawy
Lukasmarcysia Lelitoo
Justyna Iwona Olle
Elżbieta Kania
Beata Pełka
Anna D. Łopot
Jolanta Znaj
Ewunia Paola
Dorcia Paulina Sk
Paulcia Paulinka
Anna S Paulla
Agnieszka Michalska
Urszula Kulkowska
Madzia Kozlowska
Monika Szczypczynska
Aleksandra Trafisz
Zaborowscy Michał Paulina
Anna Sok
Iza Izabela
Sylwia Wilamowska
Paulina Woźniak
Agata Aga Olkuska
Aneta Stalinska
Adriana Schenk
Agnieszka Rutkowska
Teresa Koneczna
Paulina Karolinka
Małgorzata Pawłowska
Paulina Dolecka
Kinga Perłowska
Karolina Wiktoria Pe
Justyna Justyna
Margaretta Jańczak-Zarycka
Małgorzata Goławska
Magdalena Kozłowska
Beata Szlagor Nowak
Beata Szczawińska
Sloboda Justyna
Gosia Mamita

    23 godz.

    Odpowiedz
    Send message
    Ukryj

Jadwiga Kasia Wierzba
Walentynki to miłości czas,
którą przeżywa każdy z nas ❤
Ja swojej czuły liścik napisałam,
i cała moją miłość mu wyznałam.
Jesteśmy razem już 13 lat,
pięknej,długiej miłości czas ❤
Moja miłość do Ciebie,
jest jak słodka czekolada!
Dzięki Tobie czuję się jak w niebie,
nasze życie to piękna ballada.
Dziękuję Ci za każdą noc i dzień,
kiedy przy mnie stoisz jak mój cień.
Kocham Cię mój drogi nad życie,
o takiej miłości całe życie marzyłam skrycie!
Przygotuję dla Ciebie smaczną kolację i wyśmienite wino,
wcześniej zahaczymy o nasze kino!
Poświęć się dla mnie i na komedię romantyczną mnie weź,
na spacerek za rączki po parku też 🙂
Powspominamy nasze wspólne cudowne lata i porobimy zdjęcia na pamiątkę,
dzieci zostawimy u babci-nareszcie będziemy sami-tu tkwi wyjątek!!!
Uwielbiam z Tobą wspólnie spędzać czas,Ty też wiem,
razem chcemy być....przytulić,pocałować się ❤
W takim dniu wystarczą drobne gesty,buziak,a nie drogie prezenty,a jak
Kochamy się cały rok bardzo mocno!!! o tak ❤
Oddałam Ci serce moje,oddałam moje sny,
a Ty podarowałeś mi cudowne noce i wszystkie piękne dni ❤ zapraszam Iwona Maria Sosnowska Joanna Magdalena Walczyk
Może być zdjęciem przedstawiającym 2 osoby i koń

    1 dzień

    Odpowiedz
    Send message
    Ukryj

Krzysiek Dabrowski
Bosko 😊😊😊
Z ogromną radością i uśmiechem na twarzy biorę udział w tym super konkursie i gram o fantastyczną nagrodę
Zapraszam do zabawy
Kasia Bargiel
Jakub Kuba
Justyna Bałchan
Elżbieta Kania
Elwira Golec
Elżbieta Dziukiewicz
Paula Ada Szczygłowska
Ewunia Paola
Paulina Woźniak

    14 godz.

    Odpowiedz
    Send message
    Ukryj

Aleksandra Dopierała
Kocham siebie za siłę, która każdego dnia pcha mnie do działania i za upór, dzięki któremu wciąż osiągam sukces. Podzieliłabym się nagrodą z moim mężem, Artur Dopierała, który oczywiście powinien wziąć udział i zapraszam jego oraz Kasia Jóźwik i Wioletta Kaczmarek, by też spróbowali swoich sił. ♥️

    1 dzień

    Odpowiedz
    Send message
    Ukryj

Patrycja Libner
Biorę udział 🍀 gram o prezent😍
Powiem prosto też: nikt tak jak ja nie potrafi się cieszyć z wygranych. Ja się cieszę do tego stopnia, że mam taki wyrzut adrenaliny, aż mam ścisk serduszka, a moje poliki są czerwone jak burak 😁🤣
Do konkursu zapraszam
Dominik Lemisz
Tom Nowak
Anna Pietrusewicz
🍀🍀🍀

    1 dzień

    Odpowiedz
    Send message
    Ukryj

Plik Martin
Gram dla mej żoneczki mej szalonej, pozytwynie zakręconej i najdroższej ukochanej ... z radości by mnie ukochała i milion buziaków dała. Buzia by się jej cały dzień śmiała i tym uśmiechem wszystkich w koło by obdarowała. 😍❤️Szczęście to jedyna rzecz, która się mnoży jeśli się ją dzieli".
💠🪩🌀❄️🌠🍀🌠❄️🌀🪩💠
biorę udział
💠🪩🌀❄️🌠❤️🌠❄️🌀🪩💠
Zapraszam Elżbieta Dziukiewicz Monika Karpik Agata Blicharska
Może być zdjęciem przedstawiającym serce, kawa i filiżanka kawy

    3 dni

    Odpowiedz
    Send message
    Ukryj

Agnieszka Kruszewska
Gdy te konkurs ujrzałam 👀💝 , od razu o mojej babci pomyślałam 👵💓👑. Chciałabym ten prezent podarować właśnie Jej 💓
Moja babcia 15 lutego kończy 86 lat , dzień wcześniej są Walentynki ale niestety moja babcia nie ma już swojej Walentynki 😔🕯💔. Bardzo wiele Jej zawdzięczam , więc na pewno miło by Jej się zrobiło na sercu 💕w te Święto. Dla niektórych moje Walentynkowe plany mogą wydawać się śmieszne albo banalne. Ale ja ten dzień chciałabym spędzić z moją ukochaną babcią... Wiem ile dla Niej znaczy moja obecność... Mam w planach Ją odwiedzić z dużym bukietem róż oraz napoleonkami , które uwielbia ❤. Będzie to czas spędzony na życiowych rozmowach , wspomnieniach , oraz oglądaniu pamiątkowych zdjęć. I oczywiście trzeba będzie "spalić" te napoleonki 😁💪 , więc Nordic Walking , który obje tak kochany ❤❤.
💓 Moja babcia Tereska jest po prostu szalona , nie jednego młodzieniaszka w wielu rzeczach pokona💪👊🔥 Od wszystkich , nawet nieznajomych zawsze otrzyma tzw "ukłona" 😀. Nie jeden mężczyzna jak się zapatrzy oooooooj to nawet zaliczy tzw "dzwona" 🔔🤕👁️👁️😂
Babcia była już "dilerką" zanim stało się to "modne" 🤣. Od 33 lat po dziś dzień , przymyca banknoty w czekoladach albo bombonierka i mówi "Tylko nie pokazuj "starym" 😉😂
Z ręką na sercu mówię , że na swoją babcię nigdy nie powiedziałam złego słowa. Dziękuję Jej za to , że nigdy nie usłyszałam od Niej słów " Nie teraz , nie mam czasu , poczekaj ,później ". Nawet jak była czymś bardzo zajęta , zostawiała wszystko i poświęcała mi uwagę . Jest bardzo wyrozumiałą , uczynną i bardzo elegancką kobietą. 👸👑 Nie miała łatwego życia , wcześnie została wdową, z dwójką małych dzieci, ale nigdy się nie poddała , bo mimo trudności miała dla kogo żyć. Jest to kobieta o napuchniętym miłością przeogrooooomnym sercu ❤. Nigdy nie dzieliła ludzi , dla każdego zawsze ma ogromny szacunek, zawsze była zaradna. Mimo , że teraz są takie czasy , że można kupić wszystko. Moja babcia do dnia dzisiejszego potrafi zrobić coś z niczego, bo pamięta czasy gdy nie miała dużo pieniędzy. To moja babcia nauczyła mnie cierpliwości , to dzięki Niej opanowałam do perfekcji sztukę negocjacji , oraz poprawiła moją zdolność obserwacji . Ile razy świat wypadał mi z rąk , Ona zawsze była .... To Jej pierwszej zawsze zwierzałam się z wszystkich moich miłostek i bolączek, bo wiem ,że Jej ramiona zawsze są dla mnie otwarte. Moja ukochana babcia po dziś dzień mi powtarza piękne słowa , które na zawsze utkwią mi w pamięci .... ,ŻE NIE TEN JEST NAPRAWDĘ SZCZĘŚLIWY CO WSZYSTKO MA . TYLKO TEN KTÓRY DOCENIA TO CO MA , MIMO ŻE MOŻE CZASEM MA BARDZO MAŁO . To babcia nauczyła mnie , sztuki przemilczenia i wybaczania , a jednocześnie walki o swoje.
To babcia przekazała mi ZŁOTĄ 10tkę rad życia 🎯🔟❤
Po pierwsze: (wiek to tylko liczba ) zawsze mimo swoje wieku ubieraj tylko kolorowe ubrania -nic tak nie dodaje energii jak "żywe" , "rzucające się w oczy" kolory ❤️💛💚💙💜♥️
Po drugie: makijaż zawsze musi być 👸💄💋👄👁👁nawet nie wiem jak bardzo byłabyś bardzo zmęczona musisz się zmobilizować i podkreślić swoje oczy i usta 🥰
Po trzecie : nóżka na obcasie albo na koturnie. Obcas zawsze doda Ci odwagi, także śmielej i bardziej ochoczo pójdziesz przez życie nawet w pochmurnym dniu! 💃🏻👠👡
Po czwarte: śniadanie obowiązkowe-dzięki niemu, kiedy jest pożywne dostaniesz kopa na cały dzień. 🦸‍♀ Do szkoły i pracy również zabieraj "kolorki" banan , jabłko , kiwi , brzoskwinia , gruszka 🍏🍎🍐🍊🍌🥝
Po piąte: PRZERWA -kiedy kawka czy herbatka warto sięgnąć po coś z węglowodanami-cukry! czemu nie! od dwóch cząsteczek nigdy nie przytyjemy 🍫😇🤗a magnez w czekoladzie doda Ci powera i da upust nerwom. 🦹‍♀🦸‍♀
Po szóste: dużo ruchu 💪🏻🦶🏼🦵🏼 rower , spacery, basen.
Po siódme: rozpieszczaj się w domu. Kąpiel z niewyobrażalną ilością piany 🛀🏻🧼🧽🚿. W tle relaksujące muzyka i świece. 💡📻
Po ósme: nie przejmuj się już stertą ubrań czy kurzem zalegającym na meblach 🤗 Od brudu nikt nie umarł, a przecież królowa Teściowa 😀😀😀😀 jak będzie chciała i tak Ci zawsze dogryzie, nawet jak będzie wszystko lśniło 🥴🤭🤫💎 ❤💗❤💗❤💗
Po dziewiąte: zmień hasło: "co mam zrobić jutro, zrobię...kiedy będzie mi się chciało 😀🤗
Po dziesiąte: staraj się zawsze dostrzegać drobnostki w swoim otoczeniu i dostrzegaj swój każdy mały krok do przodu. Babcia nauczyła mnie 1️⃣ Wiary, że gdy połknę pestkę (np. jabłka) to w brzuchu urośnie mi drzewo – dziś mam prywatny sad.
2️⃣ Że ludzie lubią jak mówi im się prawdę – dziś nie oszukuję
3️⃣ Że nerwy trzeba schować czasami do konserwy – dziś potrafię być cierpliwa.
4️⃣ Że wydłubię sobie oko łyżeczką od herbaty – dziś piję tylko kawę , i soki 😁😁
5️⃣ Że jak dojadę na miejsce, mam dać znać – dziś sama troszczę się o innych.
6️⃣ Że jak nie zgaszę świeczki to spalę dom – dziś jestem odpowiedzialna i przewidująca.
7️⃣ Że z rodziną fajnie jest nie tylko na zdjęciach – dziś jest moim priorytetem. 1⃣🏅🏆
To babcia nauczyła mnie "błyszczeć" 🌟💖
Śmiało mogę powiedzieć , że moja babcia jest wzorem do naśladowania 👩‍❤‍👩👩‍❤‍💋‍👩👭. Jak sama o sobie mówi " Jest emerytką ale zawsze i wszędzie jeszcze na czas zdąży i za najnowszym trendem podąży 😍💃👣
Aleksandra Kruszewska
Aneta Krekora
Agnieszka Znyk
Marta Rosińska
Marlena Kathke
Może być czarno-białym zdjęciem przedstawiającym 1 osoba, niemowlę i śmiech

    4 dni

    Odpowiedz
    Send message
    Ukryj

Beata Barbara
🎁🍀Biorę udział z wielką przyjemnością I radością 🍀🎁💞🐘
Cudna nagroda mi się marzy I może szczęściem mnie obdarzy 🐘💞🎁🍀
Szczęście przybywaj mocno kciuki trzymam za uśmiech losu 🍀🎁💞🐘
Zapraszam Kasia Kulczyńska Marta Dzedzej Wróbel Asia Cudasia Kama Sied Karolina Wojewoda 🐘💞🎁🍀❤🎊🥰💚🌷💛🌹🌻💙💖🔥💋

    4 dni

    Odpowiedz
    Send message
    Ukryj

Mariusz Szopa
BIORĘ UDZIAŁ! 🙂
GOTOWE! 🙂
ZROBIONE 🙂
Przewspaniałej urody zmysłowo-uczuciowej, potrzebny nieziemsko w codzienności, takie bajeczne must have, niebanalny, fajny, urodny, barwny, sprawdzony, markowy, praktyczny, magiczny, doskonały, wizualny, niepowtarzalny mega potrzebny wielce uroczy, niesamowity, z prezencją, świetny, zgrabny i powabny, dobrutki, wizualny, rewela - podarek! 🙂Będę piękny i zjawiskowy, megaśny podarek miał!🙂Ha! Rewelacja! Ooo! Tak! 🙂
Łaaaaaał! Ależ mega sprawa i zabawa! Kolorowa, mega, przewyborna, interesująca, wspaniała - po prostu: rewelacja! Udział w zabawie rzecz jasna i ja swój zgłaszam, ochoczo do rozdania zacnego łączę, o świetny, zjawiskowy, niebanalny, z prezencją, elegancki, niesamowity, znamienity, potrzebny, specjalny, zachwycający wielce podarek niespodziankowy, fajny, nietuzinkowy, dizajnerski, miły, doskonały, nieziemskiej urody, powabny, ładny i zgrabny!
zaproszę
Jurek Buś
Beata Szczawińska
Krzysztof Kołek
Andrzej Graczewski
Dorota Ł. Szopa
Może być zdjęciem przedstawiającym koniczyna biała

    9 godz.

    Odpowiedz
    Send message
    Ukryj

Anita Brzdęk
🌷🌿 Świetnie. Zgłaszam się.🌷🌿
🌷🩷Szczęście... jesteś?🌷🩷
🌷🩷🌷 Duodent Przychodnia Lekarska z przyjemnością BIORĘ UDZIAŁ w konkursie 🙂👍🙂
🌷🩷🌷Byłoby wspaniale , byłoby bosko gdyby udało się wygrać ✊👍🙂
Zapraszam do wspólnej zabawy
Anna Pałęga
Dorota Czajowska
Beata Sygiet
Może być rysunkiem przedstawiającym co najmniej jedna osoba, uśmiechnięci ludzie i serce

    15 godz.

    Odpowiedz
    Send message
    Ukryj

Stanisława Wawrzyk
Xoxo bardzo miło xoxo ❤️❤️❤️❤️🔥🔥🔥🔥🔥
😍
Bardzo marzy mi się taka nagroda jest przednia byłabym bardzo z niej zadowolona i wprost skakała do sufitu. ❤️❤️❤️❤️❤️🔥🔥🔥🔥🔥
Macie naprawdę dużo wspaniałego 😍 asortymentu 👍 z pewnością bym się wszystkim pochwaliła taka nagroda 🏆 na fb i swoim bliskim bo niech każdy się dowie o tak wspaniałym sklepie jakim jest wasz. Wygrać to jest moje wielkie marzenie
Warto marzyć bo czasem się one spełniają. Trzymam mocno kciuki ✊ ❤️❤️❤️❤️❤️❤️🔥🔥🔥🔥🔥
😘 🚀 zdecydowanie 10/10
Same wspaniałe hity tego sezonu 🔥 ‼‼‼🆕✂💟🔝🔝🔝👍😀❤️❤️❤️❤️❤️
BIORE UDZIAŁ 😊 ‼‼‼
Świetnie wspaniale bosko
Bardzo miło 😊 🌹🌹
Zapraszam
Edyta Myśliwiec
Anna Gołębiewska
Izabela Klejdysz
Renia Huber
Agnieszka Jęczkowska
Kasia Modera
Monika Wieczorek
Anna Wildangier Maharjan

    1 dzień

    Odpowiedz
    Send message
    Ukryj

Lucyna Kmiecik
Z pięknym uśmiechem łatwiej iść przez życie a ten jak wiadomo zależy od troski i dbania o swoje ząbki, dlatego byłoby cudownie wygrać te szczoteczki i rozjaśnić nie tylko swój uśmiech, ale też mamusi czy cioteczki 🙂
Zapraszam: Rafał Faleński, Diana Szydło, Tamara Jaśkiewicz

    2 dni

    Odpowiedz
    Send message
    Ukryj

Stefania Kupczak
Ta nagroda mi sie marzy, moze szczescie sie przydarzy i nagroda trafi do mnie i ucieszy mnie ogromnie🍀🍀🍀🍀 Wiec czym predzej sie zglaszam i znajomych zapraszam Daria Badurska Maria Roszczak Irena Zofia Jagoda Gronowska Ewa Lesniewska ❤

    2 dni

    Odpowiedz
    Send message
    Ukryj

Magda Lis
Biorę udział 🩵
Zapraszam
Anna Baran
Kuba Jacek
Katarzyna Głuch

    1 dzień

    Odpowiedz
    Send message
    Ukryj

Patrycja Winowiecka
Biorę udział 🥰🍀
Zapraszam Aga Geschke Agata Aga Olkuska Ligocka Justyna
🥰🥰🥰🥰❤️❤️❤️❤️❤️❤️❤️❤️❤️❤️🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸😍😍😍😍😍😍😍😍😍😍😍😍😍😍🤩🤩🤩🤩🤩🤩🤩🤩🤩🤩🤩🤩🤩🤩🤩🥳🥳🥳🥳🥳🥳🥳🥳🥳🔥🔥🔥🔥🔥🔥🔥🔥❤️❤️❤️❤️❤️❤️❤️❤️❤️❤️❤️❤️🤗🤗🤗🤗🤗🤗🤗🤗🤗🤗🤗🤗🤗🤗🤗🤗🤗🤗🤗🤗🤗🤗🤗🤗🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸🌸

    1 dzień

    Odpowiedz
    Send message
    Ukryj

Stanislaw Wydra
Biorę udział z miłą chęcią
Fantastyczna nagroda mi się marzy,
Czy to się dziś wydarzy?
Wszyscy w konkursach wygrywają
I fantastyczne nagrody zdobywają.
Zapraszam
Urszula Wy
Ewa Wojciechowska
Tamara Jaskiewicz
Justyna Naczk
Beata Szczawińska
My Heart Love GIF by LINE FRIENDS

    1 dzień

    Odpowiedz
    Send message
    Ukryj

Karol Ka
Biorę udział ✋
Zapraszam … Wyświetl więcej
GIF

    3 dni

    Odpowiedz
    Send message
    Ukryj

Agnieszka Dąbrowska
Świetnie 🌷🌷🌷
Z wielką przyjemnością biorę udział w konkursie i do wspólnej zabawy zapraszam znajomych
Hanna Jędro
Ka… Wyświetl więcej

    9 godz.

    Odpowiedz
    Send message
    Ukryj

Bernadeta Pawłowska
Wspaniała nagroda ❤️ Biorę udział 🍀 Zapraszam serdecznie Katarzyna Michałowicz Alicja Foltys Alicja Janc

    12 godz.

    Odpowiedz
    Send message
    Ukryj

Dorota Sycha
Super nagroda❤️
Zapraszam serdecznie
Edyta Bąkiewicz
Olga Kalinowska
Edyta Kaczkowska
❤️❤️❤️

    12 godz.

    Odpowiedz
    Send message
    Ukryj

Joanna Dąbrowska
Chcę ze swoimi naturalnymi zębami w pięknym uśmiechu przez życie kroczyć, a nie sztuczne zęby w szklance moczyć 😁
Zapraszam Marzena Mórawska Ewelina Kiliańska Renata Mariusz Dądera

    4 dni

    Odpowiedz
    Send message
    Ukryj

Jolanta Warszawska
Wskakuję i ja na koniec. 🙂
Próbuję szczęścia i liczę na szczęśliwy los.
Zapraszam:
Joanna Węzik
Joa Joanna
Anna Baran

    8 godz.

    Odpowiedz
    Send message
    Ukryj

Edwin Vega Aquino
Razem z Synkiem o nagrodę dla Jego Mamy walczymy 🎁 i szczerze wierzymy, że ją tutaj skutecznie złowimy! 😃
Maximo Fortunato Vega Estrada
Lourdes Aquino Morales
Erika Patricia Vega Aquino
Może być zdjęciem przedstawiającym 1 osoba, niemowlę, zabawka dla dzieci i cukierek

    1 dzień

    Odpowiedz
    Send message
    Ukryj

Iwona Sokołowska
Biorę
Udział
Zapraszam
Beata Szlagor Nowak
Lucyna Pięta
Bernadeta Bomba

    1 dzień

    Odpowiedz
    Send message
    Ukryj

Agnieszka Żurek
❤️❤️❤️❤️❤️Biorę udział ❤️❤️❤️❤️❤️
❤️❤️❤️❤️❤️❤️❤️
Zapraszam
❤️❤️❤️❤️❤️❤️❤️
Anna Dombek
Syla Syla
Monika Frąckowska
❤️❤️❤️❤️❤️❤️❤️❤️❤️❤️❤️❤️❤️❤️❤️❤️❤️❤️❤️❤️❤️❤️❤️❤️❤️❤️❤️❤️❤️
GIF

    2 dni

    Odpowiedz
    Send message
    Ukryj

Marzena Gad
Z ogromną przyjemnością biorę udział i zapraszam do zabawy Karolina Rybicka Martyna Rems Klaudia Kuchta Anna Tomasiuk🌺

    2 dni

    Odpowiedz
    Send message
    Ukryj

Beata Szlagor Nowak
Białe zęby warto w uśmiechu wystawiać,
Znajomych ciekawą rozmową zabawiać.
Cudowny uśmiech to do zaufania wrota,
Na pogawędkę od razu przychodzi ochota!
Dlatego rano i wieczorem zęby szczoteczką szoruję, 🦷🦷🦷
A gdy je wynitkuje od razu się lepiej poczuję.
Cudowna nagroda ♥️🌹♥️🌹♥️ gram z przyjemnością i zapraszam do zabawy i polubienia strony;
Patrycja Chmura
Gabriela Stefek
Jolanta Sembol-Jachym

    2 dni

    Odpowiedz
    Send message
    Ukryj

Elcia Dz
Biorę udział z przyjemnością i zapraszam serdecznie do wspólnej zabawy Magdalena Kwapisz , Natalia Budzyńska , Anna S Paulla ♥️ Gotowe Warunki Spełnione

    2 dni

    Odpowiedz
    Send message
    Ukryj

Maria Joanna
Kocham siebie za siłę i odwagę, aby walczyć o swoje ❤
Zapraszam
Anna Korcz
Zuzanna Korcz
Tomek Byczyński

    15 godz.

    Odpowiedz
    Send message
    Ukryj

Ewelina Sykała
Biorę udział i zapraszam Marzena Bronikowska Anna Sok Ola Ola 🍀

    1 dzień

    Odpowiedz
    Send message
    Ukryj

Gosia Kawula
Biorę udział 🤗🤗🤗🤗🤗🤗🤗🤗🤗🤗🤗🤗🤗🤗🤗 gram 🌺🌺🌺🌺🌺🌺🌺🌺🌺🌺🌺🌺🌺 i zapraszam do zabawy Ania Kawula Kamil Kawula Dominik Kawula Sławek Ka Krzysiek Kawula Krystyna Strojna 🍀❤️🍀❤️🍀❤️🍀❤️🍀❤️🍀❤️🍀❤️🍀❤️🍀❤️🍀❤️🍀❤️🍀❤️🍀❤️🍀❤️🍀❤️🍀❤️🍀❤️🍀❤️

    1 dzień

    Odpowiedz
    Send message
    Ukryj

Emila Kejna
Biorę udział zaproszam Elcia Dz Edyta Pohl Margaretta Jańczak-Zarycka Agnieszka Ewelina Rowka Renia Grocholska Emilia Graczewska

    2 dni

    Odpowiedz
    Send message
    Ukryj

Kinga Kierońska
Biorę udział Danusia Jedlecka Magda Wiejowska Krzychu Kieroński 🙂

    3 dni

    Odpowiedz
    Send message
    Ukryj

Hanna Jędro
Biorę udział i zapraszam ❤️
Karolina Wojewoda Sylwia Szechińska Agnieszka Dąbrowska Justyna Naczk Patrycja Napierała San Dra Marcelina Mazur Małgorzata Goławska ♥️

    9 godz.

    Odpowiedz
    Send message
    Ukryj

Agnieszka Wawrzyniak
Zapraszam 😍
Paul La
Anna Wartalska
Justyna Pawlak 🤩

    12 godz.

    Odpowiedz
    Send message
    Ukryj

Pani Ka
Biore udział 💓💓💓
Zapraszam
Beata Klimek
Lilianna Czaja
Karolina Teresa

    17 godz.

    Odpowiedz
    Send message
    Ukryj

Halina Wieczorek-Prokop
Z wielką ochotą zgłaszam udział w konkursie i zapraszam do konkursu
🍀Waldemar Konietzny
🍀Henryk Cieśla
🍀Ginter Prokop

    18 godz.

    Odpowiedz
    Send message
    Ukryj

Tomasz Sekita
Zapraszam Agnieszka Sekita,Rafał Sekita,Kasia Sekita😀

    19 godz.

    Odpowiedz
    Send message
    Ukryj

Agnieszka Marta Jabłonska
gram i zapraszam Aneta Strecker Anna Sok Monika Zakrzewska

    20 godz.

    Odpowiedz
    Send message
    Ukryj

Ania Borysik
💋💋💋💋💋💋💋💋💋💋💋💋💋💋💋
🎁🎀🎁🎀🎁🎀🎁🎀🎁🎀🎁🎀🎁🎀🎁
Gdy te fantastyczne rozdanie ujrzałam od razu się wpisuję 💁‍♀️❤ bo bym też chciała wygrać🍀 😊🙃🙂 💚.By był 😁 fajny 🎁 ✨na WALENTYNKI dla pary 💏♥️👄 więc i ja przystępuje do zabawy 💖💖💖.
A stronka Duodent Przychodnia Lekarska nam oferuje wspaniałe oferty 😃❣🔥❗️📣
Dlatego postanowiłam próbować sił swych w cudownym rozdaniu 💪❤😚
Szczęście przybywaj do mnie tym razem ❗️❗️❗️😀🍭😁🍀😄💚😃
Mam cichą nadzieję los mi dopisze 😁😀😄😉 jak u znajomych są wygrane za wygraną 😊☺🙂 a u mnie zonk na los 😕😔☹ pechchchchcch by mógł iść 😁😀😃😄 i dopisać szczęście w tym 2025 Roku 🎉✨🎊
Warunki spełnione wszystkie ❤
Zapraszam do zabawy kochane moje......😘😗😙😚
♥️ Olga Ganich
♥️ Ola Jakubiak
♥️ Ola Ola
♥️♥️♥️♥️♥️♥️♥️♥️♥️♥️♥️♥️♥️♥️♥️
👄👄👄👄👄👄👄👄👄👄👄👄👄👄👄

    22 godz.

    Odpowiedz
    Send message
    Ukryj

Małgorzata Rutkowska
Zgłaszam się z wielką przyjemnością🍂🥰
Zapraszam kochane do wspólnej zabawy! Koniecznie zaobserwujcie stronę🦋
Ew… Wyświetl więcej

    1 dzień

    Odpowiedz
    Send message
    Ukryj

Olena Kuchina
Biorę udział 🙂
Zapraszam Artur Wakuła , Aneta Kloc , Tamara Jaskiewicz

    2 dni

    Odpowiedz
    Send message
    Ukryj

Martyna Woj
Biore udział ✨gram✨
Marzenie to jest moje 🩷
Trzymam kciuki aby spełniło się 🩷
Wierze że jeśli pomogę szczęściu,
To uda mi się i ja tez dostanę prezent
Bo marzenia podobno spełniają się 🩷
A ja w to bardzo wierze że kiedyś będzie ten dzień🩷
Zapraszam
Hanna Jędro Aneta Stalinska Kasia Kulczyńska

    2 dni

    Odpowiedz
    Send message
    Ukryj

Anna Tomasiuk
Biorę udział i zapraszam Pola Jarzyńska Magda Matuszewska Krystyna Wasowska🤩

    2 dni

    Odpowiedz
    Send message
    Ukryj

Jolanta Mrożek
Biorę udział Krzysztof Chruślicki , Janina Mrożek, Kinga Kierońska 🙂

    3 dni

    Odpowiedz
    Send message
    Ukryj

Patrycja Weronika Ja-cz
Zapraszam Tomasz Andrzej , Tymon Tomasz Ryczkowski , Marynia Pyrka Fel-k 💖

    3 dni

    Odpowiedz
    Send message
    Ukryj

Aneta Raś
Biorę udział z wielką przyjemnością i zapraszam do zabawy w konkursie 🙂
Dorota Bednarek Elżbieta Kania Monika Mądra
🙂🙂🙂

    3 dni

    Odpowiedz
    Send message
    Ukryj

Agata Blicharska
Biore udzial z wielka przyjemnoscia bo naprawde warto dbac o swoj usmiech zapraszam Paulina Dolecka Paulina Kowalczyk Paulina Białowieżec

    3 dni

    Odpowiedz
    Send message
    Ukryj
    Edytowano

Patrycja Napierała
Biorę udział Alina Freitag Dorota Napierała Daria Michałowska 😍

    4 dni

    Odpowiedz
    Send message
    Ukryj

Kasia Kulczyńska
Z przyjemnością biorę udział zapraszam 🍀💟🍀💟🍀💟🍀💟🍀💟🍀💟🍀💟🍀💟
Beata Wąsik
Beata Pełka
Tomasz Ewski

    4 dni

    Odpowiedz
    Send message
    Ukryj

Meg Mat
Zapraszam Łukasz Kołodziej Agnieszka Gotówko Madzialenka Magda

    15 godz.

    Odpowiedz
    Send message
    Ukryj

Beata Okrój
Zapraszam❤️ Dominika Nikel Ania Lubecka Daria Krefta

    1 dzień

    Odpowiedz
    Send message
    Ukryj

Przemek Paździora
ZAPRASZAM DO ZABAWY Ania Paździora Mario Kempes Agnieszka Zaremba

    1 dzień

    Odpowiedz
    Send message
    Ukryj

Kuba Jacek
Biorę udział i zapraszam
Emilia Zajkowska
Martyna Pierzynka
Bartłomiej Wojtyła

    1 dzień

    Odpowiedz
    Send message
    Ukryj

Dorcia Paulina Sk
Moje marzenie to wygrać biorę udział z chęcią
Tomasz Ewski
Karol Ka
Paulina Karolinka

    1 dzień

    Odpowiedz
    Send message
    Ukryj

Pola Jarzyńska
Zapraszam Anna Fijałkowska Anna Wszołek Paulina Sternak🥰🥰🥰🥰🥰🥰🥰🥰

    2 dni

    Odpowiedz
    Send message
    Ukryj

Krystyna Wasowska
Zgłaszam się i zapraszam Reni Reni Ko Marzena Gad Atewi Ko Ewa Ewa❤💗❤

    2 dni

    Odpowiedz
    Send message
    Ukryj

Kinga Wołek
Zapraszam Przemysław Kusy Wołek,
Andrzej Wołek, Urszula Wołek

    3 dni

    Odpowiedz
    Send message
    Ukryj

Do Ro Ta
Zapraszam Ka Ri Na
Tomasz Kaźmierczak
Tom Asz

    3 dni

    Odpowiedz
    Send message
    Ukryj

Kama Sied
Biorę udział i zachęcam również do wzięcia udziału ciebie Zofia Wojtunik Kamila Ślusarczyk Monika Mądra

    4 dni

    Odpowiedz
    Send message
    Ukryj

San Dra
Z wielką przyjemnością biorę udział w konkursie ❤️
Do zabawy i polubienia strony zapraszam Daria Daria Agnieszka Dąbrowska Justyna Anna Jankowska

    9 godz.

    Odpowiedz
    Send message
    Ukryj

Marzena Nykiel
Zapraszam Mariola Hryc Zuzanna Niemiec Weronika Iwanska

    16 godz.

    Odpowiedz
    Send message
    Ukryj

Karolina Agnieszka Setlak
Zapraszam Monika Brońska Paulina Karpińska Ewa Szumska

    16 godz.

    Odpowiedz
    Send message
    Ukryj

Justyna Iwona Olle
Biore udział zapraszam Elżbieta Kania
Oles Lukasz
Paulina Mianowska
Dorota Katarzyna
Lukasmarcysia Lelitoo
Zaborowscy Michał Paulina

    1 dzień

    Odpowiedz
    Send message
    Ukryj

Elżbieta Świtulska
Zapraszam Kazek Krzysztof Emila Kejna Madzia Florek

    2 dni

    Odpowiedz
    Send message
    Ukryj

Arek Zieliński
biorę udział Michał Orzechowski Kinga Klim Weronika Witkowska

    2 dni

    Odpowiedz
    Send message
    Ukryj

Justyna Justyna
Biore udział
Justyna Uszyńska
Justynaa Łuczka
Justyna Cik
Katarzyna Leja
Luk
Sylwia Ramos
Paulina Białowieżec

    2 dni

    Odpowiedz
    Send message
    Ukryj

Agnieszka Kowalczuk
Zapraszam
Anto Miny
Dagmara Wietrzynska
Paulina Łukasik

    2 dni

    Odpowiedz
    Send message
    Ukryj

Ilona Zielinka
biorę udział
Elzbieta Radziszewska
Agnieszka Prygiel
Mariusz Fudala

    3 dni

    Odpowiedz
    Send message
    Ukryj

Natalia Świergiel
Zapraszam: Elżbieta Klisz Ela Szela Joanna Koniuszy

    13 godz.

    Odpowiedz
    Send message
    Ukryj

Magdalena Zabagło
Biorę udział 🍀❤
Zapraszam do wspólnej zabawy oraz do polubienia strony Monika Kołodziejczyk Marzena Bronikowska Aleksandra Moller
🍀🍀🍀

    1 dzień

    Odpowiedz
    Send message
    Ukryj

Anna S Paulla
Gram gram gram trzymając kciuki zapraszam
Ewa Więckowska
Ewka Ewka
Ewunia Paola
Dorcia Paulina Sk
Paulcia Paulinka
warunki spełnione

    2 dni

    Odpowiedz
    Send message
    Ukryj

Iza Izabela
Zapraszam
Agnieszka Rutkowska
Patrycja Kaczmarek
Katarzyna Walczak Nowara

    2 dni

    Odpowiedz
    Send message
    Ukryj

Nikola Lewandowska
Biorę udział w konkursie 🌸
Arleta Skuratowicz Patrycja Weronika Rojewska Magda Kurtysiak

    22 godz.

    Odpowiedz
    Send message
    Ukryj

Jolanta Znaj
Kocham siebie za to że jestem opiekuńczą mamą i dbam o moje dzieci z całego serca ❤️🙂
Biorę udział
Zapraszam 🌷
Michał Znaj
Marta Potrzebka
Karolina Jod

    23 godz.

    Odpowiedz
    Send message
    Ukryj

Tamara Jaskiewicz
Biorę udział
Amelia Asztemborska
Urszula Kulkowska
Katarzyna Leja

    2 dni

    Odpowiedz
    Send message
    Ukryj

Aneta Kloc
Zapraszam Paula Odrobina Olena Kuchina Bernadeta Anna Agata Aga Olkuska

    2 dni

    Odpowiedz
    Send message
    Ukryj

Krystyna Jeziorska
biorę udział
Anna Lewicka Anna Manthey Beata Wallerin Bartkowska

    3 dni

    Odpowiedz
    Send message
    Ukryj

Adriana Schenk
Biorę udział w zabawie
Zapraszam
Dominika Dróbka
Ania Cygert
Anna Bajer
Barbara Sumorowska
Izabela Cichańska
Izabela Anna Filipczyk

    10 godz.

    Odpowiedz
    Send message
    Ukryj

Adam Rutkowski
Biore udział
Karolina Wu
Karolina Ranosz
Marta Potrzebka
Karolina Zakrzewska
Paulinka Paulcia

    14 godz.

    Odpowiedz
    Send message
    Ukryj

Irena Gondko-Konopka
Biorę udział z okazji urodzin męża zapraszam Teresa Gondko Gosia Mamita Sylwia Olszewska

    12 godz.

    Odpowiedz
    Send message
    Ukryj

Hela Staszyńska
Biorę udział ❤🍀❤
Zapraszam
Anna Gołębiewska
Julianna Stasz
Marta Potrzebka
Bożena Jamróz
Marta Frankowska

    2 dni

    Odpowiedz
    Send message
    Ukryj

Monika Zielińska
biorę udział
Luiza Łagódka Magdalena Stróżyńska Daria Wojciechowska ❤

    3 dni

    Odpowiedz
    Send message
    Ukryj

Ewelina Kotas
Suepr marzęnie wygrać 😍❤️❤️ z Marta Gawęda Keklak Ela Kijek ❤️😘🤪

    1 dzień

    Odpowiedz
    Send message
    Ukryj

Weronika Wisniowska
Biorę udział 😍😍🤩🥰😍
Zapraszam do zabawy 🍀🍀🥰🍀🍀🥰
Lza Hendzel
Zuzanna Wawrzko
Patrycja Wisniowska
Ewelina Undziakiewicz
Wiktoria Chęć
Amelia Pilch
Patrycja Król
Wiktoria Chęć 🍀🥰🍀🍀🥰🍀🍀

    2 dni

    Odpowiedz
    Send message
    Ukryj

Alina Zarzycka
Zapraszam Iwona Nieściór Elwira Kołtun Natalia Rybak

    18 godz.

    Odpowiedz
    Send message
    Ukryj

Agnieszka Michalska
Biorę udział Beata SzczawińskaUrszula WyEwelina Kotas

    2 dni

    Odpowiedz
    Send message
    Ukryj

Sara Szepler
Biorę udział i zapraszam Kamil Szepler Wiktoria Rozalia Szabla Klaudia Szabla

    11 godz.

    Odpowiedz
    Send message
    Ukryj

Karolina Wojewoda
Biorę udział ❤️ Zapraszam Katarzyna Leja Monika Wlazlo Jolanta Znaj

    9 godz.

    Odpowiedz
    Send message
    Ukryj

Lidia Aleksandra Ciopala
Biorę udział zapraszam Renata Chrpyt Paula Fudro Anna Niezgódka

    9 godz.

    Odpowiedz
    Send message
    Ukryj

Asia Walczyk
Biorę udział zapraszam Madzia Florek Bernadeta Bomba Lucyna Pięta

    10 godz.

    Odpowiedz
    Send message
    Ukryj

Danuta Mamczur
Biorę udział 😍👍
Zapraszam
Paulcia Paulinka
Anna Gołębiewska
Urszula Wy

    11 godz.

    Odpowiedz
    Send message
    Ukryj

Joanna Burchacka
Biorę udział ! 🎁🎁🎁 Zapraszam Karolina Warczygłowa Elżbieta Andrzejewska Paula Prus

    13 godz.

    Odpowiedz
    Send message
    Ukryj

Maja Anna
Bawię się z Duodent Przychodnia Lekarska 🎉
Zapraszam do zabawy
Elżbieta Bujko Sylwia Wilamowska Beata Wąsik

    13 godz.

    Odpowiedz
    Send message
    Ukryj

Beata Malinowska
Biorę udział zapraszam Anna Bendyk
Liliana Białkowska
Edward Warszawski
❤️🎁❤️🎁❤️🎁❤️

    16 godz.

    Odpowiedz
    Send message
    Ukryj

Małgorzata Goławska
Biorę udział I zapraszam Monika Błaszczuk Monika Woźniak Magdalena Makierska Karolina Kobiecińska

    16 godz.

    Odpowiedz
    Send message
    Ukryj

Elżbieta Kania
Biorę udział 💖💖💖
Zapraszam do zabawy
Anna D. Łopot
Beata Pełka
Edyta Myśliwiec

    22 godz.

    Odpowiedz
    Send message
    Ukryj

Agata Curyło
Biorę udział ❤️
Zapraszam
Aga Mróz
Karo Bała
Beata Szlagor Nowak

    23 godz.

    Odpowiedz
    Send message
    Ukryj

Ewa Więckowska
Biorę udział zapraszam
Klaudia Owsianka
Skrobek Paulina
Ewka Ewka

    1 dzień

    Odpowiedz
    Send message
    Ukryj

Sylwia Wilamowska
♥️♥️♥️♥️ biore udział zapraszam do zabawy Agata Aga Olkuska Maja Anna Gosiaa Gosiaa

    1 dzień

    Odpowiedz
    Send message
    Ukryj

Buszek Agnieszka
Zoé Fournié Agnes Agnes Kowalska Agnieszka

    1 dzień

    Odpowiedz
    Send message
    Ukryj

Kowalska Agnieszka
Dorota Szybiak
Klaudia Piwek
Klaudia Szubińska
Zapraszam

    2 dni

    Odpowiedz
    Send message
    Ukryj

Aga Dra
Biorę udział 🥰🎁, zapraszam Bożena Długajczyk Agata Aga Olkuska Edyta Pohl ❤️❤️❤️❤️❤️

    2 dni

    Odpowiedz
    Send message
    Ukryj

Joanna Kozera
Biorę udział i zapraszam Karolina Rybicka Monika Szczypczynska Iwona Pietryszyn Iwona Pietryszyn🌷🌷🌷

    2 dni

    Odpowiedz
    Send message
    Ukryj

Magdalena Gałycz
Biorę udział
Zapraszam
Patrycja RduchIzabela KozińskaKatarzyna Krajanowska

    2 dni

    Odpowiedz
    Send message
    Ukryj

Ewa Gudz
Z wielką przyjemnością biorę udział i zapraszam
Czesław Czesław
Kamila Gudz
Andrzej Gudz
Megie Margo
Brak dostępnego opisu zdjęcia.

    2 dni

    Odpowiedz
    Send message
    Ukryj

Monika Karpik
🎉.... ....🎉
.......💋💞💢💫❤️‍🔥💫💢💞💋........
.......💌🩷 Biorę udział 🩷💌........
.......💋💞💢💫❤️‍🔥💫💢💞💋........
🎉.... ....🎉 Zapraszam..... Elżbieta Dziukiewicz Agata Blicharska Plik Martin
Może być zdjęciem przedstawiającym serce

    2 dni

    Odpowiedz
    Send message
    Ukryj

Agnieszka Lis
Biorę udział
❤❤❤
Zapraszam
Anna Jedynak
Marcin Lis
Andrzej Jedynak

    2 dni

    Odpowiedz
    Send message
    Ukryj

Renia Grocholska
Biorę udział ❤🍀
Zapraszam do zabawy
Bernadeta Bomba
Anna Bajer
Anna Sok

    2 dni

    Odpowiedz
    Send message
    Ukryj

Dagmara Wietrzynska
Biorę udział
Zapraszam
Beata Szlagor Nowak
Bernadeta Bomba
Agnieszka Kowalczuk
Może być zdjęciem przedstawiającym zaćmienie, ocean, horyzont i zmierzch

    2 dni

    Odpowiedz
    Send message
    Ukryj

Barbara Furtak
Z przyjemnością biorę udział zapraszam 🍀
Andrzej Banach Krystyna Helt Kamila Kielesińska

    3 dni

    Odpowiedz
    Send message
    Ukryj

Agnieszka SuRyl
🪽🪽🪽🪽🎄🌟🍀✅️❄️☃️❤️😊✨️✨️Biorę udział✨️✨️☺️🎄☃️🍀❄️✅️🎄🪽🪽🪽🪽
..🍀🌫😊❤️🪽🪽🪽🪽🪽🪽🌫🍀..
✅️✅️✅️ Zapraszam Agata Blicharska Wiesława Brodowska Plik Martin

    3 dni

    Odpowiedz
    Send message
    Ukryj

Jadwiga Gałycz
Biorę udział
Zapraszam
Włodzimierz Gałycz Mateusz Gałycz Magdalena Gałycz

    3 dni

    Odpowiedz
    Send message
    Ukryj

Zuzanna Knapik
😘😘😘 Biorę udział
Zapraszam
Madzia Kozlowska
Izabela Cichańska
Iwona Stefańska

    3 dni

    Odpowiedz
    Send message
    Ukryj

Rafał Faleński
Biorę udział.
Zapraszam
Lucyna Kmiecik
Karol Ka
Krystian Kubik

    3 dni

    Odpowiedz
    Send message
    Ukryj

Paulina Dolecka
Biorę udział
Zapraszam
Paulina Krzysiak
Agata Górska
Agata Blicharska
♥️♥️♥️

    4 dni

    Odpowiedz
    Send message
    Ukryj

Paulina Ostrowska
Damian Ostrowski
Sylwia Korytkowska
Katarzyna Woźniak
❤️🩷❤️🩷

    1 dzień

    Odpowiedz
    Send message
    Ukryj
"""



lajki_posta_ig = """ksenia_wrzosek
natalia_swic
gawlowskamariola
masurian_blissgirl
hope__nope
n.lezuchowska
marti.nikaa
nugu.best
sasiiixx
do_travel_too
pamela_lta
polskalasem
damianmoroz
xxbarmell
kawkazeesmietanka
czytam.powiesci
instytut.glosu.i.mowy
daniel.oli.maja
jutrobedziemyszczesliwi
hi.panorama
ann_kkowa
martynabee_
bl0ndpanidomu
mamamikusia89
krystyna.krysiunia
martasaputa
kupiec.marcin
m_o_n_i_k_a_ewa
m.piwonia
natalia.tomkiewicz
lusiak91
nuurcia
podrozowiec
britney__perry
amelialozg
viktorvolkov
mifeks1983
its_spider
marakuja1212
michellakej
milenaszubert
xxallema
itwas_may_
gabrysqaj
majkrzakewelina
ulia92022
karolinakaspro
plysiek
malgorzatatl
margaretquaa
agatshia
bebka0
agaaww12
martul12
balumbalum_pyszak
dwertos
myszojshimi
danuta.nowak.336717
san_divaa
majewska7008
szeherezadka
justynarub
_dorcia1980
ann.ka62
sochockanatalia
czerwoneszpile
ola_manolaaa
karo.linaa005
dymkowska.j
paulina.malmur.fizjo
kobackakatarzyna
anna_holcka
robertpilatowicz
defugda
plotherapy_
ejsnerx
pilatowicz_
roseblue900
londonparissss
girl96non1998
halina_karpinska_nieruchomosci
julia_mroz1
irinav_u
czapla__paulina
karolina_strachota
sokolowsskaa
mstrachotka
dominika_czapla
higienistka_by
alpazc_atyde
amandababalija
jablonska_a._
ela.t0m
xlittlewhitelie
sakovska.m
krisisz
p_parys
kasiaa_wer
kamilavolska
hipa6970
dorotaswistek
lololololooooolll
daintylandii
natalqap
chiquitka
bednasia
agataszymikowska
ka.tarzyna886
wiczka63
agata_krynicka
claudia_alicjaa
marlenkamc
mozdzonek.m
dawid.szulta
adriana_michalowska
frelinii
m.chmielnicki
julka.julita.b
juliett_michalowska
adamowskangelika
joanna_melzacka
radek.official_
sakowska
salaterka223
elarosik
harelikava_tatsiana
wika_1210
higienistka_dominika__debowska
fylyp121
olalegeza
mo.nika_legeza
tomaszewskaad
madallenne
anjan_anjan123
aleksandra.madrak
anulaaa_s
a_u_r_e_ola
deedee_domka
olka_mazur
duodentbielany
ellaa_babuttt
patrycjakitaa
x_xkamil_x_x
"""



lajki_posta_fb = """DMD Domy
Duodent Przychodnia Lekarska
Kinga Kierońska
Patrycja Wieczorek
Danuta Kosinska
Małgorzata Sawka
Jolanta Warszawska
Edward Warszawski
Agnieszka Pyć
San Dra
Karolina Wojewoda
Hanna Jędro
Mariusz Szopa
Lidia Aleksandra Ciopala
Agnieszka Dąbrowska
Agnieszka Wąsowska
Dominika Dębowska
Justyna Bacławska
Adriana Schenk
Dorota Ł. Szopa
Katarzyna Bajda
Asia Walczyk
Anna Wartalska
Danuta Mamczur
Sara Szepler
Alicja Janc
Agnieszka Wawrzyniak
Irena Gondko-Konopka
Dorota Sycha
Bernadeta Pawłowska
Joanna Burchacka
Andrzej Gdanski
Stanisław Małgorzata Kieta
Natalia Świergiel
Maja Anna
Elżbieta Dziukiewicz
Krzysiek Dabrowski
Zaborowscy Michał Paulina
Dorota Ewa Szweda
Elżbieta Tomaszewska
Adam Rutkowski
Beata Sandra Gal
Ela Grudnik
Anita Brzdęk
Meg Mat
Maria Joanna
Józef Durka
Marzena Nykiel
Martyna Koczorowska
Beata Malinowska
Małgorzata Goławska
Karolina Agnieszka Setlak
Ola Mazur
Łukasz Kijek
Pani Ka
Alina Zarzycka
Halina Wieczorek-Prokop
Stanisław Grocholski
Dawid Szaboranin
Tomasz Sekita
Piotr Wojciechowski
Agnieszka Marta Jabłonska
Aneta Stalinska
Ewa Ewa
Przemek Pe
Sandra P-ka
Sandra Malina
Judyta Pati
Ewa Kawczyńska
Arkadiusz Potek
Filip Nowakowski
Nikola Lewandowska
Ania Borysik
Elżbieta Kania
Aleksandra Trafisz
Jolanta Znaj
Agata Curyło
Paulina Mianowska
Beata Okrój
Barbara Paździora
Ewelina Sykała
Przemek Paździora
Barbara Nowak
Mariusz Paździora
Paulina Ostrowska
Ewa Więckowska
Aleksandra Dopierała
Daria Cieszyńska-Bladowska
Bogdan Czerwiński
Edwin Vega Aquino
Krysia Bryzik
Klaudia Piwek
Dorcia Paulina Sk
Małgorzata Cichoń
Kuba Jacek
Patrycja Libner
Ewunia Paola
Anna Fijałkowska
Paulcia Paulinka
Jadwiga Kasia Wierzba
Patrycja Winowiecka
Sylwia Wilamowska
Iwona Sokołowska
Danusia Kujawska
Stanisława Wawrzyk
Gosia Kawula
Alicja Stettner
Magdalena Zabagło
Joanna Asia
Justyna Iwona Olle
Stanislaw Wydra
Buszek Agnieszka
Halinka De
Klaudia Karina Chylińska
Ewelina Kotas
Kwiatek Łukasz
Weronika Wisniowska
Hela Staszyńska
Kazek Krzysztof
Agnieszka Michalska
Kowalska Agnieszka
Małgorzata Rutkowska
Aga Dra
Agnieszka Żurek
Pola Jarzyńska
Elżbieta Świtulska
Tamara Jaskiewicz
Margaretta Jańczak-Zarycka
Emila Kejna
Joanna Kozera
Małgorzata Warmbier
Marzena Gad
Krystyna Wasowska
Magdalena Gałycz
Lucyna Kmiecik
Anto Miny
Ewa Gudz
Katarzyna Dębicka
Anna S Paulla
Ania Dudkowiak
Stefania Kupczak
Aneta Kloc
Beata Szlagor Nowak
Monika Karpik
Olena Kuchina
Beata Szczawińska
Arek Zieliński
Natalia Kostro
Agnieszka Lis
Skibinska Aga
Kinga Jędzura
Justyna Justyna
Elcia Dz
Renia Grocholska
Maria Sakowska
Dagmara Wietrzynska
Agnieszka Kowalczuk
Martyna Woj
Iwona Skorek
Agnieszka Rutkowska
e-Konkursy.info - o krok od wygranej...
Justyna Zejfert
Anna Tomasiuk
Iza Izabela
Plik Martin
Oles Lukasz
Aleksandra Deputat
Kinga Wołek
Barbara Furtak
Ilona Zielinka
Krystyna Jeziorska
Monika Zielińska
Adrianna Fliszewska
Magdalena Sakowska
Jolanta Mrożek
Krzysztof Szpejna
Magdalenka Uroda
Natalia Skrzyniarz
Agnieszka SuRyl
Małgorzata Cee
Patrycja Weronika Ja-cz
Tomasz Kaźmierczak
Do Ro Ta
Monika Monia Kalista
Joanna Czardyban
Aneta Raś
Paulina Malmur
Marzena Gujska
Marlena Staropiętka
Jadwiga Gałycz
Zuzanna Knapik
Justyna Lech Gajek
Sylwia Ramos
Bernadeta Bomba
Agata Blicharska
Magdalena Kozłowska
Rafał Faleński
Paulina Karolinka
Beata Włodarczyk
Karol Ka
Michał Konecz
Joanna Dąbrowska
Agnieszka Kruszewska
Magdalena Magdalena
Patrycja Napierała
Konrad Goszczyński
Amn Tree
Alicja Zygadło
Kama Sied
Barbara Jajko
Paulina Dolecka
Beata Barbara
Anna Myszak
Karolina Kowalewska
Ola Legęza
Monika Legęza
Magda Lis
Fred Graf
Kasia Kulczyńska
Tomasz Ewski
Natalia Rutkowska
Pat Ka
Mariola Dębowska
Ola Katarzyna Król
Sylwia Żmuda
Marta Martucha
"""



followers_ig = """ochenka_jd
basix_420
misioweglupotki
ola283339
berezinska
verkosia_priv
ksenia_wrzosek
natalia_swic
gawlowskamariola
masurian_blissgirl
hope__nope
n.lezuchowska
ewapotyrcha
marti.nikaa
zmuda8436
maggie81iewa
sasiiixx
do_travel_too
pamela_lta
polskalasem
damianmoroz
xxbarmell
kawkazeesmietanka
czytam.powiesci
angelika.n20
instytut.glosu.i.mowy
daniel.oli.maja
dutyloop
jutrobedziemyszczesliwi
hi.panorama
ann_kkowa
martynabee_
bl0ndpanidomu
mamamikusia89
victoure_x3
arutkowski77
dorksien
dortento
mastergreenpeas
krystyna.krysiunia
martasaputa
kupiec.marcin
m_o_n_i_k_a_ewa
m.piwonia
natalia.tomkiewicz
lusiak91
nuurcia
justynaczarn
domek_slodki_domek
milkmoxha
podrozowiec
beatkamala
britney__perry
amelialozg
oliwkowy_groszek
viktorvolkov
matuszewskyyy
mifeks1983
its_spider
marakuja1212
pijana91
artdeecoo
michellakej
wtulonawsny
Iwona Matelska
milenaszubert
xxallema
renata12ca
itwas_may_
_aalice.z_
gabrysqaj
bebuszka_
majkrzakewelina
ulia92022
niebieskiemigdaly
karolinakaspro
hanabiranoyouni
plysiek
pilkers_pilkers
natka0097_lm
malgorzatatl
margaretquaa
agnieszka.rutkowska.50159
agatshia
bebka0
martul12
balumbalum_pyszak
dwertos
myszojshimi
Peacemeki
danuta.nowak.336717
majewska7008
defugda
szeherezadka
justynarub
_dorcia1980
ann.ka62
sochockanatalia
czerwoneszpile
ola_manolaaa
karo.linaa005
paulina.malmur.fizjo
anna_holcka
kiniu_siaa
plotherapy_
ejsnerx
pilatowicz_
roseblue900
radek.official_
londonparissss
girl96non1998
julia_mroz1
karolina_strachota
sokolowsskaa
_lukasz_lukasz90
Łukasz_Łukasz
alpazc_atyde
E.Z
pablitoo_official
Paweł Gliński-Waniewski
ela.t0m
Elżbieta Tomaszewska
xlittlewhitelie
𝓸𝓵𝓲𝓿𝓲𝓪
jablonska_a._
Ola
sakovska.m
krisisz
Krzysztof Szpejna
dr_fat_ninja
T_King
p_parys
Paris
kasiaa_wer
Katarzyna Pieczarowska
kamilavolska
Kamcia🩷
hipa6970
Hubert Kordek
lololololooooolll
Angelika Ostrowska
daintylandii
𝓭𝓪𝓲𝓷𝓽𝔂𝓵𝓪𝓷𝓭𝓲𝓲
natalqap
Natalia Przestrzelska
anna.jeziorowska80
Anna Jeziorowska
chiquitka
Monitshka
bednasia
Joanna.
agataszymikowska
agata
ka.tarzyna886
Katarzyna
agata_krynicka
Agata Krynicka
marekpopowskiphoto
Marek Popowski Photography | Fotografia & Video |
claudia_alicjaa
Claudia Alicja
marlenkamc
Marlenn
dawid.szulta
dawid
bozena_michalowska
Bożena Michałowska
adriana_michalowska
Adriana Michałowska
frelinii
julka.julita.b
Julita Justyna Bisko
adamowskangelika
joanna_melzacka
asia
salaterka223
Łukasz Salata
sylwia_zj
Sylwia Jaworska
wika_1210
Wiktoria Błaszkiewicz
madallenne
Magdalena Strachota
tomaszewskaad
Dominika Tomaszewska
fylyp121
Filip Nowakowski
mozdzonek.m
Mateusz Możdżonek
x_xkamil_x_x
Kamil Babut
halina_karpinska_nieruchomosci
Halina Karpińska
goslawa.i
Gosia
lejszysbc_strategbiznesu_
Dagmara Lejszys |Ekspert biznesu medycznego.Szkolenia.Strategia.
higienistkawpigule
Higienistka stomatologiczna, mgr pielęgniarstwa Ania
pracowniaortodruciaki
DRUCIAKI
anna.kita.71
Anna Kita
malgorzatagorabialek
Małgorzata Góra Białek
ewagaczek
Ewa Gaczek
beata_krawczynska
Beata Krawczyńska
zmudaprzem
paplania
Patrycja Paplak
anulaaa_s
Anulaaa
kocinska_k
Klaudia Kuśnierz
dmddomy
DMD
higienistka_by
Стоматолог-гигиенист Варшава
duodent_przychodnia
Duodent Przychodnia Stomatologiczna
zmudasyl
madziaaa_98
Magdalena Łuczak-Tabaka
dr_magdalenaluczak
lek.dent. Magdalena Łuczak-Tabaka • Medycyna Estetyczna 💉
superasna
harelikava_tatsiana
Татьяна Гореликова
suchy_rr
FILT
rakmag19
Magdalena Rakowska
xwlodar
Wojciech
uszataa
marcela_legeza
mo.nika_legeza
Monika
_justyna.m_
Justyna M
grabtomski
Tomek Grabowski
m.chmielnicki
aleksandra.madrak
Ola Madrak
eliza.strakhanova
LIZA STRAKHANOVA🤍
wkanownik
Weronika Kanownik
juliett_michalowska
juliett_michalowska
jedzurakinga
Kinga
higienistka_dominika__debowska
ŚlicznaHigieniczna
olalegeza
Ola Legęza
wiczka63
Wiktoria Nowakowska
a_u_r_e_ola
Ola Król
olka_mazur
Ola Mazur
allizyyy
Aliz
kamilacza
Kamila Czapla
sakowska
Magdalena✨
patrycjakitaa
Patii
deedee_domka
🧡D O M KA 🧡
"""



followers_fb = """Małgorzata Sawka
Jolanta Warszawska
Edward Warszawski
Agnieszka Pyć
San Dra
Karolina Wojewoda
Hanna Jędro
Mariusz Szopa
Lidia Aleksandra Ciopala
Agnieszka Dąbrowska
Agnieszka Wąsowska
Justyna Bacławska
Adriana Schenk
Asia Walczyk
Anna Wartalska
Danuta Mamczur
Sara Szepler
Irena Gondko-Konopka
Dorota Sycha
Bernadeta Pawłowska
Stanisław Małgorzata Kieta
Maja Anna
Krzysiek Dabrowski
Zaborowscy Michał Paulina
Meg Mat
Maria Joanna
Józef Durka
Beata Malinowska
Małgorzata Goławska
Pani Ka
Alina Zarzycka
Stanisław Grocholski
Halina Wieczorek-Prokop
Dawid Szaboranin
Katarzyna Bokisz
Paulina Ostrowska
Agnieszka Marta Jabłonska
Przemek Pe
Sandra Malina
Ewa Kawczyńska
Arkadiusz Potek
Ania Borysik
Elżbieta Kania
Agnieszka Rutkowska
Aleksandra Trafisz
Jolanta Znaj
Agata Curyło
Paulina Mianowska
Beata Okrój
Ania Paździora
Ewelina Sykała
Przemek Paździora
Barbara Nowak
Mariusz Paździora
Ewa Więckowska
Daria Cieszyńska-Bladowska
Bogdan Czerwiński
Edwin Vega Aquino
Magdalena Zabagło
Krysia Bryzik
Klaudia Piwek
Dorcia Paulina Sk
Magda Lis
Patrycja Libner
Agata Szkołut
Ewunia Paola
Anna Fijałkowska
Jadwiga Kasia Wierzba
Stanisława Wawrzyk
Gosia Kawula
Wiktoria Nowaczyk
Justyna Iwona Olle
Stanislaw Wydra
Halinka De
Kwiatek Łukasz
Hela Staszyńska
Kazek Krzysztof
Agnieszka Michalska
Kowalska Agnieszka
Małgorzata Rutkowska
Pola Jarzyńska
Elżbieta Świtulska
Tamara Jaskiewicz
Margaretta Jańczak-Zarycka
Emila Kejna
Joanna Kozera
Marzena Gad
Krystyna Wasowska
Magdalena Gałycz
Ania Dudkowiak
Beata Szczawińska
Beata Szlagor Nowak
Monika Karpik
Patrycja Słabik
Arek Zieliński
Leszek Wawrzyniecki
Agnieszka Lis
Justyna Justyna
Elcia Dz
Renia Grocholska
Martyna Woj
Iwona Skorek
Anna Tomasiuk
Iza Izabela
Plik Martin
Oles Lukasz
Barbara Furtak
Ilona Zielinka
Krystyna Jeziorska
Jolanta Mrożek
Krzysztof Szpejna
Magdalenka Uroda
Agnieszka SuRyl
Patrycja Weronika Ja-cz
Tomasz Kaźmierczak
Do Ro Ta
Joanna Czardyban
Aneta Raś
Jadwiga Gałycz
Zuzanna Knapik
Justyna Lech Gajek
Sylwia Ramos
Bernadeta Bomba
Agata Blicharska
Magdalena Kozłowska
Rafał Faleński
Paulina Karolinka
Karol Ka
Michał Konecz
Agnieszka Kruszewska
Kama Sied
Barbara Jajko
Paulina Dolecka
Chatyna
Kasia Kulczyńska
Tomasz Ewski
Pat Ka
Jolanta Chojecka
Elżbieta Kujko
Gosia Szafraniec
Michał Formatyk
Gracjana Gracjanka
Beata Błażejewska
Małgorzata Ciborowska
Hubert Porębski
Seba Stian
Sławomir Kamola
Dariusz Grin-Zuchowski
Marta Pytlarz
Kinga Kosciewicz
Mariusz Medalik
Irena Kowalewska
Paulina Domżalska
Martyna M Górecka
Renata Lubiankowska
Paulina Piesiewicz
Katarzyna Kuty
Małgorzata Płomińska
Mieszko Nowakowski
Amn Tree
Agnieszka Pająk
Robert Nowakowski
Magda Kiliś
Julka Kobacka
Paulina Malmur
Agata Gierałtowska
Monika Nowakowska
Julia Kalinowska
Magdalena Odziemczyk
Łukasz Tabaka
Kasia Kasiunia
Magdalena Ratajczak Tehrani
Ola Mazur
Michał Włodarczyk
Kamila Pasławska
Iwona Kacprzak
Sylwester Palka
Grzegorz Ryszard
Agnieszka Popkiewicz
Sylwia Betko
Wiktoria Nowakowska
Ewa Gaczek
Dominik Pawlak
Magdalena Papińska
Halina Karpińska
Piotr Salwa
Krystyna Kiszelewska-Kotyńska
Arletta Romanska
Marek Popowski
Radoslaw Bogusiak
Krzysiek Szymczak
Lech Skwarski
Jacek Wojcieski
Mariusz Wołodko
Małgosia Kraska
Anna Jancewicz
Natalia Wawrzeńczyk
Jan Kazimierz Siwek
Gabrysia W-k
Jan Moszczynski
Marzena Chraniuk
Staś Borzecki
Paulina Nowaczek
Anna Jędruch
Anna Śmiechowska
Jadzia Lewandowska
Jerzy Witkowski
Marcin Dolota
Teresa Fojer
Marcin Sikora
Olena Korchynska
Małgorzata Rusztecka
Kacper Kowalski
Ewelina Chrzanowska
Elżbieta Żądełek
Joanna Zabłocka
Seweryn Dymkowski
Maciej Marszałkiewicz
Milena Krawętkowska
Bozenna Józefowicz
Hubert Niewiadowski
Agnieszka Fedorowicz
Marcin Johny
Martyna Dyga
Aneta Janiszewska
Olga Burzyńska
Beata Kwiatkowska
Aleksandra Bukalska
Anna Urbaniak
Sylwia Burzyk
Justyna Płuciennik
Любовь Тишковец
Zośka Kurzaj
Ola Jałonickia
Krzysztof Bator
Nata Prima
Krzysztof Senktas
Anatol Liakishev
Jerzy Biaduń
Dominika Majcher
Przemek Kobacki
Cezary Kwiatkowski
Andrzej Gromek
Anna Łukasiewicz
Kasia Os
Joanna Orzechowska
Karolina Tarasek
Marta Jogunica
Dominika Ogonowska
Monika Molska
Katarzyna Janowska Pudlo
Renata Boniecka
Mariusz Zawadzki
Tomasz Laskowski
Jarosław Starowicz
Izabela Porębska
Marta Dudzińska
Ula Wicher
Dawid Bracik
Bartłomiej Pawiński
Oliwia Lewandowska
Iza Białek
Monika Stanislawska
Kamil Studzianek
Beata Puchcińska
Kamila Wasiak
Irena Ciesielska
Katarzyna Żmuda
Dariusz Pęczkowicz
Kinga Wołek
Agnieszka Głozak
Patrycja Bykowska
Kinga Kralik Kwiatkowska
Laura Głowińska
Anna Tomczyk
Maria Borkowska
Katarzyna Tyszkiewicz
Justyna Miecznikowska
Mateusz Lech
Norbert Kruk
Małgorzata Krzemień
Mariola Malczewska
Dariusz Rutkowski
Maia Wisniewska
Yulia Myts
Monika Luganska
Katarzyna Podołowska-Błądek
Diana Kulej-Janiszewska
Berkowska Wioletta
Piotr Grochowski
Kamila Kalińska
Paulina Jensen
Urszula Kurowska
Monika Omes-Kurowska
Joanna Mazur-Różycka
Karina Górecka-Zreda
Renata Rydzewska Henriques
Basia Basia
Paweł Kuty
Kuba Szymanowski
Natalia Reucka
Maryla Lech
Paweł Wąs
Karolina Blanka Zawadka
Izabela Mociak-Laskowska
Albin Sławiński
Jan Pio
Jolanta Zach
Marzena Dobrogosz
Agnieszka Wojciechowska
Krzysio Włodarczyk
Sara Shamsa
Patrycja Krawczak
Ślepecki Artur
Mateusz Woś
Marcin Żbik
Bartosz Lech
Aneta Przedpełska
"""

dict_instagram_comments = parse_instagram_comments(komentarze_instagram)
dict_facebook_comments = parse_facebook_comments(komentarze_facebook)
list_lajki_posta_ig = lajki_posta_ig.split()
list_lajki_posta_fb = lajki_posta_fb.split()
list_followers_ig = followers_ig.split()
list_followers_fb = followers_fb.split()

uczestnicy_ig = [
    author_ig for author_ig in dict_instagram_comments
    if author_ig in list_lajki_posta_ig and author_ig in list_followers_ig
]

uczestnicy_fb = [
    author_fb for author_fb in dict_facebook_comments
    if author_fb in list_lajki_posta_fb and author_fb in list_followers_fb
]

zwyciezca_fb = None
zwyciezca_ig = None

@app.route('/admin/losowanie')
def drawing_of_competition_results():
    if not session.get('username'):
        return redirect(url_for('index'))

    if not direct_by_permision(session, permission_sought='administrator'):
        return redirect(url_for('index'))

    return render_template(
        "drawing_of_competition_results.html", 
        uczestnicy_fb=uczestnicy_fb, 
        uczestnicy_ig=uczestnicy_ig, 
        zwyciezca_fb=zwyciezca_fb, 
        zwyciezca_ig=zwyciezca_ig
    )

@app.route('/admin/losuj', methods=['POST'])
def losuj():
    if not session.get('username'):
        return jsonify({"success": False, "message": "Brak wymaganych uprawnień!"}), 403

    if not direct_by_permision(session, permission_sought='administrator'):
        return jsonify({"success": False, "message": "Brak wymaganych uprawnień!"}), 403

    global zwyciezca_fb, zwyciezca_ig

    platforma = request.json.get('platform')

    if platforma == "fb" and uczestnicy_fb:
        zwyciezca_fb = random.choice(uczestnicy_fb)
    elif platforma == "ig" and uczestnicy_ig:
        zwyciezca_ig = random.choice(uczestnicy_ig)

    return jsonify({"zwyciezca_fb": zwyciezca_fb, "zwyciezca_ig": zwyciezca_ig})


# Kontakt
# Strona kontaktu
@app.route('/kontakt-z-przychodnia-stomatologiczna', methods=['GET'])
def contact_page():
    session['page'] = 'kontakt'
    pageTitle = 'Kontakt z przychodnią stomatologiczną'
    return render_template('contact.html', pageTitle=pageTitle)



@app.route('/umow-wizyte-online', methods=['GET'])
def book_appointment_page():
    session['page'] = 'umow_wizyte_online'
    pageTitle = 'Umów wizytę online'
    return render_template('book_appointment.html', pageTitle=pageTitle)



















# ========================================================================================= #
#  ENDPOINTY DYNAMICZNE
#  
#  Obsługa generowania treści dynamicznej:
#  - Renderowanie stron HTML na podstawie szablonów.
#  - Personalizacja treści w oparciu o dane użytkownika.
#  - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -  
#  Wymagają odpowiedniego zabezpieczenia przed atakami XSS i CSRF.
# ========================================================================================= #


@app.route('/zabieg-stomatologiczny/<path:treatment_slug>')
def treatment_dynamic(treatment_slug):
    
    treatments_dict = {item["ready_route"]: item["tytul_glowny"] for item in treatments_db(False)}
    if treatment_slug in treatments_dict:
        pageTitle = treatments_dict[treatment_slug]
        session['page'] = treatment_slug

        treatmentOne = treatments_db_all_by_route_dict(True, treatment_slug)
        treatmentOne['prizeTableSync'] = []
        desc, prizes = validatorZip(treatmentOne['page_price_table_content_list_comma_section_5'][0], 
                                    treatmentOne['page_price_table_content_list_comma_section_5'][1])
        for item in zip(desc, prizes):
            treatmentOne['prizeTableSync'].append(item)
        
        treatmentShortly = treatments_db(True)
        treatmentOne['treatmentShorts'] = []
        i=0
        for item in treatmentShortly:
            if 'tytul_glowny' in item:
                if item['tytul_glowny'] != treatments_dict[treatment_slug]:
                    treatmentOne['treatmentShorts'].append(item)
                    i+=1
            if i==3: break
        treatmentOne['icon_id'] = 0
        if treatmentOne.get('icon'):
            treatmentOne['icon_id'] = iconer_changer_by_neme.get(treatmentOne.get('icon'), 0)
            
        return render_template(
            'treatment_details.html',
            # 'labo_one.html',
            pageTitle=pageTitle,
            nazwa_uslugi=treatments_dict[treatment_slug],
            treatmentOne=treatmentOne
        )
    else:
        abort(404)


@app.route('/dokumenty/<path:filename>')
def download_file(filename):
    # Sprawdź, czy plik istnieje w katalogu
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)
    else:
        # Zwróć błąd 404, jeśli plik nie istnieje
        abort(404)



@app.route('/zespol/<string:name_pracownika>')
def team_mambers(name_pracownika):
    DYNAMIC_team_memeber_dict = team_memeber_router()
    DYNAMIC_team_memeber_dict_id = DYNAMIC_team_memeber_dict.get('by_id', {})
    if name_pracownika in DYNAMIC_team_memeber_dict_id:
        idPracownika = DYNAMIC_team_memeber_dict_id[name_pracownika]
        member_data_prepared = [member_data for member_data in generator_userDataDB() if member_data['id'] == idPracownika]

        if member_data_prepared:
            member_data_prepared = member_data_prepared[0]

            # Sprawdzanie uprawnień
            # ========================================================
            # 🌟 Model implementacji uprawnień - Rekomendacja 🌟
            # Ten kod jest czytelny, modułowy i łatwy w rozbudowie.
            # Każdy poziom uprawnień ma jasno określoną logikę.
            # Użycie funkcji `direct_by_permision` zapewnia elastyczność.
            # Idealne do zastosowania w wielu endpointach systemu!
            # ========================================================
            if session.get('username', False):
                if direct_by_permision(session, permission_sought='administrator'):  # Administrator
                    # Usuń tylko hasło i salt
                    member_data_prepared.pop('password', None)
                    member_data_prepared.pop('salt', None)
                elif direct_by_permision(session, permission_sought='super_user'):  # Super user
                    # Usuń hasło, salt i uprawnienia
                    member_data_prepared.pop('password', None)
                    member_data_prepared.pop('salt', None)
                    member_data_prepared.pop('uprawnienia', None)
                elif direct_by_permision(session, permission_sought='user'):  # Pracownik
                    # Usuń wybrane dane
                    keys_to_remove = ['password', 'salt', 'uprawnienia', 'email', 'login', 'contact', 'status_usera']
                    for key in keys_to_remove:
                        member_data_prepared.pop(key, None)
                else:
                    # Brak innych uprawnień - usuń cały pakiet
                    keys_to_remove = ['password', 'salt', 'contact', 'uprawnienia', 'email', 'login', 'contact', 'status_usera']
                    for key in keys_to_remove:
                        member_data_prepared.pop(key, None)
            else:
                # Użytkownik niezalogowany - usuń wszystko
                keys_to_remove = ['password', 'salt', 'contact', 'uprawnienia', 'email', 'login', 'contact', 'status_usera']
                for key in keys_to_remove:
                    member_data_prepared.pop(key, None)
                
        else:
            member_data_prepared = {}

        ready_name = member_data_prepared.get('name', 'Brak nazwy')
        pageTitle = ready_name
        session['page'] = ready_name

        return render_template(
            'team_member.html',
            pageTitle=pageTitle,
            dane_pracownika=member_data_prepared
        )
    else:
        abort(404)


@app.route("/reception/<link_hash>")
def reception_dashboard(link_hash):
    """ Widok recepcji do obsługi wizyt pacjentów """

    visit_data = get_visit_data(link_hash)

    # Pobranie parametrów GET z URL (data, czas, email)
    selected_email = request.args.get("emailtoconfirmverification")
    selected_date = request.args.get("date")
    selected_time = request.args.get("time")

    if visit_data:
        visit_date_str = str(visit_data.get("visit_date"))  # Konwersja na string dla poprawnego porównania

        if selected_date and selected_time and selected_email:
            if selected_date == visit_date_str and selected_email == visit_data.get("email"):
                # Tworzenie pełnego datetime z daty i godziny wizyty
                confirmed_datetime_str = f"{selected_date} {selected_time[:2]}:{selected_time[2:]}:00"
                confirmed_datetime = datetime.strptime(confirmed_datetime_str, "%Y-%m-%d %H:%M:%S")
                now = datetime.now()

                # 🔹 Sprawdzamy, czy data i godzina nie są w przeszłości
                if confirmed_datetime < now:
                    flash("❌ Nie można ustawić terminu wstecznego!", "error")
                    return redirect(url_for("reception_dashboard", link_hash=visit_data.get("link_hash")))

                # Aktualizacja statusu wizyty w bazie
                update_query = """
                    UPDATE appointment_requests 
                    SET status = 'confirmed', confirmed_date = %s, confirmed_flag = 0 
                    WHERE id = %s AND status = 'in_progress' AND confirmed_flag = 0
                """
                updated = msq.insert_to_database(update_query, (confirmed_datetime_str, visit_data["id"]))

                if updated:
                    return redirect(url_for("reception_dashboard", link_hash=visit_data.get("link_hash")))

        return render_template("reception.html", visit=visit_data)

    return redirect(url_for('index'))

    









if __name__ == '__main__':
    # app.run(debug=True, port=5000)
    app.run(debug=True, host='0.0.0.0', port=5000)