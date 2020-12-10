import config
import _thread
import time

from random import randint
from pprint import pprint
from flask import Flask, redirect, url_for, request, render_template
from main import LuxmedRequester, LuxmedParser

app = Flask(__name__)

storage = {}


def search_block(exam, term):
    while not term:
        sleep_time = randint(15, 45)
        print(f'Czekamy {sleep_time} sekund...')
        time.sleep(sleep_time)
        visits = requester.searchVisits(exam['id'])
        term = parser.parseVisits(visits, start_date, end_date)

    response_dict = confirm_visit_block(exam, term)
    return term


def confirm_visit_block(exam, term):
    requester = storage['requester']
    token = requester.getToken()
    requester.saveTerm()
    reservation_id = requester.lockTerm(exam, term)
    response_dict = requester.confirmVisit()
    return response_dict


@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # fetch form inputs
        email = request.form['login']
        password = request.form['password']

        # initiate requester and store it for next methods
        requester = LuxmedRequester(login=email, password=password)
        storage['requester'] = requester

        # get main page
        requester.getMainPage()

        # try to login
        try:
            username = requester.getLogin()
            storage['username'] = username
        except Exception as e:
            return redirect(url_for('login', message=str(e)))

        return redirect(url_for('search'))

    message = request.args.get('message', '')
    return render_template('login.html', message=message)


@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'GET':
        # initiate parser and requester
        parser = LuxmedParser()
        requester = storage['requester']

        # fetch all exam varieties
        service_groups = requester.getGroupsIds()
        varieties = parser.parseVarieties(service_groups)
        return render_template('index.html', varieties=varieties, username=storage['username'])
    else:
        # initiate requester and parser
        parser = LuxmedParser()
        requester = storage['requester']

        # fetch form inputs
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        exam_choice = request.form['exam_choice']

        # start searching process
        service_groups = requester.getGroupsIds()
        varieties = parser.parseVarieties(service_groups)
        exam_index = int(exam_choice.split('|')[0])
        exam_nested_index = int(exam_choice.split('|')[1])
        exam = varieties[exam_index]['examList'][exam_nested_index]
        visits = requester.searchVisits(exam['id'])
        term = parser.parseVisits(visits, start_date, end_date)

        # if term is not available start new thread with searching
        # process and return info to user
        if not term:
            _thread.start_new_thread(search_block, (exam, term, ))
            response_dict = {
                'username': storage['username'],
                'status': 'W trakcie wyszukiwania',
                'message': f'Brak wizyt w podanym przedziale czasowym\n'
                           f'Poinformujemy Cię mailowo jeśli uda się zarezerwować '
                           f'wizytę w wybranym przez Ciebie terminie.',
                'reservation_details': {},
            }
            return render_template('manage_reservation.html', response_dict=response_dict)

        # if term is available return details to user
        response_dict = confirm_visit_block(exam, term)
        return render_template('manage_reservation.html', response_dict=response_dict)
