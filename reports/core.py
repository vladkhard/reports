import couchdb
import couchdb.design
import os.path
import csv
import os
import os.path
import arrow
import time
import yaml
import requests
import argparse
import requests_cache
from requests.exceptions import RequestException
from yaml.scanner import ScannerError
from dateutil.parser import parse
from config import Config
from design import bids_owner_date, tenders_owner_date
from couchdb.design import ViewDefinition
from logging import getLogger
from reports.helpers import get_cmd_parser, create_db_url, Kind, Status


views = [bids_owner_date, tenders_owner_date]

requests_cache.install_cache('audit_cache')
NEW_ALG_DATE = "2017-08-16"


class BaseUtility(object):

    def __init__(self, operation, rev=False):
        self.rev = rev
        self.headers = None
        self.operation = operation
        self.threshold_date = '2017-01-01T00:00+02:00'

    def _initialize(self, broker, period, config, tz=''):
        self.broker = broker
        self.config = Config(config, self.rev)
        self.start_date = ''
        self.end_date = ''
        self.timezone = tz
        self.payments = []

        if period:
            if len(period) == 1:
                self.start_date = self.convert_date(period[0])
            if len(period) == 2:
                self.start_date = self.convert_date(period[0])
                self.end_date = self.convert_date(period[1])
        self.get_db_connection()
        self.Logger = getLogger(self.operation)
        self.payments = self.config.payments(True)
        self.payments_before = self.config.payments(False)

    def get_db_connection(self):
        host = self.config.get_option('db', 'host')
        port = self.config.get_option('db', 'port')
        user_name = self.config.get_option('user', 'username')
        user_password = self.config.get_option('user', 'password')

        db_name = self.config.get_option('db', 'name')

        self.db = couchdb.Database(
            create_db_url(host, port, user_name, user_password, db_name),
            session=couchdb.Session(retry_delays=range(10))
        )

        a_name = self.config.get_option('admin', 'username')
        a_password = self.config.get_option('admin', 'password')
        self.adb = couchdb.Database(
            create_db_url(host, port, a_name, a_password, db_name)
        )

    def row(self):
        raise NotImplemented

    def rows(self):
        raise NotImplemented

    def convert_date(self, date):
        if len(date) < 3:
            date = time.strftime("%Y-%m-") + date
        date = arrow.get(parse(date), self.timezone)
        res = date.to('UTC').strftime("%Y-%m-%dT%H:%M:%S.%f")
        return res

    def get_payment(self, value, before_2017=False):
        p = self.payments_before if before_2017 else self.payments
        for index, threshold in enumerate(self.config.thresholds):
            if value <= threshold:
                return p[index]
        return p[-1]

    def _sync_views(self):
        ViewDefinition.sync_many(self.adb, views)

    def get_response(self):
        self._sync_views()

        if not self.view:
            raise NotImplemented

        if not self.start_date and not self.end_date:
            self.response = self.db.iterview(
                self.view, 1000,
                startkey=(self.broker, ""),
                endkey=(self.broker, "9999-12-30T00:00:00.000000")
            )
        elif self.start_date and not self.end_date:
            self.response = self.db.iterview(
                self.view, 1000,
                startkey=(self.broker, self.start_date),
                endkey=(self.broker, "9999-12-30T00:00:00.000000")
            )
        else:
            self.response = self.db.iterview(
                self.view, 1000,
                startkey=(self.broker, self.start_date),
                endkey=(self.broker, self.end_date)
            )

    def out_name(self):
        start = ''
        end = ''
        if self.start_date:
            start = arrow.get(parse(self.start_date))\
                .to('Europe/Kiev').strftime("%Y-%m-%d")
        if self.end_date:
            end = arrow.get(parse(self.end_date))\
                .to('Europe/Kiev').strftime("%Y-%m-%d")
        name = "{}@{}--{}-{}.csv".format(
            self.broker,
            start,
            end,
            self.operation
        )
        self.put_path = os.path.join(self.config.out_path, name)

    def write_csv(self):
        if not self.headers:
            raise ValueError
        if not os.path.exists(os.path.dirname(os.path.abspath(self.put_path))):
            os.makedirs(os.path.dirname(os.path.abspath(self.put_path)))
        with open(self.put_path, 'w') as out_file:
            writer = csv.writer(out_file)
            writer.writerow(self.headers)
            for row in self.rows():
                writer.writerow(row)

    def run(self):
        self.get_response()
        self.out_name()
        self.write_csv()


