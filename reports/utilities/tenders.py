
from reports.core import BaseTendersUtility
from reports.helpers import (
    value_currency_normalize
)


class TendersUtility(BaseTendersUtility):

    def __init__(self):
        super(TendersUtility, self).__init__('tenders')
        self.headers = ["tender", "tenderID", "lot",
                        "status", "lot_status", "currency",
                        "kind", "value", "rate", "bill"]
        [self.headers.remove(col) for col in self.skip_cols if col in self.headers]

    def row(self, record):
        rate = None
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
            self.Logger.info('Skip tender {} by kind'.format(tender))
            return
        if self.check_status(status, lot_status):
            self.Logger.info('Skip tender {} by status {}'.format(tender, status))
            return
        row = list(record.get(col, '') for col in self.headers[:-2])
        value = float(record.get(u'value', 0))
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
        r = str(rate) if rate else ''
        row.append(r)
        row.append(self.get_payment(value))
        self.Logger.info(
            "Bill {} for tender {} with value {}".format(
                row[-1], row[0], value
            )
        )
        return row

    def rows(self):
        for resp in self.response:
            r = self.row(resp['value'])
            if r:
                yield r


def run():
    utility = TendersUtility()
    utility.run()

if __name__ == "__main__":
    run()