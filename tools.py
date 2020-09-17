import json
from pprint import pprint


def saveFile(filename, data):
    with open(f'{filename}.html', 'w') as f:
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
