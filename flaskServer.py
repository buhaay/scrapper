from pprint import pprint

from flask import Flask, redirect, url_for, request, render_template
from main import Luxmed
import config

app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # luxmed = Luxmed(config.email, config.password)
        email = request.form['login']
        password = request.form['password']
        luxmed = Luxmed(email, password)
        return redirect(url_for('search', luxmed=luxmed))

    return render_template('login.html')


@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'GET':
        pprint(request)
        luxmed = request.args['luxmed']
        print(luxmed)
        # luxmed = Luxmed(config.email, config.password)
        # luxmed.getLogin()
        # luxmed.getGroupsIds()
        # varieties = luxmed.parseVarieties()
        from varieties import varieties
        return render_template('index.html', varieties=varieties)
    else:
        pass
