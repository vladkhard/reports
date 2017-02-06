import couchdb
import os.path
import csv
import os
import os.path
import logging
from collections import OrderedDict
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

    module = 'base'

    def __init__(self, config):
        self.config = config
        setattr(self.config, 'module', self.__class__.module)
        self.db = couchdb.Database(
            self.config.db_url,
            session=couchdb.Session(retry_delays=range(10))
        )
        self.adb = couchdb.Database(
            self.config.admin_db_url,
            session=couchdb.Session(retry_delays=range(10))
        )
        ViewDefinition.sync_many(self.adb, views)
        logger.info('Start {}. Params: {} -> {}--{}'.format(self.module,
                                                            self.config.broker,
                                                            self.config.start_date(),
                                                            self.config.end_date()))

    def get_payment(self, value):
        for index, threshold in enumerate(self.config.thresholds):
            if value <= threshold:
                return self.config.payments[index]
        return self.config.payments[-1]

    @property
    def response(self):
        date = self.config.end_date()
        if not date:
            date = "9999-12-30T00:00:00.000000"
        return self.db.iterview(
            self.view, 1000,
            startkey=(self.config.broker, self.config.start_date()),
            endkey=(self.config.broker, date)
        )


class BaseBidsGenerator(BaseUtility):

    view = 'report/bids_owner_date'


class BaseTendersGenerator(BaseUtility):

    view = 'report/tenders_owner_date'


class RowMixin(object):

    @property
    def rows(self):
        for resp in self.response:
            row = self.row(resp["value"])
            if row:
                yield row


class RowInvoiceMixin(object):

    @property
    def rows(self):
        for resp in self.response:
            self.row(resp['value'])
        for row in [
            self.config.payments,
            self.counter,
            [c * v for c, v in zip(self.counter, self.config.payments)]
        ]:
            yield row


class HeadersToRowMixin(object):

    def record(self, row):
        record = OrderedDict()
        for f in self.fields:
            record[f] = row.get(f, '')
        if str(row[u'currency']) != 'UAH':
            value = row['value']
            record['value'], record['rate'] = value_currency_normalize(
                float(record['value']),
                record['currency'],
                row['startdate']
            )
            logger.info('Changed value {} -> {} by exchange rate'
                        ' {} ({})'.format(value, record['value'],
                                          record['rate'], row['startdate']))
        return record


class CSVMixin(object):

    def run(self):
        if not self.headers:
            raise ValueError
        path = os.path.dirname(os.path.abspath(self.config.out_file))
        if not os.path.exists(path):
            os.makedirs(path)
        with open(self.config.out_file, 'w') as out_file:
            writer = csv.writer(out_file)
            writer.writerow(self.headers)
            for row in self.rows:
                writer.writerow(row)
