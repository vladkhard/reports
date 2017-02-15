from reports.core import BaseBidsUtility
from reports.helpers import (
    thresholds_headers,
    value_currency_normalize
)


class InvoicesUtility(BaseBidsUtility):

    def __init__(self):
        super(InvoicesUtility, self).__init__('invoices')
        self.headers = thresholds_headers(
            self.config.thresholds
        )
        self.counter = [0 for _ in self.config.payments]

    def row(self, record):
        value = float(record.get("value", 0))
        bid = record.get(u"bid", '')
        if record.get('startdate', '') < "2016-04-01" and \
                not self.bid_date_valid(bid, record.get(u'audits', '')):
            return
        if record[u'currency'] != u'UAH':
            old = value
            value, rate = value_currency_normalize(
                value, record[u'currency'], record[u'startdate']
            )
            msg = "Changed value {} {} by exgange rate {} on {}"\
                " is  {} UAH in {}".format(
                    old, record[u'currency'], rate,
                    record[u'startdate'], value, record['tender']
                )
            self.Logger.info(msg)
        payment = self.get_payment(value)
        for i, x in enumerate(self.config.payments):
            if payment == x:
                msg = 'Computated bill {} for value {} '\
                      'in {} tender'.format(payment, value, record['tender'])
                self.Logger.info(msg)
                self.counter[i] += 1

    def rows(self):
        self._rows = [self.counter, self.config.payments]
        for resp in self.response:
            self.row(resp['value'])
        self._rows.append(
            [c * v for c, v in zip(self.counter, self.config.payments)]
        )
        for row in self._rows:
            yield row


def run():
    utility = InvoicesUtility()
    utility.run()


if __name__ == "__main__":
    run()