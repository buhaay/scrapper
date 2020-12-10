import re
import sys
import uuid

from datetime import date, datetime
from pprint import pprint
from simplejson.errors import JSONDecodeError
import requests
from tools import saveFile, getToday, getDeltaDate, getDayName, logger
import config


class LuxmedRequester:

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
        }

        # URLS
        self._URL = 'https://portalpacjenta.luxmed.pl/PatientPortal/'
        self._URL_MAIN_PAGE = self._URL + 'Account/LogOn'
        self._URL_LOGIN = self._URL + 'Account/LogIn'
        self._URL_GROUPS = self._URL + 'NewPortal/Dictionary/serviceVariantsGroups'
        self._URL_SEARCH = self._URL + 'NewPortal/terms/index'
        self._URL_TOKEN = self._URL + 'NewPortal/security/getforgerytoken'
        self._URL_SAVETERM = self._URL + 'NewPortal/availabilityLog/save'
        self._URL_LOCKTERM = self._URL + 'NewPortal/reservation/lockterm'
        self._URL_CONFIRM = self._URL + 'NewPortal/reservation/confirm'

        # CONFIG
        self._DEBUG = False
        self.debug_dict = {
            'exam_id': 4436,
        }

    def request_printer(self):
        def wrapper_function(*args, **kwargs):
            print('\n')
            logger('{}'.format(self.__name__))
            session = args[0].session
            print('{} Request Headers {}'.format('#'*20, '#'*20))
            for header_name, header_value in session.headers.items():
                print(f'[{header_name} : {header_value}]')
            print('#'*57)
            return self(*args, **kwargs)

        return wrapper_function

    @request_printer
    def getMainPage(self):
        """Initiate main page to get all cookies
        """
        session = self.session
        session.headers.update(self.headers)

        response = session.get(self._URL_MAIN_PAGE, headers=self.headers)
        if not response.status_code == 200:
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

        username_pattern = re.compile(
            'dropdown[\'\"].*?[\'\"]name[\'\"]>([A-Z\s]+)<', re.S)
        username = username_pattern.findall(response.text)[0]
        self.storage['username'] = username
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

        return service_groups

    @request_printer
    def searchVisits(self, exam_id):
        """Search for visit using user input
        """
        storage = self.storage
        session = self.session
        processId = str(uuid.uuid1())
        storage['processId'] = processId

        postData = {
            'serviceVariantId': exam_id,
            'cityId': '5',
            'languageId': '10',
            'searchDateFrom': getToday(),
            # for now search default 2 weeks
            'searchDateTo': getDeltaDate(date.today(), expected_format='%Y-%m-%d', days=14),
            'searchDatePreset': '14',
            'processId': processId,
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
                'correlationId': jsonResponse['correlationId'],
                'allTermsCount': jsonResponse['termsForService']['additionalData']['allTermsCount'],
            })
            availability = jsonResponse['termsForService']['termsForDays']

        except JSONDecodeError:
            raise Exception('Coś poszło nie tak przy parsowaniu wizyt.')

        print(f'* Szukam terminów... \n'
              f'* Znalazłem {len(availability)} dostępnych dni:')
        return availability

    @request_printer
    def getToken(self):
        """ endpoint - /getforgerytoken
        || GET    || returns token which is required to setup as request-header in next step
        """
        session = self.session
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

        self.headers.update({
            'XSRF-TOKEN': jsonResponse['token'],
            'X-Requested-With': 'XMLHttpRequest',
        })
        if 'X-Is-RWD' in self.headers:
            del self.headers['X-Is-RWD']

        return jsonResponse['token']

    @request_printer
    def saveTerm(self):
        """ endpoint - /save
        || POST  || there's no content returned by this enpoint but it's nes
        """
        storage = self.storage
        session = self.session

        postData = {
            'processId': storage['processId'],
            'correlationId': storage['correlationId'],
            'searchParameters': {
                'cityId': 5,
                'serviceVariantId': 4436,
                'referralTypeId': None,
                'searchDateFrom': getToday(),
                'searchDateTo': getDeltaDate(date.today(), expected_format='%Y-%m-%d', days=14),
                'facilityIds': [],
                'doctorIds': [],
                'languageId': 10,
                'partsOfDay': [0],
            },
            'searchResult': {
                'allTermsCount': storage['allTermsCount'],
                'additionalTermsCount': 37
            }
        }

        pprint(postData)
        response = session.post(
            self._URL_SAVETERM,  data=postData, headers=self.headers)
        print(self._URL_LOCKTERM)
        print(response.status_code)
        return

    @request_printer
    def lockTerm(self, exam, av_visit):
        """ endpoint - /lockterm
        || POST   || sends reservation specific post data & returns 'temporaryReservationId' passed
                     as param in next step
        """
        time_from = av_visit['dateTimeFrom'].split('T')[1][:-3]
        time_to = av_visit['dateTimeTo'].split('T')[1][:-3]

        start_date = datetime.strptime(
            av_visit['dateTimeFrom'], '%Y-%m-%dT%H:%M:%S')
        full_date = getDeltaDate(
            start_date, expected_format='%Y-%m-%dT%H:%M:%S.000Z', hours=-1)
        postData = {
            'serviceVariantId': exam['id'],
            'serviceVariantName': exam['name'],
            'facilityId': av_visit['clinicId'],
            'facilityName': 'Konsultacja telefoniczna' if 'telefoniczna' in exam['name']
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
            'correlationId': self.storage['correlationId'],
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
        session = self.session
        response = session.post(
            self._URL_LOCKTERM, data=postData, headers=self.headers)
        print(self._URL_LOCKTERM)

        if self._DEBUG:
            saveFile('lockterm', response.text)

        try:
            jsonResponse = response.json()
            reservation_id = jsonResponse['value']['temporaryReservationId']
            pprint('=== response ===')
            pprint(jsonResponse)
            pprint('=== /response ===')
            if jsonResponse['errors']:
                raise Exception(jsonResponse['errors'][0]['message'])
        except Exception as e:
            raise Exception(str(e))

        self.storage.update({
            'tmp_reservation_id': reservation_id,
            'valuation': jsonResponse['value']['valuations'][0],
            'doctorDetails': jsonResponse['value']['doctorDetails'],
        })
        # self.storage['valuation']['price'] = int(self.storage['valuation']['price'])
        return reservation_id

    @request_printer
    def confirmVisit(self):
        """ endpoint - /confirm
        || POST   || last request, returns json with reservationId
        """
        storage = self.storage
        session = self.session
        response_dict = {}

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

        response = session.post(
            self._URL_CONFIRM, data=postData, headers=self.headers)
        if self._DEBUG:
            saveFile('confirm', response.text)

        try:
            error_messages = []
            jsonResponse = response.json()
            pprint('=== response ===')
            pprint(jsonResponse)
            pprint('=== /response ===')
            if jsonResponse.get('errors', []):
                error_messages = [error['message']
                                  for error in jsonResponse['errors']]
                raise Exception('\n'.join(error_messages))
            elif jsonResponse.get('warnings', []):
                error_messages = [error['message']
                                  for error in jsonResponse['warnings']]
                raise Exception('\n'.join(error_messages))

            if jsonResponse.get('value'):
                reservation_id = jsonResponse['value']['reservationId']
                status = 'Potwierdzona'
                message = 'Wizyta zarezerwowana!'
                reservation_details = {
                    'date': post_data_prev['date'].split('T')[0],
                    'time': post_data_prev['timeFrom'],
                    'doctor': storage['doctorDetails'],
                }
            response_dict = {
                'username': storage['username'],
                'status': status,
                'message': message,
                'reservation_details': reservation_details,
            }

        except Exception as e:
            status = 'Odrzucona'
            if error_messages:
                message = str(e)
            else:
                message = 'Coś poszło nie tak. Zaloguj się na <a href="{}"> Portalu Pacjenta ' \
                          'aby sprawdzić swoje rezerwacje'.format(
                              self._URL_MAIN_PAGE)

            response_dict = {
                'username': storage['username'],
                'status': status,
                'message': message,
                'reservation_details': {},
            }

        return response_dict


class LuxmedParser:
    def __init__(self, *args, **kwargs):
        return

    def parseVarieties(self, service_groups):
        """Parses all possibilities to user friendly format and asks for specific visit goal
        """
        # parse varieties and print all possibilities to user
        varieties = {}
        for index, exam in enumerate(service_groups, start=1):
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
        return varieties

    def parseVisits(self, visits, user_start_date, user_end_date):
        """Parse response and check for available visits
        """
        for i, av_day in enumerate(visits, start=1):
            date_string = av_day['day'].split('T')[0]
            day_name = getDayName(date_string)
            print(f'[{i}. {date_string} {day_name}]')

        if len(visits) > 0:
            for av_visit in visits:
                if user_start_date.split(' ')[0] <= av_visit['day'].split('T')[0] <= user_end_date.split(' ')[0]:
                    # if user_start_date.split('T')[0] <= av_visit['day'].split('T')[0] <= user_end_date.split('T')[0]:
                    for term in av_visit['terms']:
                        pprint(term)
                        visit_date_start = term['dateTimeFrom']
                        visit_date_start_obj = datetime.strptime(
                            visit_date_start, '%Y-%m-%dT%H:%M:%S')
                        # user_start_date_obj = datetime.strptime(user_start_date, '%Y-%m-%dT%H:%M')
                        user_start_date_obj = datetime.strptime(
                            user_start_date, '%Y-%m-%d %H:%M')
                        # user_end_date_obj = datetime.strptime(user_end_date, '%Y-%m-%dT%H:%M')
                        user_end_date_obj = datetime.strptime(
                            user_end_date, '%Y-%m-%d %H:%M')
                        print(type(visit_date_start_obj))
                        print(user_start_date_obj)
                        print(user_end_date_obj)
                        if user_start_date_obj <= visit_date_start_obj <= user_end_date_obj:
                            pprint(term)
                            return term
        return False


if __name__ == '__main__':
    try:
        user_start_date = sys.argv[1]
        user_end_date = sys.argv[2]
    except IndexError:
        user_start_date = None
        user_end_date = None

    requester = LuxmedRequester(login=config.email, password=config.password)
    parser = LuxmedParser()
    requester.getMainPage()
    requester.getLogin()
    service_groups = requester.getGroupsIds()
    varieties = parser.parseVarieties(service_groups)

    examId = 4436
    visits = requester.searchVisits(examId)
    term = parser.parseVisits(visits, user_start_date, user_end_date)

    while not term:
        import time
        from random import randint

        sleep_time = randint(15, 45)
        print(f'Czekamy {sleep_time} sekund...')
        time.sleep(sleep_time)
        visits = requester.searchVisits()
        term = parser.parseVisits(visits, user_start_date, user_end_date)

    token = requester.getToken()
    requester.saveTerm()
    pprint(token)
    exam = {
        'id': 4436,
        'name': 'Ortopeda'
    }
    reservation_id = requester.lockTerm(exam, term)
    pprint(reservation_id)
    requester.confirmVisit()
