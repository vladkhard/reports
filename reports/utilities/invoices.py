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

        self.counter = [0 for _ in range(0, 5)]
        self.counter_before = [0 for _ in range(0, 5)]
        self.counter_1 = [0 for _ in range(0, 5)]
        self.counter_2 = [0 for _ in range(0, 5)]
        self.counter_3 = [0 for _ in range(0, 5)]
        self.counter_4 = [0 for _ in range(0, 5)]

    def row(self, record):
        startdate = record.get('startdate', '')
        version = 1 if startdate < "2017-08-09" else 2
        date_terminated = record.get('date_terminated', '')
        value = float(record.get("value", 0))
        bid = record.get(u"bid", '')
        state = record.get('state', '')
        use_audit = True
        self.get_initial_bids(record.get('audits', ''),
                              record.get('tender', ''))
        if not self.initial_bids:
            use_audit = False

        if record.get('startdate', '') < "2016-04-01" and \
                not self.bid_date_valid(bid):
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

        if use_audit:
            initial_bid = [b for b in self.initial_bids
                           if b['bidder'] == bid]
            if not initial_bid:
                initial_bid_date = record.get('initialDate', '')
            else:
                initial_bid_date = initial_bid[0]['date']

        else:
            self.Logger.fatal('Unable to load initial bids'
                              ' for tender id={} for audits.'
                              'Use initial bid date from revisions'.format(record.get('tender')))
            initial_bid_date = record.get('initialDate', '')
            self.Logger.info('Initial date from revisions {}'.format(initial_bid_date))
        before = initial_bid_date > self.threshold_date or version == 2
        payment = self.get_payment(value, before)
        p = self.payments
        c = self.counter
        if before:
            p = self.payments_before
            c = self.counter_before
        if version == 2:
            if date_terminated:
                c = self.counter_3 if state == 3 else self.counter_2
            else:
                c = self.counter_4
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
            self.counter,
            self.payments,
            [c * v for c, v in zip(self.counter, self.payments)],
            ['' for _ in range(5)],
            self.counter_before,
            self.payments_before,
            [c * v for c, v in zip(self.counter_before, self.payments_before)],
            ['after 2017-08-09'],
            [a + b + c for a, b, c in zip(self.counter_2, self.counter_3, self.counter_4)],
            self.counter_2,
            self.counter_3,
            self.counter_4,
            self.payments,
            [c * v for c, v in zip(self.counter_4, self.payments_before)],
        ]:
            yield row


def run():
    utility = InvoicesUtility()
    utility.run()


if __name__ == "__main__":
    run()
