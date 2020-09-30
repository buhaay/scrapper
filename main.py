from pprint import pprint

import requests
from tools import saveFile, _printer, getToday, getDeltaDate, getDayName
import config


class Luxmed:
    def __init__(self, login, password):
        self.login = login
        self.password = password
        self.session = requests.Session()
        self.headers = {
            'Accept': 'application/json, text/plain, */*',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Host': 'portalpacjenta.luxmed.pl',
            'TE': 'Trailers',
            'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:78.0) Gecko/20100101 Firefox/78.0',
            'X-Is-RWD': 'false',
            'X-Requested-With': 'XMLHttpRequest',
            'XSRF-TOKEN': '',
        }
        # URLS
        self._URL = 'https://portalpacjenta.luxmed.pl/PatientPortal/'
        self._URL_MAIN_PAGE = self._URL + 'Account/LogOn'
        self._URL_LOGIN = self._URL + 'Account/LogIn'
        self._URL_GROUPS = self._URL + '/NewPortal/Dictionary/serviceVariantsGroups'
        self._URL_SEARCH = self._URL + '/NewPortal/terms/index'
        # CONFIG
        self._DEBUG = True

        self.service_groups = None

    def getMainPage(self, s):
        """Initiate main page to get all cookies
        """
        r = s.get(self._URL_MAIN_PAGE, headers=self.headers)

        if self._DEBUG:
            saveFile('main_page', r.text)
        return r

    def getLogin(self):
        """Login to your account
        """
        session = self.session
        r = self.getMainPage(session)
        if r.status_code == 200:
            print('Main page is ready.')
        else:
            raise Exception('Problem with loading main page!')

        login_data = {
            'Login': self.login,
            'Password': self.password
        }
        response = session.post(self._URL_LOGIN, data=login_data)
        if response.status_code == 200:
            print('Login successful!')
        else:
            print(response.status_code)
            raise Exception('Problem with login!')
        # _printer(header='LOGIN PAGE', data=response)

        if self._DEBUG:
            saveFile('after_login', response.text)

        return session

    def getGroupsIds(self):
        """Get json with all IDs for services, doctors and places
        """
        session = self.session
        self.headers.update({
            'Referer': 'https://portalpacjenta.luxmed.pl/PatientPortal/NewPortal/Page/Reservation/Search',
            'X-Requested-With': 'XMLHttpRequest',
            'X-Is-RWD': 'false',
        })
        response = session.get(self._URL_GROUPS, headers=self.headers)
        if self._DEBUG:
            saveFile('groups_page', response.text)
        # _printer(header='RESPONSE', data=response.content)
        self.service_groups = response.json()
        return response.json()

    def searchVisits(self):
        """Search for visit using user input
        """
        session = self.session

        # parse varieties and print all possibilities to user
        varieties = {}
        for index, exam in enumerate(self.service_groups, start=1):
            name = exam['name']
            print(f'{index}. {name}')
            variety = {
                'name': exam['name'],
                'id': exam['id']
            }

            exams_dict = {}
            for i, subexam in enumerate(exam['children'], start=1):
                if subexam.get('children'):
                    for i, subsubexam in enumerate(subexam['children'], start=1):
                        exams_dict.update({
                            i: {
                                'name': subsubexam['name'],
                                'id': subsubexam['id'],
                            }
                        })
                else:
                    exams_dict.update({
                        i: {
                            'name': subexam['name'],
                            'id': subexam['id'],
                        }
                    })
            variety['examList'] = exams_dict
            varieties.update({
                index: variety,
            })

        user_choice_exam = int(input(f'Wybierz usługę z listy powyżej. '
                                     f'[{min(varieties.keys())}-{max(varieties.keys())}]'))

        # specific exams are nested in general exam types so we have to ask user for actual choice
        if len(varieties[user_choice_exam]['examList']) > 0:
            for i, exam in varieties[user_choice_exam]['examList'].items():
                name = exam['name']
                print(f'{i}. {name}')

        user_choice_subexam = int(input(f'Wybierz konkretne badanie z listy powyżej. '
                                        f'[{min(varieties.keys())}-{max(varieties.keys())}]'))

        postData = {
            'serviceVariantId': varieties[user_choice_exam]['examList'][user_choice_subexam]['id'],
            'cityId': '5',
            'languageId': '10',
            'searchDateFrom': getToday(),
            # for now search default 2 weeks
            'searchDateTo': getDeltaDate(days=14),
            'searchDatePreset': '14',
            'processId': '0c7f68f8-d62b-4db4-a949-7cbc6599ea0b',
            # 'secondServiceVariantId': '12574',
            'nextSearch': 'false',
            'searchByMedicalSpecialist': 'false',
            'isSecondServiceVariantPostTriage': 'true',
            '': '',
        }

        response = session.get(self._URL_SEARCH, params=postData)
        if self._DEBUG:
            saveFile('visits', response.text)
        return response.json()

    def parseVisits(self, data):
        """Parse response and check for available visits
        """
        visitName = data['termsForService']['serviceVariantName']
        availability = data['termsForService']['termsForDays']
        # doctor = '{} {}'.format(data['doctor']['firstName'], data['doctor']['lastName'])

        print(f'You\'re searching for visits to: {visitName} \n'
              f'We\'ve found {len(availability)} available visits:')

        print(f'Available days to see {visitName.upper()}: ')
        for i, day in enumerate(availability, start=1):
            date_string = day['day'].split('T')[0]
            day_name = getDayName(date_string)
            print(f'[{i}. {date_string} {day_name}]')

        return


if __name__ == '__main__':
    luxmed = Luxmed(login=config.email, password=config.password)
    luxmed.getLogin()
    luxmed.getGroupsIds()
    visits = luxmed.searchVisits()
    luxmed.parseVisits(visits)
