from reports.core import BaseTendersUtility, NEW_ALG_DATE
from reports.helpers import (
    thresholds_headers,
    value_currency_normalize
)


class RefundsUtility(BaseTendersUtility):

    def __init__(self):
        super(RefundsUtility, self).__init__('refunds')
        self.headers = thresholds_headers(self.config.thresholds)
        self.counter = [0 for _ in range(0, 5)]
        self.counter_before = [0 for _ in range(0, 5)]
        self.new_counter = [0 for _ in range(0, 5)]

    def row(self, record):
        tender = record.get('tender', '')
        lot = record.get('lot', '')
        status = record.get('status', '')
        lot_status = record.get('lot_status', '')
        initial_date = record.get('startdate', '')
        version = 2 if initial_date > NEW_ALG_DATE else 1

        if lot:
            if ','.join([tender, lot]) in self.ignore:
                self.Logger.info(
                    'Skip tender {} with lot {} by'
                    ' ignore list'.format(tender, lot))
                return
        else:
            if '{},'.format(tender) in self.ignore:
                self.Logger.info(
                    'Skip tender {} by ignore list'.format(tender)
                )
                return
        if record.get('kind') not in self.kinds and version == 1:
            self.Logger.info('Scip tender {} by kind'.format(tender))
            return
        if self.check_status(status, lot_status) and version == 1:
            self.Logger.info('Skip tender {} by status {}'.format(tender, status))
            return

        value = float(record.get("value", 0))
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

        before = initial_date > self.threshold_date
        payment = self.get_payment(value, before)
        p = self.payments
        c = self.counter
        if before:
            p = self.payments_before
            c = self.counter_before
        if version == 2:
            c = self.new_counter
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
            self.payments,
            self.counter,
            [c * v for c, v in zip(self.counter, self.payments)],
            ['' for _ in range(5)],
            self.payments_before,
            self.counter_before,
            [c * v for c, v in zip(self.counter_before, self.payments_before)],
            ['after {}'.format(NEW_ALG_DATE)],
            self.payments,
            self.new_counter,
            [c * v for c, v in zip(self.new_counter, self.payments)],
        ]:
            yield row


def run():
    utility = RefundsUtility()
    utility.run()


if __name__ == "__main__":
    run()
