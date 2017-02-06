from reports.modules import PassClient
from os.path import join


class Vault(object):

    def __init__(self, config):
        self.type = config.vault
        if self.type != 'pass':
            raise NotImplementedError('Only pass is supported')
        self.config = config
        self.client = PassClient()

    def ses(self):
        return self.client.ses_credentials(self.config.ses)

    def s3(self):
        return self.client.s3_credentials(self.config.s3)

    def broker_password(self, broker):
        passwd = self.client.broker_password(join(self.config.zip, broker))
        return passwd.strip('\n')
