import re
import sys
from datetime import date, datetime
from pprint import pprint
from simplejson.errors import JSONDecodeError
import requests
from tools import saveFile, getToday, getDeltaDate, getDayName
import config


class Luxmed:
    user_input = {

    }

    def __init__(self, login, password):  # , user_input):
        # user_input = self.user_input
        # store important data collected from every request
        self.storage = {}

        # private login and password get from config.py module
        self.login = login
        self.password = password

        # create session and setup headers for it
        self.session = requests.Session()
        self.headers = {
            'Accept': 'application/json, text/plain, */*',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Host': 'portalpacjenta.luxmed.pl',
            'TE': 'Trailers',
            'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:78.0) Gecko/20100101 Firefox/78.0',
            # 'X-Is-RWD': 'false',
            # 'X-Requested-With': 'XMLHttpRequest',
            # 'XSRF-TOKEN': '',
        }

        # URLS
        self._URL = 'https://portalpacjenta.luxmed.pl/PatientPortal/'
        self._URL_MAIN_PAGE = self._URL + 'Account/LogOn'
        self._URL_LOGIN = self._URL + 'Account/LogIn'
        self._URL_GROUPS = self._URL + 'NewPortal/Dictionary/serviceVariantsGroups'
        self._URL_SEARCH = self._URL + 'NewPortal/terms/index'
        self._URL_TOKEN = self._URL + 'NewPortal/security/getforgerytoken'
        self._URL_LOCKTERM = self._URL + 'NewPortal/reservation/lockterm'
        self._URL_CONFIRM = self._URL + 'NewPortal/reservation/confirm'

        # CONFIG
        self._DEBUG = True

    def request_printer(self):
        def wrapper_function(*args, **kwargs):
            print('--- {}'.format(self.__name__))
            session = args[0].session
            print('### Request Headers ({}) ###'.format(datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S')))
            for header_name, header_value in session.headers.items():
                print(f'[{header_name} : {header_value}]')
            return self(*args, **kwargs)

        return wrapper_function

    @request_printer
    def getMainPage(self):
        """Initiate main page to get all cookies
        """
        session = self.session
        session.headers.update(self.headers)

        response = session.get(self._URL_MAIN_PAGE, headers=self.headers)
        if response.status_code == 200:
            print('Main page is ready.')
        else:
            raise Exception('Problem with loading main page!')

        if self._DEBUG:
            saveFile('main_page.html', response.text)
        return response

    @request_printer
    def getLogin(self):
        """Login to your account
        """
        session = self.session

        login_data = {
            'Login': self.login,
            'Password': self.password
        }
        response = session.post(self._URL_LOGIN, data=login_data)

        # check if login form is still present
        if re.search('id=[\'\"]loginForm[\'\"]', response.text):
            message = 'Błąd logowania! Upewnij się, że wpisałeś poprawne ' \
                      'dane i spróbuj ponownie.'
            raise Exception(message)
        # if response.status_code == 200:
        #     print('Login successful!')
        # else:
        #     print(response.status_code)
        #     raise Exception('Problem with login!')

        if self._DEBUG:
            saveFile('after_login', response.text)

        username_pattern = re.compile('dropdown[\'\"].*?[\'\"]name[\'\"]>([A-Z\s]+)<', re.S)
        username = username_pattern.findall(response.text)[0]
        return username

    @request_printer
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
        try:
            service_groups = response.json()
        except JSONDecodeError:
            raise Exception('Error occurred during parsing groups labels.')
        self.storage.update({
            'labels': service_groups
        })
        return

    def parseVarieties(self):
        """Parses all possibilities to user friendly format and asks for specific visit goal
        """
        # parse varieties and print all possibilities to user
        varieties = {}
        for index, exam in enumerate(self.storage['labels'], start=1):
            name = exam['name']
            # print(f'[{index}. {name}]')
            # prints:
            # [1. Konsultacje w placówce]
            # [2. Konsultacje telefoniczne]
            # ....
            # [12. Pozostałe badania]
            variety = {
                'name': exam['name'],
                'id': exam['id']
            }

            exams_dict = {}
            for i, subexam in enumerate(exam['children'], start=1):
                if subexam.get('children'):
                    for subi, subsubexam in enumerate(subexam['children'], start=1):
                        exams_dict.update({
                            subi: {
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

        # user_choice_exam = int(input(f'# Wybierz usługę z listy powyżej. '
        #                              f'[{min(varieties.keys())}-{max(varieties.keys())}]'))

        # user_choice_exam = 1 # TODO
        # specific exams are nested in general exam types so we have to ask user for actual choice
        # if len(varieties[user_choice_exam]['examList']) > 0:
        #     for i, exam in varieties[user_choice_exam]['examList'].items():
        #         name = exam['name']
        #         print(f'[{i}. {name}]')

        # user_choice_subexam = int(input(f'# Wybierz konkretne badanie z listy powyżej. '
        #                                 f'[{min(varieties[user_choice_exam]["examList"].keys())}-{max(varieties[user_choice_exam]["examList"].keys())}]'))

        # user_choice_subexam = 1 # TODO

        # self.storage.update({
        #     'user_choice': {
        #         'exam': varieties[user_choice_exam]['examList'][user_choice_subexam]
        #     }
        # })
        return varieties

    @request_printer
    def searchVisits(self, exam_id):
        """Search for visit using user input
        """
        storage = self.storage
        session = self.session

        postData = {
            'serviceVariantId': exam_id,
            'cityId': '5',
            'languageId': '10',
            'searchDateFrom': getToday(),
            # for now search default 2 weeks
            'searchDateTo': getDeltaDate(date.today(), expected_format='%Y-%m-%d', days=14),
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

        try:
            jsonResponse = response.json()
            self.storage.update({
                'correlationId': jsonResponse['correlationId']
            })
            availability = jsonResponse['termsForService']['termsForDays']

        except JSONDecodeError:
            raise Exception('Coś poszło nie tak przy parsowaniu wizyt.')

        print(f'* Szukam terminów... \n'
              f'* Znalazłem {len(availability)} dostępnych dni:')
        return availability

    def parseVisits(self, visits, user_start_date, user_end_date):
        """Parse response and check for available visits
        """
        # visitName = visits['termsForService']['serviceVariantName']
        availability = visits

        for i, av_day in enumerate(availability, start=1):
            date_string = av_day['day'].split('T')[0]
            day_name = getDayName(date_string)
            print(f'[{i}. {date_string} {day_name}]')

        if len(availability) > 0:
            for av_visit in availability:
                if user_start_date.split(' ')[0] < av_visit['day'].split('T')[0] < user_end_date.split(' ')[0]:
                    for term in av_visit['terms']:
                        pprint(term)
                        visit_date_start = term['dateTimeFrom']
                        visit_date_start_obj = datetime.strptime(visit_date_start, '%Y-%m-%dT%H:%M:%S')
                        user_start_date_obj = datetime.strptime(user_start_date, '%Y-%m-%d %H:%M')
                        user_end_date_obj = datetime.strptime(user_end_date, '%Y-%m-%d %H:%M')
                        print(type(visit_date_start_obj))
                        print(user_start_date_obj)
                        print(user_end_date_obj)
                        if user_start_date_obj < visit_date_start_obj < user_end_date_obj:
                            pprint(term)
                            return term
        return False

    @request_printer
    def bookVisit(self, exam, av_visit):
        print(av_visit)
        """Runs 4 requests to Luxmed site required to confirm visit:
        || endpoint          || method ||   action
        1. /getforgerytoken  || GET    || returns token which is required to setup as request-header in next step
        2. /save             || POST   || returns nothing but it's possible that it's needed to make reservation
        3. /lockterm         || POST   || sends reservation specific post data & returns 'temporaryReservationId' passed
                             ||        || as param in next step
        4. /confirm          || POST   || last request, returns json with reservationId
        """

        def getToken():
            response = session.get(self._URL_TOKEN)
            print(self._URL_TOKEN)

            if self._DEBUG:
                saveFile('getToken', response.text)

            try:
                jsonResponse = response.json()
                print('=== response ===')
                pprint(jsonResponse)
                print('=== response ===')
            except JSONDecodeError:
                raise Exception('Coldn\'t parse token.')

            return jsonResponse['token']

        def lockTerm(exam, av_visit):
            print('=== lockTerm ===')
            time_from = av_visit['dateTimeFrom'].split('T')[1][:-3]
            time_to = av_visit['dateTimeTo'].split('T')[1][:-3]

            start_date = datetime.strptime(av_visit['dateTimeFrom'], '%Y-%m-%dT%H:%M:%S')
            full_date = getDeltaDate(start_date, expected_format='%Y-%m-%dT%H:%M:%S.000Z', hours=-1)
            postData = {
                'serviceVariantId': exam['id'],
                'serviceVariantName': exam['name'],
                'facilityId': av_visit['clinicId'],
                'facilityName': 'Konsultacja telefoniczna' if 'telefoniczna' in exam['name'] \
                    else av_visit['clinic'],
                'roomId': av_visit['roomId'],
                'scheduleId': av_visit['scheduleId'],
                'date': full_date,
                'timeFrom': time_from,
                'timeTo': time_to,
                'doctorId': av_visit['doctor']['id'],
                'doctor': av_visit['doctor'],
                'isAdditional': av_visit['isAdditional'],
                'isImpediment': False,
                'impedimentText': '',
                'isPreparationRequired': False,
                'preparationItems': [],
                'referralId': None,
                'referralTypeId': None,
                'parentReservationId': None,
                'correlationId': storage['correlationId'],
                'isTelemedicine': av_visit['isTelemedicine'],
            }
            self.storage.update({
                'post_data': {
                    'lockTerm': postData,
                }
            })
            pprint('=== postData ===')
            pprint(postData)
            pprint('=== /postData ===')
            response = session.post(self._URL_LOCKTERM, data=postData, headers=self.headers)
            print(self._URL_LOCKTERM)

            if self._DEBUG:
                saveFile('lockterm', response.text)

            try:
                jsonResponse = response.json()
                pprint('=== response ===')
                pprint(jsonResponse)
                pprint('=== /response ===')
                if jsonResponse['errors']:
                    raise Exception(jsonResponse['errors'][0]['message'])
            except Exception as e:
                raise Exception(str(e))

            self.storage.update({
                'tmp_reservation_id': jsonResponse['value']['temporaryReservationId'],
                'valuation': jsonResponse['value']['valuations'][0],
            })
            self.storage['valuation']['price'] = int(self.storage['valuation']['price'])

        def confirmVisit():
            post_data_prev = storage['post_data']['lockTerm']
            postData = {
                'date': post_data_prev['date'],
                'doctorId': post_data_prev['doctorId'],
                'facilityId': post_data_prev['facilityId'],
                'parentReservationId': post_data_prev['parentReservationId'],
                'referralId': post_data_prev['referralId'],
                'referralRequired': False,
                'roomId': post_data_prev['roomId'],
                'serviceVariantId': post_data_prev['serviceVariantId'],
                'temporaryReservationId': storage['tmp_reservation_id'],
                'timeFrom': post_data_prev['timeFrom'],
                'valuation': storage['valuation'],
                'valuationId': None,
            }
            print('=== postData ===')
            pprint(postData)
            print('=== /postData ===')
            pprint(self.headers)
            response = session.post(self._URL_CONFIRM, data=postData, headers=self.headers)
            print(self._URL_CONFIRM)
            pprint(response)
            pprint(response.text)
            if self._DEBUG:
                saveFile('confirm', response.text)
            return

        storage = self.storage
        session = self.session
        token = getToken()
        self.headers.update({
            'XSRF-TOKEN': token,
            'X-Requested-With': 'XMLHttpRequest',
        })
        if 'X-Is-RWD' in self.headers:
            del self.headers['X-Is-RWD']

        lockTerm(exam, av_visit)
        confirmVisit()
        return


if __name__ == '__main__':
    try:
        user_start_date = sys.argv[1]
        print(user_start_date)
        user_end_date = sys.argv[2]
        print(user_end_date)
    except IndexError:
        user_start_date = None
        user_end_date = None

    luxmed = Luxmed(login=config.email, password=config.password)
    luxmed.getMainPage()
    luxmed.getLogin()
    luxmed.getGroupsIds()
    luxmed.parseVarieties()
    visits = luxmed.searchVisits()
    term = luxmed.parseVisits()

    while not term:
        import time
        from random import randint

        sleep_time = randint(15, 45)
        print(f'Czekamy {sleep_time} sekund...')
        time.sleep(sleep_time)
        visits = luxmed.searchVisits()
        term = luxmed.parseVisits()

    luxmed.bookVisit(term)
