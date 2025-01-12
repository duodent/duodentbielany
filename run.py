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
import string
import re
import os
from flask_session import Session
import hashlib
import uuid
from sendEmailBySmtp import send_html_email




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
                for c in SPLX_MULTI_ITEM: 
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
    # Tymczasowe zmienne prototypowe
    tygodniowa_statystyka_uslug = 120  # Liczba usług wykonanych w tygodniu
    data_rozpoczecia_dzialalnosci = datetime(1989, 5, 20)  # Data rozpoczęcia działalności
    liczba_pracownikow = len(generator_teamDB())  # Aktualna liczba pracowników
    zadeklarowani_pracownicy = 10  # Członkowie zespołu z poza strony www
    procent_zadowolonych_klientow = 75  # Zadeklarowany procent zadowolonych klientów (w %)

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
    got_data = take_data_where_ID("*", 'table', 'id', 1)

    return



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
                <p style="color: red;">Jeżeli potrzebujesz jeszcze login skontaktuj się z <a href="mailto:admin@duodent.com.pl" style="color: #24363f;">administratorem systemu: admin@duodent.com.pl</a></p>
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
    if len(treatmentFooter) >= 3:
        treatmentFooter = treatmentFooter[:3]
    return {
        'userName': session.get("username", 'NotLogin'),
        'treatmentMenu': {item["ready_route"]: item["tytul_glowny"] for item in treatments_db(True)},
        'treatmentFooter': treatmentFooter,
        'companyStats': calculate_statistics()
    }


















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
            }
        superuser_worker_select.append(insertRekord)


    own_user_data = {
        'id': session.get('user_data',{}).get('id'),
        'name': session.get('user_data',{}).get('name')
        }


    # Renderowanie szablonu z rolą użytkownika
    return render_template(
        "rootipa.html",
        user_role=user_role,
        superuser_worker_select=superuser_worker_select,
        own_user_data=own_user_data
    )













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

    return render_template(
        'index.html',
        pageTitle=pageTitle,
        members=generator_teamDB_v
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











if __name__ == '__main__':
    # app.run(debug=True, port=5000)
    app.run(debug=True, host='0.0.0.0', port=5000)