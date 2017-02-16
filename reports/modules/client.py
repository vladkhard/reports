import subprocess


class PassClient(object):

    def __init__(self):
        self.cmd = 'pass'

    def _output(self, cmd):
        return subprocess.check_output(cmd, shell=True)

    def _credentials(self, path):
        cmd = self.cmd + ' {}'.format(path)
        out = self._output(cmd)
        return dict(item.split('=') for item
                    in out.split('\n') if item)

    def ses_credentials(self, key):
        return self._credentials(key)

    def s3_credentials(self, key):
        return self._credentials(key)

    def broker_password(self, key):
        return self._output(self.cmd + ' {}'.format(key))