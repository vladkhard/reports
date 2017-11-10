from reports.core import BaseBidsUtility, NEW_ALG_DATE
from reports.helpers import (
    thresholds_headers,
    value_currency_normalize,
    get_arguments_parser
)


class InvoicesUtility(BaseBidsUtility):
    def __init__(
            self, broker, period, config,
            timezone="Europe/Kiev"
            ):
        super(InvoicesUtility, self).__init__(
            broker, period, config, operation='invoices', timezone=timezone)
        self.headers = thresholds_headers(
            self.config.thresholds
        )
        self.counters = {
            index: [0 for _ in range(0, 5)]
            for index in range(0, 5)
        }

    def row(self, record):
        startdate = record.get('startdate', '')
        version = 1 if startdate < NEW_ALG_DATE else 2 #TODO: unused
        date_terminated = record.get('date_terminated', '') #TODO: unused
        value, rate = self.convert_value(record)
        bid = record.get(u"bid", '') # TODO: unused
        state = record.get('state', '')

        payment = self.get_payment(value)
        p = self.config.payments(2017)
        c = self.counters[state] if state else self.counters[0]
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
            ['after_2017-01-01'],
            self.counters[0],
            self.config.payments(grid=2016),
            [c * v for c, v in zip(self.counters[0], self.config.payments(grid=2016))],
            ['after_{}'.format(NEW_ALG_DATE)],
            self.counters[1],
            self.counters[2],
            self.counters[3],
            [a - b - c for a, b, c in zip(self.counters[1], self.counters[2], self.counters[3])],
            self.config.payments(grid=2017),
            [c * v for c, v in zip([a - b - c for a, b, c in zip(self.counters[1], self.counters[2], self.counters[3])], self.config.payments(grid=2017))],
        ]:
            yield row


def run():
    parser = get_arguments_parser()
    args = parser.parse_args()
    utility = InvoicesUtility(
        args.broker, args.period,
        args.config, timezone=args.timezone)
    utility.run()


if __name__ == "__main__":
    run()
