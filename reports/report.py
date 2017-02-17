import os.path
import yaml
import argparse
import csv
import pyminizip
from datetime import date
from datetime import datetime
from logging import getLogger
from logging.config import dictConfig
from reports.modules import (
    Bids,
    Invoices,
    Tenders,
    Refunds,
    AWSClient
)

from reports.modules.bids import (
    headers as bids_headers
)


from reports.helpers import (
    convert_date
)

from reports.config import (
    Config
)

from reports.vault import (
    Vault
)

ARGS = [
    'config',
    'type',
    'period',
    'notify',
    'notify_brokers',
    'brokers',
    'timestamp',
    'include',
    'timezone',
    'include_cancelled',
    'to_now'
]
logger = getLogger()


class ReportConfig(object):

    def __init__(self, path):
        for key in ARGS:
            setattr(self, key, '')

        if not os.path.exists(path):
            raise ValueError("Config file does not exists."
                             "Please provide one")
        with open(path, 'r') as yaml_in:
            self.config = yaml.load(yaml_in)
        dictConfig(self.config)
        self.brokers = self.config.get('brokers', {}).keys() if\
                            self.config.get('brokers', {}) else []
        self.emails = self.config.get('brokers') if self.brokers else {}
        aws = self.config.get('aws')
        self.ses = aws.get('ses_pass_path')
        self.s3 = aws.get('s3_pass_path')
        self.bucket = aws.get('bucket')
        self.expires = aws.get('expires')

        email = self.config.get('email')
        self.smtp_server = email.get('smtp_server')
        self.smtp_port = email.get('smtp_port')
        self.verified_email = email.get('verified_email')
        self.zip = self.config.get('zip_path')
        self.vault = self.config.get('vault')

    def produce_module_config(self, broker):
        config = Config(self.config)
        for param in ['period', 'timezone', 'include_cancelled']:
            setattr(config, param, getattr(self, param))
        config.broker = broker
        config.include_cancelled = self.include_cancelled
        config.period = [convert_date(self.start_date, from_tz='UTC', to_tz='Europe/Kiev'),
                         convert_date(self.end_date, from_tz='UTC', to_tz='Europe/Kiev')]
        return config

    @property
    def start_date(self):
        if len(self.period) == 0:
            today = date.today().replace(day=1)
            if today.month == 1:
                return today.replace(year=today.year-1,
                                     month=12,
                                     day=1).strftime('%Y-%m-%d')
            elif not self.to_now:
                return today.replace(month=today.month-1,
                                     day=1).strftime('%Y-%m-%d')
            return today.strftime('%Y-%m-%d')
        return self.period[0].split('T')[0]

    @property
    def end_date(self):
        if len(self.period) < 2 and not self.to_now:
            return date.today().replace(day=1).strftime('%Y-%m-%d')
        if len(self.period) < 2 and self.to_now:
            return date.today().strftime('%Y-%m-%d')
        return self.period[1].split('T')[0]

    @classmethod
    def from_namespace(cls, args):
        inst = cls(args.config)

        for key in [a for a in ARGS if a != 'config']:
            if hasattr(args, key) and getattr(args, key, ) is not None:
                setattr(inst, key, getattr(args, key))
        return inst

    @property
    def modules(self):
        if self.type == ['all']:
            return ['bids', 'invoices', 'tenders', 'refunds']
        return self.type

    @property
    def work_dir(self):
        return self.config['out']['out_dir']


