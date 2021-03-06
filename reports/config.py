import sys
from logging.config import fileConfig
from ConfigParser import ConfigParser, NoSectionError, NoOptionError


class Config(object):

    def __init__(self, path, rev=False):
        self.config = ConfigParser()
        self.config.read(path)
        fileConfig(path)
        self.rev = rev

    def get_option(self, section, name):
        try:
            opt = self.config.get(section, name)
        except NoSectionError:
            print "No section {} in configuration file".format(section)
            sys.exit(1)
        except NoOptionError:
            print "No option {} in configuration file".format(name)
            sys.exit(1)
        return opt

    @property
    def api_url(self):
        host = self.get_option('api', 'host')
        version = self.get_option('api', 'version')
        url = '{}/api/{}'.format(host, version)
        return url

    @property
    def thresholds(self):
        t = self.config.get('payments', 'thresholds')
        return [float(i.strip()) for i in t.split(',')]

    def payments(self, before_2017=False):
        if self.rev:
            key = 'emall_{}'
        else:
            key = 'cdb_{}'
        key = key.format('2016') if before_2017 else \
                    key.format('2017')

        p = self.config.get('payments', key)
        return [float(i.strip()) for i in p.split(',')]

    @property
    def out_path(self):
        return self.get_option('out', 'out_dir')
