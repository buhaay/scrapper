from pprint import pprint

import requests
from tools import saveFile, _printer
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
        self._URL_SEARCH = self._URL + '/NewPortal/terms/index?cityId=5&serviceVariantId=13410&languageId=10&searchDateFrom=2020-09-17&searchDateTo=2020-09-30&searchDatePreset=14&=,&processId=a2ed410b-17c9-4338-a801-6a1a9ce3f608&nextSearch=false&searchByMedicalSpecialist=false&isSecondServiceVariantPostTriage=false'
        # CONFIG
        self._DEBUG = True

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
        session = self.session
        self.headers.update({
            'Referer': 'https://portalpacjenta.luxmed.pl/PatientPortal/NewPortal/Page/Reservation/Search',
            'X-Requested-With': 'XMLHttpRequest',
            'X-Is-RWD': 'false',
        })
        response = session.get(self._URL_GROUPS, headers=self.headers)
        print(response.status_code)
        if self._DEBUG:
            saveFile('groups_page', response.text)
        _printer(header='RESPONSE', data=response.content)
        return response.json()

    def searchVisits(self):
        session = self.session
        response = session.get(self._URL_SEARCH)
        if self._DEBUG:
            saveFile('visits', response.text)
        print(response.status_code)
        pprint(response.json())


if __name__ == '__main__':
    luxmed = Luxmed(login=config.email, password=config.password)
    luxmed.getLogin()
    luxmed.getGroupsIds()
    luxmed.searchVisits()
