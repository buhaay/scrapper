from pprint import pprint

from flask import Flask
from flask import request, render_template
from main import Luxmed
import config

app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def hello_world():
    if request.method == 'GET':
        # luxmed = Luxmed(config.email, config.password)
        # luxmed.getLogin()
        # luxmed.getGroupsIds()
        # varieties = luxmed.parseVarieties()
        from varieties import varieties
        return render_template('index.html', varieties=varieties)
    else:
        pass
