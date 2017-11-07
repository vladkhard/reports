import os
import csv
from reports.core import BaseBidsUtility, NEW_ALG_DATE
from reports.helpers import (
    get_cmd_parser,
    value_currency_normalize
)


class BidsUtility(BaseBidsUtility):

    def __init__(self):
        super(BidsUtility, self).__init__('bids')
        self.headers = [u"tender", u"tenderID", u"lot",
                        u"value", u"currency", u"bid", u'rate', u"bill", u"state"]

    def row(self, record):
        startdate = record.get('startdate', '')
        version = 1 if startdate < NEW_ALG_DATE else 2
        date_terminated = record.get('date_terminated', '')
        state = record.get('state', '')
        bid = record.get(u'bid', '')
        rate = None
        row = list(record.get(col, '') for col in self.headers[:-3])
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
        if state:
            row.append(state)
        self.Logger.info(
            "Bill {} for tender {} with value {}".format(
                row[-1], row[0], value
            )
        )
        return row, version

    def write_csv(self):
        second_version = []
        splitter = [u'after {}'.format(NEW_ALG_DATE)]
        if not self.headers:
            raise ValueError
        if not os.path.exists(os.path.dirname(os.path.abspath(self.put_path))):
            os.makedirs(os.path.dirname(os.path.abspath(self.put_path)))
        with open(self.put_path, 'w') as out_file:
            writer = csv.writer(out_file)
            writer.writerow(self.headers)
            writer.writerow(['after_2017-01-01'])
            for row, ver in self.rows():
                if ver == 1:
                    writer.writerow(row)
                else:
                    second_version.append(row)
            if second_version:
                writer.writerow(splitter)
                for row in second_version:
                    writer.writerow(row)

    def rows(self):
        for resp in self.response:
            row, ver = self.row(resp["value"])
            if row:
                yield row, ver


def run():
    utility = BidsUtility()
    utility.run()


if __name__ == "__main__":
    run()
