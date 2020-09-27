import json
from pprint import pprint
from datetime import date
from dateutil.relativedelta import relativedelta


def saveFile(filename, data):
    with open(f'{filename}.json', 'w') as f:
        f.write(data)
        # print(f'File {filename} successfully saved!')
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


def getDeltaDate(**kwargs):
    if kwargs.get('years'):
        pass
    if kwargs.get('months'):
        pass
    if kwargs.get('days'):
        print(date.today())
        newDate = date.today() + relativedelta(days=+kwargs['days'])

    return newDate.strftime('%Y-%m-%d')
