import argparse
import iso8601
import requests
import json
import requests_cache
import re
import arrow
import time
from datetime import date
from dateutil.parser import parse


requests_cache.install_cache('exchange_cache')


def create_arguments():
    parser = argparse.ArgumentParser(
        description="Openprocurement Billing"
    )
    report = parser.add_argument_group('Report', 'Report parameters')
    report.add_argument(
        '-c',
        '--config',
        dest='config',
        required=True,
        help="Path to config file. Required"
    )
    report.add_argument(
        '-b',
        '--broker',
        dest='broker',
        required=True,
        help='Broker name. Required'
    )
    report.add_argument(
        '-p',
        '--period',
        nargs='+',
        dest='period',
        default=[],
        help='Specifies period for billing report.\n '
             'By default report will be generated from all database'
    )
    report.add_argument(
        '-t',
        '--timezone',
        dest='timezone',
        default='Europe/Kiev',
        help='Timezone. Default "Europe/Kiev"'
    )
    report.add_argument(
        '--include-cancelled',
        action='store_true',
        default=False
    )
    return parser


def thresholds_headers(cthresholds):
    prev_threshold = None
    result = []
    thresholds = [str(t / 1000) for t in cthresholds]
    for t in thresholds:
        if not prev_threshold:
            result.append("<= " + t)
        else:
            result.append(">" + prev_threshold + "<=" + t)
        prev_threshold = t
    result.append(">" + thresholds[-1])
    return result


def value_currency_normalize(value, currency, date):
    if not isinstance(value, (float, int)):
        raise ValueError
    base_url = 'http://bank.gov.ua/NBUStatService'\
        '/v1/statdirectory/exchange?date={}&json'.format(
            iso8601.parse_date(date).strftime('%Y%m%d')
        )
    resp = requests.get(base_url).text.encode('utf-8')
    doc = json.loads(resp)
    if currency == u'RUR':
        currency = u'RUB'
    rate = filter(lambda x: x[u'cc'] == currency, doc)[0][u'rate']
    return value * rate, rate


def create_db_url(host, port, user, passwd, db_name=''):
    up = ''
    if user and passwd:
        up = '{}:{}@'.format(user, passwd)
    url = 'http://{}{}:{}'.format(up, host, port)
    if db_name:
        url += '/{}'.format(db_name)
    return url


def get_operations(name):
    words = re.findall(r'\w+', name)
    return [w for w in words
            if w in ['bids', 'invoices', 'refunds', 'tenders']]


def get_send_args_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-c',
        '--config',
        dest='config',
        required=True,
        help='Path to configuration file'
    )
    parser.add_argument(
        '-f',
        '--file',
        nargs='+',
        dest='files',
        help='Files to send'
    )
    parser.add_argument(
        '-n',
        '--notify',
        action='store_true',
        help='Notification flag'
    )
    parser.add_argument(
        '-e',
        '--exists',
        action='store_true',
        help='Send mails from existing directory; timestamp required'
    )
    parser.add_argument(
        '-t',
        '--timestamp',
        help='Initial run timestamp'
    )
    parser.add_argument(
        '-b',
        '--brokers',
        nargs='+',
        help='Recipients'
    )
    parser.add_argument(
        '--test-mail',
        nargs='+',
        dest='test',
        help='Send email test'
    )

    return parser


def convert_date(date, from_tz='Europe/Kiev', to_tz='UTC'):
    date = arrow.get(parse(date), from_tz)
    return date.to(to_tz).strftime("%Y-%m-%dT%H:%M:%S.%f")


def generation_period():
    end = date.today().replace(day=1)
    if end.month == 1:
        start = end.replace(year=end.year-1, month=12, day=1)
    else:
        start = end.replace(month=end.month-1, day=1)
    return start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d')
