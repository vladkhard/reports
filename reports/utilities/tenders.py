import os
import csv
from reports.core import BaseTendersUtility, NEW_ALG_DATE
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
        date = record.get('startdate', '')
        version = 2 if date > NEW_ALG_DATE else 1
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
            self.Logger.info('Skip tender {} by kind'.format(tender))
            return
        if self.check_status(status, lot_status) and version == 1:
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
        row.append(self.get_payment(value, record.get('startdate', '') > self.threshold_date))
        self.Logger.info(
            "Refund {} for tender {} with value {}".format(
                row[-1], row[0], value
            )
        )
        return row, version

    def write_csv(self):
        second_version = []
        splitter = [u'after 2017-08-09']
        if not self.headers:
            raise ValueError
        if not os.path.exists(os.path.dirname(os.path.abspath(self.put_path))):
            os.makedirs(os.path.dirname(os.path.abspath(self.put_path)))
        with open(self.put_path, 'w') as out_file:
            writer = csv.writer(out_file)
            writer.writerow(self.headers)
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
            r, ver = self.row(resp['value'])
            if r:
                yield r, ver


def run():
    utility = TendersUtility()
    utility.run()

if __name__ == "__main__":
    run()
