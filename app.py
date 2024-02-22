import asyncio
from datetime import timedelta
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, session, flash
from telethon.sync import *
import os
import dotenv
from misc import database

dotenv.load_dotenv()
app = Flask(__name__)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = os.getenv('FLASK_SECRET_KEY')


def login_required(view_func):
    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        if 'user_id' not in session:
            flash('Пожалуйста, войдите в систему для доступа к этой странице.', 'warning')
            return redirect('/')
        return view_func(*args, **kwargs)

    return wrapped_view


@app.route('/', methods=['GET', 'POST'])
def login_handler():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if not database.get_username_status(username):
            flash("Пользователь еще не зарегистрирован")
            return render_template('login.html')
        if not database.auth_correct(username, password):
            flash("Некорректные данные!")
            return render_template('login.html')
        session['user_id'] = database.get_user(username).id
        session.permanent = True  # Сессия становится постоянной
        app.permanent_session_lifetime = timedelta(minutes=30)  # Время жизни сессии в секундах
        if len(database.get_chats_by_user(session['user_id'])) == 0:
            return redirect('/telegram_auth')
        return redirect('/home')
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['email']
        password = request.form['password']

        if database.get_username_status(username):
            flash("Пользователь уже зарегистрирован")
            return render_template('register.html')


        database.add_search_account(hi_message='', email=username, password=password)
        flash('Регистрация выполнена!')
        return redirect('/')

    return render_template('register.html')


@app.route('/home', methods=['GET', 'POST'])
@login_required
def home():
    if request.method == 'POST':
        database.disable_chats_by_user_id(session['user_id'])
        params = request.form.to_dict()
        database.update_search_info(params['search_keywords'], params['hi_message'], params['account_to_post'], session['user_id'])
        del params['search_keywords']
        del params['hi_message']
        del params['account_to_post']
        print("PARAMS", params)
        for chat in params.keys():
            database.enable_chat(int(chat), session['user_id'])

    search_info = database.get_search_info(session['user_id'])
    hi_message = search_info.deal_hi_message
    search_keywords = search_info.search_words
    account_to_post = search_info.link_to_telegram_channel
    return render_template('chat_list.html',
                           hi_message=hi_message,
                           search_keywords=search_keywords,
                           account_to_post=account_to_post,
                           chat_list=database.get_chats_by_user(session['user_id']))


@app.route('/logout')
@login_required
def logout():
    session.pop('user_id', None)
    flash('Вы успешно вышли из системы!', 'success')
    return redirect('/')


@app.route('/telegram_auth', methods=['GET', 'POST'])
@login_required
def telegram_auth():
    if request.method == 'POST':
        api_id = request.form['api_id']
        session['api_id'] = api_id
        api_hash = request.form['api_hash']
        session['api_hash'] = api_hash
        phone_number = request.form['phone_number']
        session['phone_number'] = phone_number

        return redirect(url_for('chats'))

    return render_template('telegram_auth.html')


@app.route('/chats', methods=['GET', 'POST'])
@login_required
def chats():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    phone_number = session.get('phone_number')
    api_id = session.get('api_id')
    api_hash = session.get('api_hash')
    session_name = f'session_{phone_number}'
    client = TelegramClient(session_name, api_id, api_hash)
    client.connect()

    if not client.is_user_authorized():
        client.send_code_request(phone_number)
        if request.method == 'POST':
            code = request.form['code']
            client.sign_in(phone_number, code)
        else:
            return render_template('enter_code.html')
    database.save_telegram(api_id, api_hash, session_name, session.get('user_id'))
    dialogs = client.get_dialogs()
    chat_list = [{'title': dialog.title, 'id': dialog.id} for dialog in dialogs]
    client.disconnect()
    for chat in chat_list:
        database.add_telegram_chat(session.get('user_id'), chat['id'], chat['title'], False)
    return redirect('/home')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=81, debug=True)


