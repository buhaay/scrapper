from datetime import date, datetime
from pprint import pprint
from simplejson.errors import JSONDecodeError
import requests
from tools import saveFile, _printer, getToday, getDeltaDate, getDayName
import config


class Luxmed:
    user_input = {

    }

    def __init__(self, login, password): #, user_input):
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
        self._URL_GROUPS = self._URL + '/NewPortal/Dictionary/serviceVariantsGroups'
        self._URL_SEARCH = self._URL + '/NewPortal/terms/index'
        self._URL_TOKEN = self._URL + '/NewPortal/security/getforgerytoken'
        self._URL_LOCKTERM = self._URL + '/NewPortal/reservation/lockterm'
        self._URL_CONFIRM = self._URL + '/NewPortal/reservation/confirm'

        # CONFIG
        self._DEBUG = True

    def request_printer(func):
        def wrapper_function(*args, **kwargs):
            print('### {}'.format(func.__name__))
            session = args[0].session
            print('### Request Headers ###')
            for header_name, header_value in session.headers.items():
                print(f'[{header_name} : {header_value}]')
            return func(*args, **kwargs)

        return wrapper_function

    @request_printer
    def getMainPage(self, session):
        """Initiate main page to get all cookies
        """
        r = session.get(self._URL_MAIN_PAGE, headers=self.headers)

        if self._DEBUG:
            saveFile('main_page', r.text)
        return r

    @request_printer
    def getLogin(self):
        """Login to your account
        """
        session = self.session
        session.headers.update(self.headers)
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
        service_groups = response.json()
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
            print(f'[{index}. {name}]')
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

        user_choice_exam = int(input(f'# Wybierz usługę z listy powyżej. '
                                     f'[{min(varieties.keys())}-{max(varieties.keys())}]'))

        # specific exams are nested in general exam types so we have to ask user for actual choice
        if len(varieties[user_choice_exam]['examList']) > 0:
            for i, exam in varieties[user_choice_exam]['examList'].items():
                name = exam['name']
                print(f'[{i}. {name}]')

        user_choice_subexam = int(input(f'# Wybierz konkretne badanie z listy powyżej. '
                                        f'[{min(varieties[user_choice_exam]["examList"].keys())}-{max(varieties[user_choice_exam]["examList"].keys())}]'))

        self.storage.update({
            'user_choice': {
                'exam': varieties[user_choice_exam]['examList'][user_choice_subexam]
            }
        })
        return varieties

    @request_printer
    def searchVisits(self):
        """Search for visit using user input
        """
        storage = self.storage
        session = self.session

        postData = {
            'serviceVariantId': storage['user_choice']['exam']['id'],
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

        return availability

    def parseVisits(self):
        """Parse response and check for available visits
        """
        # visitName = visits['termsForService']['serviceVariantName']
        availability = visits
        print(f'* Szukam terminów... \n'
              f'* Znalazłem {len(availability)} dostępnych dni:')

        for i, av_day in enumerate(availability, start=1):
            date_string = av_day['day'].split('T')[0]
            day_name = getDayName(date_string)
            print(f'[{i}. {date_string} {day_name}]')

        if len(availability) > 0:
            # let user choose day
            user_choice_day = int(input(f'# Wybierz dzień: [1-{len(availability)}]'))
            for i, av_visit in enumerate(availability[user_choice_day - 1]['terms']):
                visit_time = av_visit['dateTimeFrom'].split('T')[1][:-3]
                clinic = av_visit['clinic']
                doctor = '{} {}'.format(av_visit['doctor']['firstName'], av_visit['doctor']['lastName'])
                print(f'[{i}. Godzina: {visit_time} | Placówka: {clinic} | Lekarz: {doctor}]')

            # let user choose hour
            user_choice_hour = int(input(f'# Wybierz godzinę: [1-{len(availability[user_choice_day - 1]["terms"])}]'))

            # save user choice visit details
            self.storage['user_choice'].update({
                'av_visit': availability[user_choice_day - 1]['terms'][user_choice_hour]
            })
        else:
            raise Exception('Nie ma dostępnych terminów w przeciągu 2 tygodni.')

    @request_printer
    def bookVisit(self):
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
            if self._DEBUG:
                saveFile('getToken', response.text)

            try:
                jsonResponse = response.json()
                print(f'## Token: {jsonResponse["token"]}')
            except JSONDecodeError:
                raise Exception('Coldn\'t parse token.')

            return jsonResponse['token']

        def lockTerm():
            self.headers.update({
                'XSRF-TOKEN': token,
            })
            time_from = av_visit['dateTimeFrom'].split('T')[1][:-3]
            time_to = av_visit['dateTimeTo'].split('T')[1][:-3]

            start_date = datetime.strptime(av_visit['dateTimeFrom'], '%Y-%m-%dT%H:%M:%S').date()
            full_date = getDeltaDate(start_date, expected_format='%Y-%m-%dT%H:%M:%S.000Z', hours=-2)

            postData = {
                'serviceVariantId': exam['id'],
                'serviceVariantName': exam['name'],
                'facilityId': av_visit['clinicId'],
                'facilityName': 'Konsultacje telefoniczne' if 'telefoniczna' in exam['name'] \
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
            response = session.post(self._URL_LOCKTERM, data=postData, headers=self.headers)

            if self._DEBUG:
                saveFile('lockterm', response.text)

            try:
                jsonResponse = response.json()
            except:
                raise Exception('!!! Wystąpił błąd podczas rezerwacji terminu !!!')

            self.storage.update({
                'tmp_reservation_id': jsonResponse['value']['temporaryReservationId'],
                'valuation': jsonResponse['value']['valuations'][0],
            })

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

            response = session.post(self._URL_CONFIRM, data=postData, headers=self.headers)
            pprint(response)
            if self._DEBUG:
                saveFile('confirmed', response.text)
            return

        storage = self.storage
        session = self.session
        token = getToken()
        av_visit = storage['user_choice']['av_visit']
        exam = storage['user_choice']['exam']

        lockTerm()
        confirmVisit()
        return


if __name__ == '__main__':
    luxmed = Luxmed(login=config.email, password=config.password)
    luxmed.getLogin()
    luxmed.getGroupsIds()
    luxmed.parseVarieties()
    visits = luxmed.searchVisits()
    while not len(visits) > 0:
        import time
        from random import randint
        sleep_time = randint(10, 15)
        print(f'Czekamy {sleep_time} sekund...')
        time.sleep(sleep_time)
        visits = luxmed.searchVisits()

    luxmed.parseVisits()
    luxmed.bookVisit()
