from reports.core import BaseTendersUtility
from reports.helpers import (
    thresholds_headers,
    value_currency_normalize
)


class RefundsUtility(BaseTendersUtility):

    def __init__(self):
        super(RefundsUtility, self).__init__('refunds')
        self.headers = thresholds_headers(self.config.thresholds)
        self.counter = [0 for _ in self.config.payments]

    def row(self, record):
        tender = record.get('tender', '')
        lot = record.get('lot', '')
        status = record.get('status', '')
        lot_status = record.get('lot_status', '')

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
        if record.get('kind') not in self.kinds:
            self.Logger.info('Scip tender {} by kind'.format(tender))
            return
        if self.check_status(status, lot_status):
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
        payment = self.get_payment(value)
        for i, x in enumerate(self.config.payments):
            if payment == x:
                msg = 'Bill {} for value {} in tender {}'.format(
                    payment, value, record['tender']
                )
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
    utility = RefundsUtility()
    utility.run()


if __name__ == "__main__":
    run()