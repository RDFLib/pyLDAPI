from os.path import dirname, realpath, join, abspath

APP_DIR = dirname(dirname(realpath(__file__)))
TEMPLATES_DIR = join(dirname(dirname(abspath(__file__))), 'view', 'templates')
STATIC_DIR = join(dirname(dirname(abspath(__file__))), 'view', 'static')
LOGFILE = APP_DIR + '/flask.log'
DEBUG = True

XML_API_URL_SITESET = 'http://dbforms.ga.gov.au/www/a.entities_api.SearchEntities' \
                        '?pOrder=ENO&pPageNo={0}&pNoOfRecordsPerPage={1}'
XML_API_URL_SITE = 'http://dbforms.ga.gov.au/www/a.entities_api.entities?pEno={0}'
# XML_API_URL_NETWORKSET = ''
# XML_API_URL_NETWORK = ''

XML_API_URL_SITESET_DATE_RANGE = \
    'http://dbforms.ga.gov.au/www/a.entities_api.SearchEntities' \
    '?pOrder=ENO&pPageNo={0}&pNoOfRecordsPerPage={1}&pStartEntryDate={2}' \
    '&pEndEntryDate={3}'

XML_API_URL_SITES_TOTAL_COUNT = 'http://dbforms.ga.gov.au/www/a.entities_api.get_total_number_records'
XML_API_URL_SITES_TOTAL_COUNT_DATE_RANGE = 'http://dbforms.ga.gov.au/www/a.entities_api.get_Number_Modified?' \
                                           'pModifiedFromDate={0}&pModifiedToDate={1}'
PAGE_SIZE_DEFAULT = 100
PAGE_SIZE_MAX = 10000

ADMIN_EMAIL = 'dataman@ga.gov.au'

URI_NETWORK_CLASS = 'http://pid.geoscience.gov.au/def/ont/ga/pdm#SiteNetwork'
URI_NETWORK_INSTANCE_BASE = 'http://pid.geoscience.gov.au/network/'
URI_SITE_CLASS = 'http://pid.geoscience.gov.au/def/ont/ga/pdm#Site'
URI_SITE_INSTANCE_BASE = 'http://pid.geoscience.gov.au/site/'

GOOGLE_MAPS_API_KEY_EMBED = 'AIzaSyDhuFCoJynhhQT7rcgKYzk3i7K77IEwjO4'
GOOGLE_MAPS_API_KEY = 'AIzaSyCUDcjVRsIHVHpv53r7ZnaX5xzqJbyGk58'
