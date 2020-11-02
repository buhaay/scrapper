from pprint import pprint

from flask import Flask, redirect, url_for, request, render_template
from main import Luxmed
import config
app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['login']
        password = request.form['password']

        return redirect(url_for('search', login=email, password=password))

    message = request.args.get('message', '')
    return render_template('login.html', message=message)


@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'GET':
        pprint(request)
        email = request.args['login']
        password = request.args['password']
        luxmed = Luxmed(login=email, password=password)
        content = {}

        luxmed.getMainPage()
        try:
            session = luxmed.getLogin()
        except Exception as e:
            return redirect(url_for('login', message=str(e)))

        luxmed.getGroupsIds()
        varieties = luxmed.parseVarieties()
        # from varieties import varieties
        return render_template('index.html', varieties=varieties)
    else:
        pass
