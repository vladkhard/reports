import couchdb
import os.path
import csv
import os
import os.path
import logging
from couchdb.design import ViewDefinition

from reports.design import (
    bids_owner_date,
    tenders_owner_date
)
from reports.helpers import (
    value_currency_normalize
)

views = [bids_owner_date, tenders_owner_date]
logger = logging.getLogger(__name__)

class BaseUtility(object):

    def __init__(self, config):
        self.config = config
        self.db = couchdb.Database(
            self.config.db_url,
            session=couchdb.Session(retry_delays=range(10))
        )
        self.adb = couchdb.Database(
            self.config.admin_db_url,
            session=couchdb.Session(retry_delays=range(10))
        )
        ViewDefinition.sync_many(self.adb, views)

    def get_payment(self, value):
        for index, threshold in enumerate(self.config.thresholds):
            if value <= threshold:
                return self.config.payments[index]
        return self.config.payments[-1]

    def _get_response(self):
        self._sync_views()

        startkey = (self.config.broker, self.config.start_date)
        if not self.config.end_date:
            endkey = (self.config.broker, "9999-12-30T00:00:00.000000")
        else:
            endkey = (self.config.broker, self.config.end_date)
        self.response = self.db.iterview(
            self.view, 1000,
            startkey=startkey,
            endkey=endkey
        )

    def write_csv(self):
        if not self.headers:
            raise ValueError
        path = os.path.dirname(os.path.abspath(self.config.out_file))
        if not os.path.exists(path):
            os.makedirs(path)
        with open(self.config.out_file, 'w') as out_file:
            writer = csv.writer(out_file)
            writer.writerow(self.headers)
            for row in self.rows():
                writer.writerow(row)

    def run(self):
        self.get_response()
        self.out_name()
        self.write_csv()


class BaseBidsUtility(BaseUtility):

    view = 'report/bids_owner_date'


class BaseTendersUtility(BaseUtility):

    view = 'report/tenders_owner_date'


class RowMixin(object):

    def rows(self, response):
        for resp in response:
            row = self.row(resp["value"])
            if row:
                yield row


class RowInvoiceMixin(object):

    def rows(self):
        for resp in self.response:
            self.row(resp['value'])
        for row in [
            self.payments,
            self.counter,
            [c * v for c, v in zip(self.counter, self.config.payments)]
        ]:
            yield row


class HeadersToRowMixin(object):

    def record(self, row):
        record = {header: row.get(header, '') for header in self.headers}
        if str(record['currency']) != 'UAH':
            value = record['value']
            record['value'], record['rate'] = value_currency_normalize(
                float(record['value']),
                record['currency'],
                record['startdate']
            )
            logger.info('Changed value {} -> {} by exchange rate'
                        ' {} ({})'.format(value, record['value'],
                                          record['rate'], record['startdate']))
        return [str(v) for v in record.values()]
