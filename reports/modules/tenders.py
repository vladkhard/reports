import logging
from reports.core import (
    BaseTendersGenerator,
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
    "kind",
    "value",
    "currency",
    'rate',
    "bill"
]


class Tenders(BaseTendersGenerator,
              RowMixin,
              HeadersToRowMixin,
              CSVMixin
              ):
    module = 'tenders'
    headers = headers
    fields = headers

    def row(self, row):
        record = self.record(row)
        if record.get('kind', '') == 'other':
            return
        record['bill'] = self.get_payment(record['value'])
        logger.info(
            "Bill {} for tender {} with value {}".format(
                record['bill'], record['tender'], record['value']
            )
        )
        return [str(c) for c in record.values()]


class Refunds(BaseTendersGenerator,
              RowInvoiceMixin,
              HeadersToRowMixin,
              CSVMixin
              ):
    counter = [0 for _ in range(5)]
    module = 'refunds'
    fields = headers

    def __init__(self, config):
        self.headers = config.headers
        BaseTendersGenerator.__init__(self, config)

    def row(self, row):
        record = self.record(row)
        if record.get('kind', '') == 'other':
            return
        payment = self.get_payment(record['value'])
        for i, x in enumerate(self.config.payments):
            if payment == x:
                msg = 'Bill {} for value {} '\
                      'in {} tender'.format(payment, record['value'],
                                            record['tender'])
                logger.info(msg)
                self.counter[i] += 1
