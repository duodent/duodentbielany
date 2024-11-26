from flask import Flask, render_template, redirect, url_for, jsonify, session, request, send_from_directory
from flask_paginate import Pagination, get_page_args
# import mysqlDB as msq
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

# Ustawienie ilości elementów na stronę (nie dotyczy sesji)
app.config['PER_PAGE'] = 6

# Inicjalizacja obsługi sesji
Session(app)

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
# def take_data_where_ID(key, table, id_name, ID):
#     dump_key = msq.connect_to_database(f'SELECT {key} FROM {table} WHERE {id_name} = {ID};')
#     return dump_key

# def take_data_table(key, table):
#     dump_key = msq.connect_to_database(f'SELECT {key} FROM {table};')
#     return dump_key


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


@app.route('/')
def index():
    session['page'] = 'index'
    pageTitle = 'Strona Główna'

    # if f'TEAM-ALL' not in session:
    #     team_list = generator_teamDB()
    #     session[f'TEAM-ALL'] = team_list
    # else:
    #     team_list = session[f'TEAM-ALL']

    # treeListTeam = []
    # for i, member in enumerate(team_list):
    #     if  i < 3: treeListTeam.append(member)
       
    # if f'BLOG-SHORT' not in session:
    #     blog_post = generator_daneDBList_short()
    #     session[f'BLOG-SHORT'] = blog_post
    # else:
    #     blog_post = session[f'BLOG-SHORT']
    
    # blog_post_three = []
    # for i, member in enumerate(blog_post):
    #     if  i < 3: blog_post_three.append(member)


    return render_template(
        f'index.html',
        pageTitle=pageTitle,
        # blog_post_three=blog_post_three,
        # treeListTeam=treeListTeam
        )

# @app.route('/my-zespol')
# def myZespol():
#     session['page'] = 'myZespol'
#     pageTitle = 'Zespół'

#     if f'TEAM-ALL' not in session:
#         team_list = generator_teamDB()
#         session[f'TEAM-ALL'] = team_list
#     else:
#         team_list = session[f'TEAM-ALL']

#     fullListTeam = []
#     for i, member in enumerate(team_list):
#        fullListTeam.append(member)
    
#     return render_template(
#         f'my-zespol.html',
#         pageTitle=pageTitle,
#         fullListTeam=fullListTeam
#         )

# @app.route('/subpage', methods=['GET'])
# def subpage():
#     session['page'] = 'subpage'
#     pageTitle = 'subpage'

#     if 'target' in request.args:
#         if request.args['target'] in ['polityka', 'zasady', 'pomoc', 'faq']:
#             targetPage = request.args['target']
#             pageTitle = targetPage
#         else: 
#             targetPage = "pomoc"
#             pageTitle = targetPage
#     else:
#         targetPage = "pomoc"
#         pageTitle = targetPage

#     return render_template(
#         f'{targetPage}.html',
#         pageTitle=pageTitle
#         )



if __name__ == '__main__':
    # app.run(debug=True, port=5000)
    app.run(debug=True, host='0.0.0.0', port=5000)