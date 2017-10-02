from reports.core import BaseBidsUtility, NEW_ALG_DATE
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
        self.counters = {
            index: [0 for _ in range(0, 5)]
            for index in range(1, 5)
        }

    def row(self, record):
        startdate = record.get('startdate', '')
        version = 1 if startdate < NEW_ALG_DATE else 2
        date_terminated = record.get('date_terminated', '')
        value = float(record.get("value", 0))
        bid = record.get(u"bid", '')
        state = record.get('state', '')
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
        p = self.payments
        c = self.counters[1]
        if version == 2:
            if date_terminated:
                c = self.counters[3] if state == 3 else self.counters[2]
            else:
                c = self.counters[4]
        for i, x in enumerate(p):
            if payment == x:
                msg = 'Computated bill {} for value {} '\
                      'in {} tender'.format(payment, value, record['tender'])
                self.Logger.info(msg)
                c[i] += 1

    def rows(self):
        for resp in self.response:
            self.row(resp['value'])
        for row in [
            self.counters[1],
            self.payments,
            [c * v for c, v in zip(self.counters[1], self.payments)],
            ['after_{}'.format(NEW_ALG_DATE)],
            [a + b + c for a, b, c in zip(self.counters[2], self.counters[3], self.counters[4])],
            self.counters[2],
            self.counters[3],
            self.counters[4],
            self.payments,
            [c * v for c, v in zip(self.counters[4], self.payments_before)],
        ]:
            yield row


def run():
    utility = InvoicesUtility()
    utility.run()


if __name__ == "__main__":
    run()