class Report(object):

    def __init__(self, config):
        self.config = config
        self.vault = Vault(config)
        self.mod_map = {
            'bids': Bids,
            'invoices': Invoices,
            'tenders': Tenders,
            'refunds': Refunds,
        }
        self.aws = AWSClient(config, vault=self.vault)
        self.run_time = datetime.now().strftime('%Y-%m-%d/%H-%M-%S-%f')

    def generate_for_broker(self, broker):
        config = self.config.produce_module_config(broker)
        for module in self.config.modules:
            config.module = module
            logger.info('generation {} for {} from {} to {}'.format(
                module,
                config.broker,
                config.start_date(),
                config.end_date(),
            ))
            op = self.mod_map.get(module)(config)
            op.run()

    def create_all_bids(self):
        all_name = 'all@{}--{}-bids.csv'.format(self.config.start_date,
                                                self.config.end_date)
        logger.info('Creating all bids csv from {} to {}'.format(
            self.config.start_date,
            self.config.end_date
        ))
        with open(os.path.join(self.config.work_dir, all_name), 'w+')\
                as part_csv:
            writer = csv.writer(part_csv)
            writer.writerow(bids_headers)
            for broker in [b for b in self.config.brokers if b != 'all']:
                name = '{}@{}--{}-bids.csv'.format(broker,
                                                   self.config.start_date,
                                                   self.config.end_date)
                with open(os.path.join(self.config.work_dir, name), 'r')\
                        as broker_csv:
                    reader = csv.reader(broker_csv)
                    next(reader)
                    for row in reader:
                        writer.writerow(row)

    def _zip(self, name, files, password=None):
        pyminizip.compress_multiple(
            files,
            os.path.join(self.config.work_dir, name),
            password,
            4
        )

    def create_tenders_archive(self):
        zname = 'all@{}--{}-tenders-refunds.zip'.format(
            self.config.start_date, self.config.end_date
        )
        logger.info('Creating all tenders zip')
        self._zip(zname, [os.path.join(self.config.work_dir,
                                       '{}@{}--{}-{}.csv'.format(
                                           broker,
                                           self.config.start_date,
                                           self.config.end_date,
                                           name))
                          for name in ['tenders', 'refunds']
                          for broker in self.config.brokers if broker != 'all'])

    def create_all_bids_archive(self):
        logger.info('Creating all bids zip')
        zname = 'all@{}--{}-bids.zip'.format(
            self.config.start_date, self.config.end_date
        )
        files = [
            os.path.join(self.config.work_dir,
                         'all@{}--{}-bids.csv'.format(self.config.start_date,
                                                      self.config.end_date))
        ] + [
            os.path.join(self.config.work_dir,
                         '{}@{}--{}-invoices.csv'.format(
                             broker,
                             self.config.start_date,
                             self.config.end_date))
            for broker in self.config.brokers if broker != 'all'
        ]

        self._zip(zname, files, self.vault.broker_password('all'))

    def create_brokers_archives(self):

        for broker in [b for b in self.config.brokers if b != 'all']:
            zip_name = '{}@{}--{}-{}.zip'.format(broker,
                                                 self.config.start_date,
                                                 self.config.end_date,
                                                 '-'.join(self.config.include))
            logger.info('Packing {}'.format(zip_name))
            files = [os.path.join(self.config.work_dir,
                                  '{}@{}--{}-{}.csv'.format(broker,
                                                            self.config.start_date,
                                                            self.config.end_date,
                                                            op))
                     for op in self.config.include]
            password = self.vault.broker_password(broker)
            self._zip(zip_name, files, password=password)

    def upload_files(self):
        for broker in self.config.brokers:
            if broker == 'all':
                files = [
                    'all@{}--{}-tenders-refunds.zip'.format(
                        self.config.start_date, self.config.end_date
                    ),
                    'all@{}--{}-bids.zip'.format(
                        self.config.start_date, self.config.end_date
                    )
                ]
            else:
                files = [
                    '{}@{}--{}-{}.zip'.format(broker,
                                              self.config.start_date,
                                              self.config.end_date,
                                              '-'.join(self.config.include))
                ]
            logger.info('Sending files to s3: {}'.format(files))
            self.aws.send_files([os.path.join(self.config.work_dir, f) for f in files], timestamp=self.run_time)

    def clean_up(self):
        files = [
            os.path.join(self.config.work_dir,
                         '{}@{}--{}-{}.csv'.format(broker,
                                                   self.config.start_date,
                                                   self.config.end_date,
                                                   op))
            for op in self.config.include
            for broker in self.config.brokers if broker != 'all'
        ] + [
            os.path.join(self.config.work_dir,
                         'all@{}--{}-bids.csv'.format(self.config.start_date,
                                                      self.config.end_date))
        ]
        try:
            logger.info('Run clean up')
            map(os.remove, files)
        except:
            pass

    def run(self):
        logger.info('Starting generation {}--{}.'.format(
            self.config.start_date,
            self.config.end_date)
        )
        logger.info('Brokers {}'.format(self.config.brokers))
        logger.info('Types: {}'.format(self.config.modules))
        if self.config.timestamp:
            logger.info('Sending from timestamp {}'.format(
                self.config.timestamp)
            )
            self.aws.send_from_timestamp(self.config.timestamp)
        else:
            for broker in [b for b in self.config.brokers if b != 'all']:
                self.generate_for_broker(broker)
            self.create_all_bids()
            self.create_tenders_archive()
            self.create_brokers_archives()
            self.create_all_bids_archive()
            self.upload_files()
            self.clean_up()
        if self.config.notify:
            self.aws.send_emails()


def run():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config')
    parser.add_argument('--type', nargs='+', default=['all'])
    parser.add_argument('--period', nargs='+', default=[])
    parser.add_argument('--notify', action='store_true', default=False)
    parser.add_argument('--to-now', action='store_true', default=False)
    parser.add_argument('--include-cancelled', action='store_true', default=False)
    parser.add_argument('--notify-brokers', nargs='+')
    parser.add_argument('--brokers', nargs='+')
    parser.add_argument('--timestamp')
    parser.add_argument('--timezone', default='Europe/Kiev')
    parser.add_argument('--include', nargs='+', default=['bids', 'invoices', 'tenders', 'refunds'])

    args = parser.parse_args()
    config = ReportConfig.from_namespace(args)
    report = Report(config)
    report.run()
