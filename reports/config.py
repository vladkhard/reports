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
        with open(path, 'r') as yaml_in:
            self.config = yaml.load(yaml_in)
        self.module = ''

    @classmethod
    def from_namespace(cls, args):
        inst = cls(args.config)
        for key in [a for a in ARGS if a != 'config']:
            if hasattr(args, key):
                setattr(inst, key, getattr(args, key))
        return inst

    @property
    def thresholds(self):
        return [float(i) for i in self.config['payments']['thresholds']]

    @property
    def payments(self):
        section = 'emall' if self.module in ['refunds', 'tenders'] else 'cdb'
        return self.config['payments'][section]

    @property
    def out_path(self):
        return self.config.get('out', '').get('out_dir', '')

    def start_date(self):
        if len(self.period) > 0:
            return convert_date(self.period[0])
        return ''

    def end_date(self):
        if len(self.period) > 1:
            return convert_date(self.period[1])
        return ''

    @property
    def out_file(self):
        start = self.start_date().split('T')[0]\
                if self.start_date else ''
        end = self.end_date().split('T')[0]\
                if self.end_date else ''
        name = "{}@{}--{}-{}.csv".format(
            self.broker,
            start,
            end,
            self.module
        )
        return os.path.join(self.out_path, name)

    @property
    def db_url(self):
        db = self.config['db']
        return create_db_url(
            db['host'],
            db['port'],
            db['user']['name'],
            db['user']['password'],
            db['name']
        )

    @property
    def admin_db_url(self):
        db = self.config['db']
        return create_db_url(
            db['host'],
            db['port'],
            db['admin']['name'],
            db['admin']['password'],
            db['name']
        )

    @property
    def headers(self):
        return thresholds_headers(self.thresholds)
