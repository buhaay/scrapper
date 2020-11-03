import json
from pprint import pprint
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
import os

polish_day_map = {
    'Monday': 'Poniedziałek',
    'Tuesday': 'Wtorek',
    'Wednesday': 'Środa',
    'Thursday': 'Czwartek',
    'Friday': 'Piątek',
    'Saturday': 'Sobota',
    'Sunday': 'Niedziela',
}


def saveFile(filename, data):
    path = os.path.join(os.getcwd(), 'responses')
    try:
        json.loads(data)
        extension = 'json'
    except:
        extension = 'html'

    with open(os.path.join(path, f'{filename}.{extension}'), 'w') as f:
        f.write(data)
    return


def _printer(header, data):
    try:
        data = json.loads(data)
    except (json.JSONDecodeError, TypeError):
        data = None

    print('[{} {} {}]'.format(25 * '#', header, 25 * '#'))
    if data:
        pprint(data)
    print('[{} {} {}]'.format(25 * '#', header, 25 * '#'))


def getToday():
    today = date.today().strftime('%Y-%m-%d')
    return today


def getDeltaDate(start_date, expected_format, **kwargs):
    if kwargs.get('years'):
        pass
    elif kwargs.get('months'):
        pass
    elif kwargs.get('days'):
        newDate = start_date + relativedelta(days=+kwargs['days'])
    elif kwargs.get('hours'):
        newDate = start_date + relativedelta(hours=+kwargs['hours'])

    return newDate.strftime(expected_format)


def getDayName(date_string):
    dateObject = datetime.strptime(date_string, '%Y-%m-%d')
    dayName = dateObject.strftime('%A')
    return polish_day_map[dayName]


