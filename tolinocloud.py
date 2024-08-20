#tolino cloud access module

# Hey, tolino developers at Telekom / T-Systems:
#
# This client wants to be a friendly citizen within the tolino cloud.
# It accesses the javascript / REST api of pageplace.de and
# does so in a responsible manner, no hacking involved.
#
# It works, but it would be nice if you could look at the
# "Hey, tolino developers" comments in this code. I'm grateful for
# some hints to make this code work better for your service.


# Copyright (C) 2014 Hanno Zulla
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.


import platform
import json
import base64
import re
from urllib.parse import urlparse, parse_qs
import logging
from pprint import pformat
import time
import sys
from configparser import ConfigParser

class TolinoException(Exception):
    pass


class TolinoCloud:

    def _hardware_id():

        # tolino wants to know a few details about the HTTP client hardware
        # when it connects.
        #
        # 1233X-44XXX-XXXXX-XXXXX-XXXXh
        #
        # 1  = os id
        # 2  = browser engine id
        # 33 = browser id
        # 44 = browser version
        # X  = the result of a fingerprinting image

        os_id = {
            'Windows' : '1',
            'Darwin'  : '2',
            'Linux'   : '3'
            }.get(platform.system(), 'x')

        # The hardware id contains some info about the browser
        #
        # Hey, tolino developers: Let me know which id values to use here
        engine_id  = 'x'
        browser_id = 'xx'
        version_id = '00'

        # For some odd reason, the tolino javascript draws the text
        # "www.tolino.de" and a rectangle filled with the offical Telekom
        # magenta #E20074 (http://de.wikipedia.org/wiki/Magenta_%28Farbe%29)
        # into an image canvas and then fuddles around with the
        # base64-encoded PNG. Probably to gain some sort of fingerprint,
        # but it's not quite clear how this would help the tolino API.
        #
        # Hey, tolino developers: Let me know what you need here.

        fingerprint = 'ABCDEFGHIJKLMNOPQR'

        return (os_id +
            engine_id +
            browser_id +
            fingerprint[0:1] +
            '-' +
            version_id +
            fingerprint[1:4] +
            '-' +
            fingerprint[4:9] +
            '-' +
            fingerprint[9:14] +
            '-' +
            fingerprint[14:18] +
            'h')

    hardware_id = _hardware_id()

    partner_name = {
         1 : 'Telekom',
         3 : 'Thalia.de',
         4 : 'Thalia.at',
         5 : 'Thalia.ch',
         6 : 'Buch.de',
         7 : 'buch.ch',
         8 : 'Books.ch / orellfuessli.ch',
        10 : 'Weltbild.de',
        11 : 'Weltbild.at',
        12 : 'Weltbild.ch',
        13 : 'Hugendubel.de',
        20 : 'derclub.de',
        21 : 'otto-media.de',
        22 : 'donauland.at',
        23 : 'osiander.de',
        30 : 'bücher.de',
        40 : 'Bild.de', # defunct?
        60 : 'StandaardBoekhandel.be',
        80 : 'Libri.de',
        81 : 'eBook.de',
        90 : 'ibs.it'
    }

    partner_settings = {
        3: {
            # Thalia.de
            'client_id'        : 'webreader',
            'scope'            : 'SCOPE_BOSH',
            'signup_url'       : 'https://www.thalia.de/shop/home/kunde/neu/',
            'profile_url'      : 'https://www.thalia.de/shop/home/kunde/',
            'token_url'        : 'https://www.thalia.de/auth/oauth2/token',
            'login_form_url'   : 'https://www.thalia.de/de.thalia.ecp.authservice.application/oauth2/login',
            'x_buchde.skin_id' : '17',
            'x_buchde.mandant_id' :'2',
            'auth_url'         : 'https://www.thalia.de/de.thalia.ecp.authservice.application/oauth2/authorize',
            'login_url'        : 'https://www.thalia.de/de.thalia.ecp.authservice.application/login.do',
            # 'revoke_url'       : 'https://www.thalia.de/de.buch.appservices/api/2004/oauth2/revoke',
            'login_form'       : {
                'username' : 'j_username',
                'password' : 'j_password',
                'extra'    : {
                    'login' : ''
                    }
             },
            'login_cookie'     : 'OAUTH-JSESSIONID',
            'logout_url'       : 'https://www.thalia.de/shop/home/login/logout/',
            'reader_url'       : 'https://webreader.mytolino.com/library/index.html#/mybooks/titles',
            'register_url'     : 'https://bosh.pageplace.de/bosh/rest/v2/registerhw',
            'devices_url'      : 'https://bosh.pageplace.de/bosh/rest/handshake/devices/list',
            'unregister_url'   : 'https://bosh.pageplace.de/bosh/rest/handshake/devices/delete',
            'upload_url'       : 'https://bosh.pageplace.de/bosh/rest/upload',
            'meta_url'         : 'https://bosh.pageplace.de/bosh/rest/meta',
            'cover_url'        : 'https://bosh.pageplace.de/bosh/rest/cover',
            'sync_data_url'    : 'https://bosh.pageplace.de/bosh/rest/sync-data?paths=publications,audiobooks',
            'delete_url'       : 'https://bosh.pageplace.de/bosh/rest/deletecontent',
            'inventory_url'    : 'https://bosh.pageplace.de/bosh/rest/inventory/delta',
            'downloadinfo_url' : 'https://bosh.pageplace.de/bosh/rest//cloud/downloadinfo/{}/{}/type/external-download'
            },
        4: {
            # Thalia.at
            'client_id'        : 'webshop01',
            'scope'            : 'SCOPE_BOSH SCOPE_BUCHDE',
            'signup_url'       : 'https://www.thalia.at/shop/home/kunde/neu/',
            'profile_url'      : 'https://www.thalia.at/shop/home/kunde/',
            'token_url'        : 'https://www.thalia.at/de.buch.appservices/api/4004/oauth2/token',
            'login_form_url'   : 'https://www.thalia.at/de.thalia.ecp.authservice.application/oauth2/login',
            'x_buchde.skin_id' : '17',
            'x_buchde.mandant_id' : '4',
            'auth_url'         : 'https://www.thalia.at/de.thalia.ecp.authservice.application/oauth2/authorize',
            'login_url'        : 'https://www.thalia.at/de.thalia.ecp.authservice.application/login.do',
            # 'revoke_url'       : 'https://www.thalia.de/de.buch.appservices/api/2004/oauth2/revoke',
            'login_form'       : {
                'username' : 'j_username',
                'password' : 'j_password',
                'extra'    : {
                    'login' : ''
                }
             },
            'login_cookie'     : 'OAUTH-JSESSIONID',
            'logout_url'       : 'https://www.thalia.at/shop/home/show/',
            'reader_url'       : 'https://webreader.mytolino.com/library/index.html#/mybooks/titles',
            'register_url'     : 'https://bosh.pageplace.de/bosh/rest/v2/registerhw',
            'devices_url'      : 'https://bosh.pageplace.de/bosh/rest/handshake/devices/list',
            'unregister_url'   : 'https://bosh.pageplace.de/bosh/rest/handshake/devices/delete',
            'upload_url'       : 'https://bosh.pageplace.de/bosh/rest/upload',
            'meta_url'         : 'https://bosh.pageplace.de/bosh/rest/meta',
            'cover_url'        : 'https://bosh.pageplace.de/bosh/rest/cover',
            'sync_data_url'    : 'https://bosh.pageplace.de/bosh/rest/sync-data?paths=publications,audiobooks',
            'delete_url'       : 'https://bosh.pageplace.de/bosh/rest/deletecontent',
            'inventory_url'    : 'https://bosh.pageplace.de/bosh/rest/inventory/delta',
            'downloadinfo_url' : 'https://bosh.pageplace.de/bosh/rest//cloud/downloadinfo/{}/{}/type/external-download'
            },
         6: {
            # Buch.de'
            'client_id'        : 'webshop01',
            'scope'            : 'SCOPE_BOSH SCOPE_BUCHDE',
            'signup_url'       : 'https://ssl.buch.de/shop/home/kunde/neu/',
            'profile_url'      : 'https://ssl.buch.de/shop/home/kunde/',
            'login_url'        : 'https://ssl.buch.de/shop/home/login/dologin/',
            'login_form'       : {
                'username' : 'username',
                'password' : 'password',
                'extra'    : {}
             },
            'login_cookie'     : 'KUNDE',
            'tat_url'          : 'https://ssl.buch.de/shop/home/ebook/anzeigen/',
            'logout_url'       : 'https://ssl.buch.de/shop/home/login/logout/',
            'reader_url'       : 'https://html5reader.buch.de/library/library.html#!/library',
            'register_url'     : 'https://bosh.pageplace.de/bosh/rest/registerhw',
            'devices_url'      : 'https://bosh.pageplace.de/bosh/rest/handshake/devices/list',
            'unregister_url'   : 'https://bosh.pageplace.de/bosh/rest/handshake/devices/delete',
            'upload_url'       : 'https://bosh.pageplace.de/bosh/rest/upload',
            'meta_url'         : 'https://bosh.pageplace.de/bosh/rest/meta',
            'cover_url'        : 'https://bosh.pageplace.de/bosh/rest/cover',
            'sync_data_url'    : 'https://bosh.pageplace.de/bosh/rest/sync-data?paths=publications,audiobooks',
            'delete_url'       : 'https://bosh.pageplace.de/bosh/rest/deletecontent',
            'inventory_url'    : 'https://bosh.pageplace.de/bosh/rest/inventory/delta',
            'downloadinfo_url' : 'https://bosh.pageplace.de/bosh/rest//cloud/downloadinfo/{}/{}/type/external-download'
            },
        8: {
            # books.ch / orellfuessli.ch
            'client_id'        : 'webreader',
            'scope'            : 'SCOPE_BOSH',
            'signup_url'       : 'https://www.orellfuessli.ch/registrierung/privatkunde',
            'profile_url'      : 'https://www.orellfuessli.ch/shop/home/kunde/',
            'token_url'        : 'https://www.orellfuessli.ch/auth/oauth2/token',
            'login_form_url'   : 'https://www.orellfuessli.ch/de.thalia.ecp.authservice.application/oauth2/login',
            'x_buchde.skin_id' : '17',
            'x_buchde.mandant_id': '37',
            'auth_url'         : 'https://www.orellfuessli.ch/de.thalia.ecp.authservice.application/oauth2/authorize',
            'login_url'        : 'https://www.orellfuessli.ch/de.thalia.ecp.authservice.application/login.do',
            'revoke_url'       : 'https://www.orellfuessli.ch//auth/oauth2/revoke',
            'login_form': {
                'username'  : 'j_username',
                'password'  : 'j_password',
                'extra'     : {
                    'login' : ''
                }
            },
            'login_cookie'     : 'OAUTH-JSESSIONID',
            'logout_url'       : 'https://www.orellfuessli.ch/shop/home/login/logout/',
            'reader_url'       : 'https://webreader.mytolino.com/library/index.html#/mybooks/titles',
            'register_url'     : 'https://bosh.pageplace.de/bosh/rest/v2/registerhw',
            'devices_url'      : 'https://bosh.pageplace.de/bosh/rest/handshake/devices/list',
            'unregister_url'   : 'https://bosh.pageplace.de/bosh/rest/handshake/devices/delete',
            'upload_url'       : 'https://bosh.pageplace.de/bosh/rest/upload',
            'delete_url'       : 'https://bosh.pageplace.de/bosh/rest/deletecontent',
            'inventory_url'    : 'https://bosh.pageplace.de/bosh/rest/inventory/delta',
            'meta_url'         : 'https://bosh.pageplace.de/bosh/rest/meta',
            'cover_url'        : 'https://bosh.pageplace.de/bosh/rest/cover',
            'sync_data_url'    : 'https://bosh.pageplace.de/bosh/rest/sync-data?paths=publications,audiobooks',
            'downloadinfo_url' : 'https://bosh.pageplace.de/bosh/rest//cloud/downloadinfo/{}/{}/type/external-download'
        },
        12: {
            # weltbild.ch
            'client_id'        : 'webreader',
            'scope'            : 'ebook_library',
            'token_url'        : 'https://api.weltbild.ch/rest/oauth2/token',
            'auth_url'         : 'https://www.weltbild.ch/oauth2/authorize',
            'login_url'        : 'https://www.weltbild.ch/konto/login',
            'logout_url'       : 'https://www.weltbild.ch/konto/abmelden',
            'login_cookie'     : 'sid',
            'login_form': {
                'username'  : 'unilogin[emailAddress]',
                'password'  : 'unilogin[password]',
                'extra': { 
                   'unilogin[type]': 0,
                }
            },
            'reader_url'       : 'https://webreader.mytolino.com/library/index.html#/mybooks/titles',
            'register_url'     : 'https://bosh.pageplace.de/bosh/rest/v2/registerhw',
            'devices_url'      : 'https://bosh.pageplace.de/bosh/rest/handshake/devices/list',
            'unregister_url'   : 'https://bosh.pageplace.de/bosh/rest/handshake/devices/delete',
            'upload_url'       : 'https://bosh.pageplace.de/bosh/rest/upload',
            'delete_url'       : 'https://bosh.pageplace.de/bosh/rest/deletecontent',
            'inventory_url'    : 'https://bosh.pageplace.de/bosh/rest/inventory/delta',
            'meta_url'         : 'https://bosh.pageplace.de/bosh/rest/meta',
            'cover_url'        : 'https://bosh.pageplace.de/bosh/rest/cover',
            'sync_data_url'    : 'https://bosh.pageplace.de/bosh/rest/sync-data?paths=publications,audiobooks',
            'downloadinfo_url' : 'https://bosh.pageplace.de/bosh/rest//cloud/downloadinfo/{}/{}/type/external-download'
        },
        13: {
            # Hugendubel.de
            'client_id'        : '4c20de744aa8b83b79b692524c7ec6ae',
            'scope'            : 'ebook_library',
            'signup_url'       : 'https://www.hugendubel.de/go/my_my/my_newRegistration/',
            'profile_url'      : 'https://www.hugendubel.de/go/my_my/my_data/',
            'token_url'        : 'https://api.hugendubel.de/rest/oauth2/token',
            # 'revoke_url'       : 'https://api.hugendubel.de/rest/oauth2/revoke',
            'auth_url'         : 'https://www.hugendubel.de/oauth/authorize',
            'login_url'        : 'https://www.hugendubel.de/de/account/login',
            'login_form'       : {
                'username' : 'username',
                'password' : 'password',
                'extra'    : {
                    'evaluate'           : 'true',
                    'isOrdering'         : '',
                    'isOneClickOrdering' : ''
                }
            },
            'login_cookie'     : 'JSESSIONID',
            'logout_url'       : 'https://www.hugendubel.de/de/account/logout',
            'reader_url'       : 'https://webreader.hugendubel.de/library/index.html',
            'register_url'     : 'https://bosh.pageplace.de/bosh/rest/registerhw',
            'devices_url'      : 'https://bosh.pageplace.de/bosh/rest/handshake/devices/list',
            'unregister_url'   : 'https://bosh.pageplace.de/bosh/rest/handshake/devices/delete',
            'upload_url'       : 'https://bosh.pageplace.de/bosh/rest/upload',
            'meta_url'         : 'https://bosh.pageplace.de/bosh/rest/meta',
            'cover_url'        : 'https://bosh.pageplace.de/bosh/rest/cover',
            'sync_data_url'    : 'https://bosh.pageplace.de/bosh/rest/sync-data?paths=publications,audiobooks',
            'delete_url'       : 'https://bosh.pageplace.de/bosh/rest/deletecontent',
            'inventory_url'    : 'https://bosh.pageplace.de/bosh/rest/inventory/delta',
            'downloadinfo_url' : 'https://bosh.pageplace.de/bosh/rest//cloud/downloadinfo/{}/{}/type/external-download'
        },
        23: {
            # osiander.de
            'client_id'        : 'webreader',
            'scope'            : 'SCOPE_BOSH',
            'token_url'        : 'https://www.osiander.de/auth/oauth2/token',
            'login_form_url'   : 'https://www.osiander.de/de.thalia.ecp.authservice.application/oauth2/login',
            'x_buchde.skin_id' : '17',
            'x_buchde.mandant_id' : '51',
            'auth_url'         : 'https://www.osiander.de/de.thalia.ecp.authservice.application/oauth2/authorize',
            'login_url'        : 'https://www.osiander.de/de.thalia.ecp.authservice.application/login.do',
            'login_form'       : {
                'username' : 'j_username',
                'password' : 'j_password',
                'extra'    : {
                    'login' : ''
                    }
             },
            'login_cookie'     : 'OAUTH-JSESSIONID',
            'revoke_url'       : 'https://www.osiander.de/auth/oauth2/revoke',
            'reader_url'       : 'https://webreader.mytolino.com/library/index.html#/mybooks/titles',
            'register_url'     : 'https://bosh.pageplace.de/bosh/rest/v2/registerhw',
            'devices_url'      : 'https://bosh.pageplace.de/bosh/rest/handshake/devices/list',
            'unregister_url'   : 'https://bosh.pageplace.de/bosh/rest/handshake/devices/delete',
            'upload_url'       : 'https://bosh.pageplace.de/bosh/rest/upload',
            'delete_url'       : 'https://bosh.pageplace.de/bosh/rest/deletecontent',
            'inventory_url'    : 'https://bosh.pageplace.de/bosh/rest/inventory/delta',
            'downloadinfo_url' : 'https://bosh.pageplace.de/bosh/rest/cloud/downloadinfo/{}/{}/type/external-download'
        },
        30: {
            # buecher.de
            'client_id'        : 'dte_ereader_app_01',
            'scope'            : 'ebook_library',
            'signup_url'       : 'https://www.buecher.de/go/my_dry/my_register_aos/',
            'profile_url'      : 'https://www.buecher.de/go/my_dry/my_login/receiver_object/my_login/',
            'token_url'        : 'https://www.buecher.de/oauth2/token',
            'revoke_url'       : 'https://www.buecher.de/oauth2/revoke',
            'auth_url'         : 'https://www.buecher.de/oauth2/authorize',
            'login_url'        : 'https://www.buecher.de/go/my_dry/my_login/',
            'login_form'       : {
                'username' : 'form[login]',
                'password' : 'form[password]',
                'extra'    : {
                    'form_send' : '1'
                }
            },
            'x_buecherde.skin_id' : 'de_dte_tolino',
            'login_cookie'     : 'session',
            'logout_url'       : 'https://www.buecher.de/go/my_dry/my_logout/',
            'reader_url'       : 'https://webreader.mytolino.com/library/',
            'register_url'     : 'https://bosh.pageplace.de/bosh/rest/v2/registerhw',
            'devices_url'      : 'https://bosh.pageplace.de/bosh/rest/handshake/devices/list',
            'unregister_url'   : 'https://bosh.pageplace.de/bosh/rest/handshake/devices/delete',
            'upload_url'       : 'https://bosh.pageplace.de/bosh/rest/upload',
            'meta_url'         : 'https://bosh.pageplace.de/bosh/rest/meta',
            'cover_url'        : 'https://bosh.pageplace.de/bosh/rest/cover',
            'sync_data_url'    : 'https://bosh.pageplace.de/bosh/rest/sync-data?paths=publications,audiobooks',
            'delete_url'       : 'https://bosh.pageplace.de/bosh/rest/deletecontent',
            'inventory_url'    : 'https://bosh.pageplace.de/bosh/rest/inventory/delta',
            'downloadinfo_url' : 'https://bosh.pageplace.de/bosh/rest//cloud/downloadinfo/{}/{}/type/external-download'
        }
    }

    def __init__(self, partner_id, use_device=False, confpath='.tolinoclientrc', libpath=''):
        sys.path.append(libpath)
        import requests
        self.partner_id = partner_id
        self.session = requests.session()
        self.use_device = use_device
        self.confpath = confpath
        self.client_id = ""

    def _debug(self, r):
        if logging.getLogger().getEffectiveLevel() >= logging.DEBUG:
            logging.debug('-------------------- HTTP response --------------------')
            logging.debug('status code: {}'.format(r.status_code))
            logging.debug('cookies: {}'.format(pformat(r.cookies)))
            logging.debug('headers: {}'.format(pformat(r.headers)))
            try:
                j = r.json()
                logging.debug('json: {}'.format(pformat(j)))
            except:
                logging.debug('text: {}'.format(r.text))
            logging.debug('-------------------------------------------------------')

    def login(self, username, password):
        s = self.session
        c = self.partner_settings[self.partner_id]

        config = ConfigParser()
        config.read(self.confpath)
        self.client_id = config.get('Defaults', 'client_id') or c['client_id']

        if self.use_device:
            TolinoCloud.hardware_id = username
            if self.partner_id == 80:
                self.access_token = password
                return

            r = s.post(c['token_url'], data = {
                'client_id'    : self.client_id,
                'grant_type'   : 'refresh_token',
                'refresh_token': password,
                'scope'        : c['scope'],
                }, verify=True, allow_redirects=False)
            self._debug(r)
            try:
                j = r.json()
                self.access_token = j['access_token']
                self.refresh_token = j['refresh_token']
                self.token_expires = int(j['expires_in'])
                #Store new refresh token
                config.set('Defaults', 'password', self.refresh_token)
                with open(self.confpath, 'w') as f:
                    config.write(f)
            except:
                raise TolinoException('oauth access token request failed.')
            return

        # Login with partner site
        # to retrieve site's cookies within browser session
        if 'login_form_url' in c:
            r = s.get(c['login_form_url'], params = {
                'client_id'     : self.client_id,
                'response_type' : 'code',
                'scope'         : c['scope'],
                'redirect_uri'  : c['reader_url'],
                'x_buchde.skin_id': c['x_buchde.skin_id'],
                'x_buchde.mandant_id' : c['x_buchde.mandant_id']
            }, verify=True, allow_redirects=False)
        data = c['login_form']['extra']
        data[c['login_form']['username']] = username
        data[c['login_form']['password']] = password
        r = s.post(c['login_url'], data=data, verify=True)
        logging.debug(data)
        logging.debug(c['login_cookie'])
        self._debug(r)
        if not c['login_cookie'] in s.cookies:
            raise TolinoException('login to {} failed.'.
                format(self.partner_name[self.partner_id]))
        auth_code = ""
        if 'tat_url' in c:
            try:
                r = s.get(c['tat_url'], verify=True)
                self._debug(r)
                b64 = re.search(r'\&tat=(.*?)%3D', r.text).group(1)
                self.access_token = base64.b64decode(b64+'==').decode('utf-8')
            except:
                raise TolinoException('oauth access token request failed.')
        else:
            # Request OAUTH code
            params = {
                'client_id'     : self.client_id,
                'response_type' : 'code',
                'scope'         : c['scope'],
                'redirect_uri'  : c['reader_url']
            }
            if 'login_form_url' in c:
                params['x_buchde.skin_id'] = c['x_buchde.skin_id']
                params['x_buchde.mandant_id'] = c['x_buchde.mandant_id']
            r = s.get(c['auth_url'], params=params, verify=True, allow_redirects=False)
            self._debug(r)
            try:
                url = r.headers['Location']
                if '#' in url:
                 url = url.split('#', 1)[-1] # weltbild sends back /index.html#/real/page?code=
                params = parse_qs(urlparse(url).query)
                auth_code = params['code'][0]
            except:
                raise TolinoException('oauth code request failed.')

            # Fetch OAUTH access token
            r = s.post(c['token_url'], data = {
                'client_id'    : self.client_id,
                'grant_type'   : 'authorization_code',
                'code'         : auth_code,
                'scope'        : c['scope'],
                'redirect_uri' : c['reader_url']
            }, verify=True, allow_redirects=False)
            self._debug(r)
            try:
                j = r.json()
                self.access_token = j['access_token']
                self.refresh_token = j['refresh_token']
                self.token_expires = int(j['expires_in'])
            except:
                raise TolinoException('oauth access token request failed.')

    def logout(self):
        if self.use_device:
            return
        s = self.session;
        c = self.partner_settings[self.partner_id]

        if 'revoke_url' in c:
            r = s.post(c['revoke_url'],
                data = {
                    'client_id'  : self.client_id,
                    'token_type' : 'refresh_token',
                    'token'      : self.refresh_token
                }
            )
            self._debug(r)
            if r.status_code != 200:
                raise TolinoException('logout failed.')
        else:
            r = s.post(c['logout_url'])
            self._debug(r)
            if r.status_code != 200:
                raise TolinoException('logout failed.')


    def register(self):
        if self.use_device:
            return
        s = self.session;
        c = self.partner_settings[self.partner_id]

        # Register our hardware
        r = s.post(c['register_url'],
              data = json.dumps({'hardware_name':'tolino sync reader'}),
              headers = {
                'content-type': 'application/json',
                't_auth_token': self.access_token,
                'hardware_id' : TolinoCloud.hardware_id,
                'reseller_id' : str(self.partner_id),
                'client_type': 'TOLINO_WEBREADER',
                'client_version': '4.4.1',
                'hardware_type': 'HTML5'
              }
        )
        self._debug(r)
        if r.status_code != 200:
            raise TolinoException('register {} failed.'.format(TolinoCloud.hardware_id))

    def unregister(self, device_id = hardware_id):
        if self.use_device:
            return
        s = self.session;
        c = self.partner_settings[self.partner_id]

        r = s.post(c['unregister_url'],
            data = json.dumps({
                'deleteDevicesRequest':{
                    'accounts' : [ {
                        'auth_token'  : self.access_token,
                        'reseller_id' : self.partner_id
                    } ],
                    'devices'  : [ {
                        'device_id'   : device_id,
                        'reseller_id' : self.partner_id
                    } ]
                }
            }),
            headers = {
                'content-type': 'application/json',
                't_auth_token': self.access_token,
                'reseller_id' : str(self.partner_id)
            }
        )
        self._debug(r)
        if r.status_code != 200:
            try:
                j = r.json()
                raise TolinoException('unregister {} failed: {}'.format(device_id, j['ResponseInfo']['message']))
            except KeyError:
                raise TolinoException('unregister {} failed: reason unknown.'.format(device_id))

    def devices(self):
        s = self.session;
        c = self.partner_settings[self.partner_id]

        r = s.post(c['devices_url'],
            data = json.dumps({
                'deviceListRequest':{
                    'accounts' : [ {
                        'auth_token'  : self.access_token,
                        'reseller_id' : self.partner_id
                    } ]
                }
            }),
            headers = {
                'content-type': 'application/json',
                't_auth_token': self.access_token,
                'reseller_id'        : str(self.partner_id)
            }
        )
        self._debug(r)
        if r.status_code != 200:
            raise TolinoException('device list request failed.')

        try:
            devs = []
            j = r.json()
            for item in j['deviceListResponse']['devices']:
                devs.append({
                    'id'         : item['deviceId'],
                    'name'       : item['deviceName'],
                    'type'       : {
                        'unknown_imx50_rdp_1' : 'tolino shine',
                        'tolino_vison'        : 'tolino vision',
                        'HTML5_1'             : 'web browser'
                        }.get(item['deviceType'], item['deviceType']),
                    'partner'    : int(item['resellerId']),
                    'registered' : int(item['deviceRegistered']),
                    'lastusage'  : int(item['deviceLastUsage'])
                })
            return devs
        except:
            raise TolinoException('device list request failed.')

    def _parse_metadata(self, j):
        try:
            md = {
                'partner'     : int(j['resellerId']),
                'id'          : j['epubMetaData']['identifier'],
                'title'       : j['epubMetaData']['title'],
                'subtitle'    : j['epubMetaData']['subtitle'],
                'author'      : [a['name'] for a in j['epubMetaData']['author']],
                'mime'        : j['epubMetaData']['deliverable'][0]['contentFormat'],
                'type'        : j['epubMetaData']['type'].lower(),
                'purchased'   : int(j['epubMetaData']['deliverable'][0]['purchased'])
            }
            if j['epubMetaData']['issued']:
                md['issued'] = int(j['epubMetaData']['issued'])
            return md
        except:
            raise TolinoException('could not parse metadata')

    def inventory(self):
        s = self.session;
        c = self.partner_settings[self.partner_id]

        r = s.get(c['inventory_url'],
            params = {'strip': 'true'},
            headers = {
                't_auth_token' : self.access_token,
                'hardware_id'  : TolinoCloud.hardware_id,
                'reseller_id'  : str(self.partner_id)
            }
        )
        self._debug(r)
        if r.status_code != 200:
            raise TolinoException('inventory list request failed.')

        try:
            inv = []
            j = r.json()
            # edata = own documents uploaded to Tolino Cloud
            for item in j['PublicationInventory']['edata']:
                inv.append(self._parse_metadata(item))
            # ebook = purchased ebooks in Tolino Cloud
            for item in j['PublicationInventory']['ebook']:
                inv.append(self._parse_metadata(item))
            return inv
        except:
            raise TolinoException('inventory list request failed.')

    def upload(self, filename, name = None, ext = None):
        s = self.session;
        c = self.partner_settings[self.partner_id]

        if name is None:
            name = filename.split('/')[-1]
        if ext is None:
            ext = filename.split('.')[-1]

        mime = {
            'pdf'  : 'application/pdf',
            'epub' : 'application/epub+zip'
        }.get(ext.lower(), 'application/pdf')

        r = s.post(c['upload_url'],
            files = [('file', (name, open(filename, 'rb'), mime))],
            headers = {
                't_auth_token' : self.access_token,
                'hardware_id'  : TolinoCloud.hardware_id,
                'reseller_id'         : str(self.partner_id)
            }
        )
        self._debug(r)
        if r.status_code != 200:
            raise TolinoException('file upload failed.')

        try:
            j = r.json()
            return j['metadata']['deliverableId']
        except:
            raise TolinoException('file upload failed.')

    def add_cover(self, book_id, filename, name = None, ext = None):
        s = self.session;
        c = self.partner_settings[self.partner_id]

        if 'cover_url' not in c:
            raise TolinoException('no cover url defined for this provider.')
        
        if name is None:
            name = filename.split('/')[-1]

        if ext is None:
            ext = filename.split('.')[-1]
        
        mime = {
            'png': 'image/png',
            'jpeg': 'image/jpeg',
            'jpg': 'image/jpeg'
        }.get(ext.lower(), 'application/jpeg')

        r = s.post(c['cover_url'],
            files = [('file', ('1092560016', open(filename, 'rb'), mime))],
            data = {'deliverableId': book_id},
            headers = {
                't_auth_token' : self.access_token,
                'hardware_id'  : TolinoCloud.hardware_id,
                'reseller_id'         : str(self.partner_id)
            }
        )
        self._debug(r)
        if r.status_code != 200:
            raise TolinoException('cover upload failed.')

    
    def metadata(self, book_id, title=None, subtitle=None, author=None, publisher=None, isbn=None, edition=None,
                issued=None, language=None):
        s = self.session;
        c = self.partner_settings[self.partner_id]

        if 'meta_url' not in c:
            raise TolinoException('no meta url defined for this provider.')

        b = c['meta_url'] + '/?deliverableId={book_id}'.format(book_id=book_id)
        r = s.get(b,
                  headers={
                      't_auth_token': self.access_token,
                      'hardware_id': TolinoCloud.hardware_id,
                      'reseller_id': str(self.partner_id)
                  }
                  )

        meta = r.json()

        self._debug(r)

        if title is not None:
            meta['metadata']['title'] = str(title)

        if subtitle is not None:
            meta['metadata']['subtitle'] = str(subtitle)

        if author is not None:
            meta['metadata']['author'] = str(author)

        if publisher is not None:
            meta['metadata']['publisher'] = str(publisher)

        if isbn is not None:
            meta['metadata']['isbn'] = str(isbn)

        if edition is not None:
            meta['metadata']['edition'] = int(edition)

        if issued is not None:
            meta['metadata']['issued'] = issued.timestamp()

        if language is not None:
            meta['metadata']['language'] = str(language)

        payload = {
            'uploadMetaData': meta['metadata']
        }

        r = s.put(b,
                  data=json.dumps(payload),
                  headers={
                      'content-type': 'application/json',
                      't_auth_token': self.access_token,
                      'hardware_id': TolinoCloud.hardware_id,
                      'reseller_id': str(self.partner_id)
                  }
                  )
        self._debug(r)
        if r.status_code != 200:
            raise TolinoException('meta data update failed.')

        try:
            return meta['metadata']['deliverableId']
        except:
            raise TolinoException('meta data update failed.')


    def add_to_collection(self, book_id, collection_name):
        s = self.session;
        c = self.partner_settings[self.partner_id]

        if 'sync_data_url' not in c:
            raise TolinoException('no meta url defined for this provider.')

        payload = {
            "revision":None,
            "patches":[
                {
                    "op":"add",
                    "value":{
                        #"revision":None,
                        "modified":round(time.time() * 1000), #Milliseconds
                        "name":collection_name,
                        "category":"collection",
                        #"transientId":base64.b64encode(collection_name.encode('ascii')).decode('ascii') #was used in legacy web client
                    },
                    "path":"/publications/{book_id}/tags".format(book_id=book_id)
                }
            ]
        }

        r = s.patch(c['sync_data_url'],
                    data=json.dumps(payload),
                    headers={
                        'content-type': 'application/json',
                        't_auth_token': self.access_token,
                        'hardware_id': TolinoCloud.hardware_id,
                        'reseller_id': str(self.partner_id),
                        'client_type': 'TOLINO_WEBREADER'
                    }
                )
        self._debug(r)
        if r.status_code != 200:
            raise TolinoException('collection update failed.')


    def delete(self, id):
        s = self.session;
        c = self.partner_settings[self.partner_id]

        r = s.get(c['delete_url'],
            params = {
                'deliverableId': id
            },
            headers = {
                't_auth_token' : self.access_token,
                'hardware_id'  : TolinoCloud.hardware_id,
                'reseller_id'   : str(self.partner_id)
            }
        )
        self._debug(r)
        if r.status_code != 200:
            try:
                j = r.json()
                raise TolinoException('delete {} failed: {}'.format(id, j['ResponseInfo']['message']))
            except KeyError:
                raise TolinoException('delete {} failed: reason unknown.'.format(id))

    def download_info(self, id):
        s = self.session;
        c = self.partner_settings[self.partner_id]

        b64 = base64.b64encode(bytes(id, 'utf-8')).decode('utf-8')
        r = s.get(c['downloadinfo_url'].format(b64, b64),
            headers = {
                't_auth_token' : self.access_token,
                'hardware_id'  : TolinoCloud.hardware_id,
                'reseller_id'  : str(self.partner_id)
            }
        )
        self._debug(r)
        if r.status_code != 200:
            raise TolinoException('download info request failed.')

        j = r.json()
        url = j['DownloadInfo']['contentUrl']
        return {
            'url'      : url,
            'filename' : url.split('/')[-1],
            'filetype' : j['DownloadInfo']['format'],
        }

    def download(self, path, id):
        s = self.session;
        c = self.partner_settings[self.partner_id]

        di = self.download_info(id)

        r = s.get(di['url'],
            stream=True,
            headers = {
                't_auth_token' : self.access_token,
                'hardware_id'  : TolinoCloud.hardware_id,
                'reseller_id'  : str(self.partner_id)
            }
        )
        self._debug(r)
        if r.status_code != 200:
            try:
                j = r.json()
                raise TolinoException('download request failed: {}'.format(j['ResponseInfo']['message']))
            except KeyError:
                raise TolinoException('download request : reason unknown.')


        filename = path + '/' + di['filename'] if path else di['filename']
        with open(filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
            f.flush()

        return filename

    def set_token(self, token):
        self.access_token = token
