import couchdb
import os.path
import csv
import os
import yaml
import requests
import requests_cache
from requests.exceptions import RequestException
from yaml.scanner import ScannerError
from couchdb.design import ViewDefinition

from reports.log import getLogger
from reports.config import Config
from reports.design import bids_owner_date, tenders_owner_date, jsonpatch
from reports.helpers import prepare_report_interval, prepare_result_file_name


VIEWS = [bids_owner_date, tenders_owner_date]
NEW_ALG_DATE = "2017-08-16"

requests_cache.install_cache('audit_cache')


class BaseUtility(object):

    def __init__(
            self, broker, period, config,
            timezone="Europe/Kiev", operation=""
            ):
        self.broker = broker
        self.period = period
        self.config_path = config
        self.timezone = timezone
        self.operation = operation
        self.threshold_date = '2017-01-01T00:00+02:00'
        self.config = Config(config, self.operation)
        self.start_date, self.end_date = prepare_report_interval(
            self.period
        )
        self.connect_db()
        self.Logger = getLogger("BILLING")

    def connect_db(self):
        self.db = couchdb.Database(
            self.config.db_url,
            session=couchdb.Session(retry_delays=range(10))
        )

        self.adb = couchdb.Database(
            self.config.adb_url,
            session=couchdb.Session(retry_delays=range(10))
        )

    def row(self):
        raise NotImplemented

    def rows(self):
        raise NotImplemented

    def get_payment(self, value, year=2017):
        p = self.config.payments(grid=year)
        for index, threshold in enumerate(self.config.thresholds):
            if value <= threshold:
                return p[index]
        return p[-1]

    def _sync_views(self):
        ViewDefinition.sync_many(self.adb, VIEWS)
        _id = '_design/report'
        original = self.adb.get(_id)
        original['views']['lib'] = {
            'jsonpatch': jsonpatch
        }
        self.adb.save(original)

    @property
    def response(self):
        self._sync_views()
        if not self.view:
            raise NotImplemented
        return self.db.iterview(
            self.view,
            1000,
            startkey=(self.broker, self.start_date),
            endkey=(self.broker, self.end_date))

    def write_csv(self):
        if not self.headers:
            raise ValueError
        destination = prepare_result_file_name(self)
        if not os.path.exists(os.path.dirname(destination)):
            os.makedirs(os.path.dirname(destination))

        with open(destination, 'w') as out_file:
            writer = csv.writer(out_file)
            writer.writerow(self.headers)
            for row in self.rows():
                writer.writerow(row)

    def run(self):
        self.Logger.info("Start generating")
        self.write_csv()


class BaseBidsUtility(BaseUtility):

    def __init__(
            self, broker, period, config,
            timezone="Europe/Kiev", operation="bids"
            ):
        self.view = 'report/bids_owner_date'
        super(BaseBidsUtility, self).__init__(
            broker, period, config, operation=operation, timezone=timezone)

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

    def __init__(
            self, broker, period, config,
            timezone="Europe/Kiev",
            operation='tenders'
            ):
        self.view = 'report/tenders_owner_date'
        super(BaseTendersUtility, self).__init__(
            broker, period, config, operation=operation, timezone=timezone)

        # TODO: kinds

        # parser.add_argument(
        #     '--kind',
        #     metavar='Kind',
        #     action=Kind,
        #     help='Kind filtering functionality. '
        #          'Usage: --kind <include, exclude, one>=<kinds>'
        # )
        # self.kinds = args.kind
