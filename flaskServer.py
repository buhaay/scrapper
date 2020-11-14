from pprint import pprint

from flask import Flask, redirect, url_for, request, render_template
from main import Luxmed
import config

app = Flask(__name__)

storage = {}


@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['login']
        password = request.form['password']
        luxmed = Luxmed(login=email, password=password)
        storage['luxmed'] = luxmed

        luxmed.getMainPage()

        try:
            username = luxmed.getLogin()
        except Exception as e:
            return redirect(url_for('login', message=str(e)))

        return redirect(url_for('search', username=username))

    message = request.args.get('message', '')
    return render_template('login.html', message=message)


@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'GET':
        content = {}
        username = request.args.get('username')
        luxmed = storage['luxmed']
        luxmed.getGroupsIds()
        varieties = luxmed.parseVarieties()
        pprint(varieties)
        return render_template('index.html', varieties=varieties, username=username)
    else:
        start_date = request.form['start_date']
        print(start_date)
        end_date = request.form['end_date']
        print(end_date)
        exam_choice = request.form['exam_choice']
        print(exam_choice)
        luxmed = storage['luxmed']
        varieties = luxmed.parseVarieties()

        exam_index = int(exam_choice.split('|')[0])
        exam_nested_index = int(exam_choice.split('|')[1])
        exam = varieties[exam_index]['examList'][exam_nested_index]
        print(exam)
        visits = luxmed.searchVisits(exam['id'])
        term = luxmed.parseVisits(visits, start_date, end_date)

        while not term:
            import time
            from random import randint

            sleep_time = randint(15, 45)
            print(f'Czekamy {sleep_time} sekund...')
            time.sleep(sleep_time)
            visits = luxmed.searchVisits(exam['id'])
            term = luxmed.parseVisits(visits, start_date, end_date)

        luxmed.bookVisit(exam, term)

        return render_template('manage_reservation.html')