class BaseBidsUtility(BaseUtility):

    def __init__(self, operation):
        super(BaseBidsUtility, self).__init__(operation)
        self.view = 'report/bids_owner_date'
        self.skip_bids = set()
        self.initial_bids = []
        self.initial_bids_for = ''
        parser = get_cmd_parser()
        args = parser.parse_args()
        self._initialize(
            args.broker,
            args.period,
            args.config,
            args.timezone
        )

    def get_initial_bids(self, audit, tender_id):
        url = audit is not None and audit.get('url')
        if not url:
            self.Logger.fatal('Invalid audit for tender id={}'.format(tender_id))
            self.initial_bids = []
            return
        try:
            yfile = yaml.load(requests.get(url).text)
            self.initial_bids = yfile['timeline']['auction_start']['initial_bids']
            self.initial_bids_for = yfile.get('tender_id', yfile.get('id', ''))
            return self.initial_bids
        except (ScannerError, KeyError, TypeError) as e:
            msg = 'Falied to scan audit file'\
                    ' for tender id={}. Error {}'.format(tender_id, e)
            self.Logger.error(msg)
        except RequestException as e:
            msg = "Request falied at getting audit file"\
                    "for tender id={0}  with error '{1}'".format(tender_id, e)
            self.Logger.info(msg)
        self.initial_bids = []

    def bid_date_valid(self, bid_id):
        for bid in self.initial_bids:
            if bid['date'] < "2016-04-01":
                self.skip_bids.add(bid['bidder'])
        if bid_id in self.skip_bids:
            self.Logger.info('Skipped fetched early bid: %s', bid_id)
            return False
        return True


class BaseTendersUtility(BaseUtility):

    def __init__(self, operation):
        super(BaseTendersUtility, self).__init__(operation, rev=True)
        self.view = 'report/tenders_owner_date'
        self.tenders_to_ignore = set()
        self.lots_to_ignore = set()
        parser = get_cmd_parser()
        parser.add_argument(
            '--kind',
            metavar='Kind',
            action=Kind,
            help='Kind filtering functionality. '
                 'Usage: --kind <include, exclude, one>=<kinds>'
        )
        parser.add_argument(
            '--status',
            metavar='status',
            action=Status,
            help='Tenders statuses filtering functionality. '
                 'Usage: --status <include, exclude, one>=<statuses>'
        )

        parser.add_argument(
            '-i',
            '--ignore',
            dest='ignore',
            type=argparse.FileType('r'),
            help='File with ids that should be skipped'
        )

        parser.add_argument(
            '--skip-columns',
            dest='columns',
            nargs='+',
            default=[],
            help='Columns to skip')

        args = parser.parse_args()
        self.ignore = set()
        self._initialize(
            args.broker,
            args.period,
            args.config,
            args.timezone
        )
        self.kinds = args.kind
        self.statuses = args.status['statuses']
        self.status_action = args.status['action']
        self.skip_cols = args.columns
        if args.ignore:
            self.ignore = [line.strip('\n') for line in args.ignore.readlines()]

    def check_status(self, tender_status, lot_status):
        if lot_status:
            if lot_status == 'active':
                if tender_status not in self.statuses:
                    return True
            elif lot_status not in self.statuses:
                return True
        else:
            if tender_status not in self.statuses:
                return True
        return False
