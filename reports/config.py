from __future__ import print_function

import os.path
import yaml

from reports.helpers import (
    convert_date,
    create_db_url,
    thresholds_headers
)


ARGS = [
    'broker',
    'period',
    'config',
    'timezone',
    'include_cancelled'
]


class Config(object):

    def __init__(self, path):
        if not os.path.exists(path):
            raise ValueError("Config file does not exists."
                             "Please provide one")
        for key in ARGS:
            setattr(self, key, '')
        self.config = yaml.load(path)
        self.module = ''

    @classmethod
    def from_namespace(cls, args, module):
        inst = cls(args.config, module)
        for key in [a for a in ARGS if a != 'config']:
            if hasattr(args, key):
                setattr(cls, key, getattr(args, key))
        return inst

    @property
    def thresholds(self):
        return [float(i) for i in self.config.get('payments', 'thresholds')]

    @property
    def payments(self):
        section = 'emall' if self.modul in ['refunds', 'tenders'] else 'cdb'
        return [float(i.strip()) for i in self.config.get('payments')(section)]

    @property
    def out_path(self):
        return self.config.get('out', '').get('out_dir', '')

    @property
    def start_date(self):
        if len(self.period) > 0:
            return convert_date(self.period[0])
        return ''

    @property
    def end_date(self):
        if len(self.period) > 1:
            return convert_date(self.period[1])
        return ''

    @property
    def out_file(self):
        start = self.start_date.split('T')[0]\
                if self.start_date else ''
        end = self.end_date.split('T')[0]\
                if self.end_date else ''
        name = "{}@{}--{}-{}.csv".format(
            self.broker,
            start,
            end,
            self.operation
        )
        return os.path.join(self.out_path, name)

    @property
    def db_url(self):
        db = self.config['db']
        return create_db_url(
            db['host'],
            db['port'],
            db['user']['name'],
            db['user']['password']
        )

    @property
    def admin_db_url(self):
        db = self.config['db']
        return create_db_url(
            db['host'],
            db['port'],
            db['admin']['name'],
            db['admin']['password']
        )

    @property
    def headers(self):
        return thresholds_headers(self.coding.get('thresholds'))
