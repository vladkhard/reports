import logging
from reports.core import (
    BaseBidsGenerator,
    RowMixin,
    RowInvoiceMixin,
    HeadersToRowMixin,
    CSVMixin
)
from reports.helpers import (
    thresholds_headers
)

logger = logging.getLogger(__name__)

headers = [
    "tender",
    "tenderID",
    "lot",
    "value",
    "currency",
    "bid",
    'rate',
    "bill"
]


class Bids(BaseBidsGenerator,
           RowMixin,
           HeadersToRowMixin,
           CSVMixin
           ):
    fields = headers
    headers = headers
    module = 'bids'

    def row(self, row):
        record = self.record(row)
        record['bill'] = self.get_payment(record['value'])
        if self.config.include_cancelled and row.get('cancelled', ''):
            record['bill'] = -record['bill']

        logger.info(
            "Bill {} for tender {} with value {}".format(
                record['bill'], record['tender'], record['value']
            )
        )
        return [str(c) for c in record.values()]


class Invoices(BaseBidsGenerator,
               RowInvoiceMixin,
               HeadersToRowMixin,
               CSVMixin
               ):
    module = 'invoices'
    fields = headers

    def __init__(self, config):
        self.headers = config.headers
        self.counter = [0 for _ in range(5)]
        self.counter_minus = [0 for _ in range(5)]
        BaseBidsGenerator.__init__(self, config)

    def row(self, row):
        record = self.record(row)
        payment = self.get_payment(record['value'])
        for i, x in enumerate(self.config.payments):
            if payment == x:
                msg = 'Bill {} for value {} '\
                      'in {} tender'.format(payment, record['value'],
                                            record['tender'])
                logger.info(msg)
                if self.config.include_cancelled and row.get('cancelled', ''):
                    self.counter_minus[i] += 1
                else:
                    self.counter[i] += 1

    @property
    def rows(self):
        for resp in self.response:
            self.row(resp['value'])
        rows = [
            self.config.payments,
            self.counter,
            [c * v for c, v in zip(self.counter, self.config.payments)]
        ]
        if self.config.include_cancelled:
            rows += [
                [],
                [-x for x in self.config.payments],
                self.counter_minus,
                [-(c * v) for c, v in zip(self.counter_minus, self.config.payments)]
            ]
        for row in rows:
            yield row