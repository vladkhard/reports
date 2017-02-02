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


class Bids(BaseBidsGenerator,
           RowMixin,
           HeadersToRowMixin,
           CSVMixin
           ):
    headers = [
        u"tender",
        u"tenderID",
        u"lot",
        u"value",
        u"currency",
        u"bid",
        u'rate',
        u"bill"
    ]
    module = 'bids'

    def row(self, row):
        record = self.record(row)
        bill = self.get_payment(record['value'])
        logger.info(
            "Bill {} for tender {} with value {}".format(
                bill, record['tender'], record['value']
            )
        )
        row = [str(c) for c in record.values()]
        row.append(str(bill))
        return row


class Invoices(BaseBidsGenerator,
               RowInvoiceMixin,
               HeadersToRowMixin,
               CSVMixin
               ):
    headers = thresholds_headers()
    counter = [0 for _ in range(5)]
    module = 'invoices'

    def row(self, row):
        record = self.record(row)
        payment = self.get_payment(record['value'])
        for i, x in enumerate(self.config.payments):
            if payment == x:
                msg = 'Bill {} for value {} '\
                      'in {} tender'.format(payment, record['value'],
                                            record['tender'])
                logger.info(msg)
                self.counter[i] += 1



