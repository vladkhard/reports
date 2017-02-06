import boto3
from botocore.exceptions import (
    ClientError
)

import os
import os.path
import re
import logging
import smtplib
from email.mime.text import MIMEText
from email.utils import COMMASPACE

from jinja2 import (
    Environment,
    PackageLoader
)
from datetime import datetime

from reports.helpers import get_operations
from reports.vault import Vault


logger = logging.getLogger()


class AWSClient(object):

    def __init__(self, config, vault=None):
        self.vault = vault if vault is not None else Vault(config)
        self.config = config
        self.template_env = Environment(
                loader=PackageLoader('reports', 'templates')
        )
        self.links = []
        self.brokers = []

    def _render_email(self, context):
        template = self.template_env.get_template('email.html')
        return template.render(context)

    def get_entry(self, file_name):
        entry = {}
        broker = file_name.split('@')[0]
        entry['period'] = '--'.join(re.findall(r'\d{4}-\d{2}-\d{2}', file_name))
        entry['broker'] = broker
        operations = get_operations(file_name)
        entry['encrypted'] = 'bids' in operations
        if len(operations) == 2:
            entry['type'] = ' and '.join(operations)
        else:
            entry['type'] = ', '.join(operations)
        return entry

    def send_files(self, files, timestamp=''):
        if not timestamp:
            timestamp = datetime.now().strftime("%Y-%m-%d/%H-%M-%S-%f")
        cred = self.vault.s3()
        s3 = boto3.client(
            's3',
            aws_access_key_id=cred.get('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=cred.get('AWS_SECRET_ACCESS_KEY'),
            region_name=cred.get('AWS_DEFAULT_REGION')
        )

        for f in files:
            file_name = os.path.basename(f)
            entry = self.get_entry(file_name)
            key = '/'.join([timestamp, file_name])
            try:
                s3.upload_file(
                    f,
                    self.config.bucket,
                    key)
                entry['link'] = s3.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': self.config.bucket, 'Key': key},
                    ExpiresIn=self.config.expires,
                )
                self.links.append(entry)
            except ClientError as e:
                logger.info("Error during uploading {}. Error: {}".format(f, e))

    def send_emails(self, email=None):
        cred = self.vault.ses()
        user = cred.get('AWS_ACCESS_KEY_ID')
        password = cred.get('AWS_SECRET_ACCESS_KEY')
        smtpserver = smtplib.SMTP(self.config.smtp_server,
                                  self.config.smtp_port)

        smtpserver.ehlo()
        smtpserver.starttls()
        smtpserver.ehlo()
        smtpserver.login(user, password)

        try:
            for context in self.links:
                recipients = self.config.emails[context['broker']]
                msg = MIMEText(self._render_email(context), 'html', 'utf-8')
                msg['Subject'] = 'Rialto Billing: {} {} ({})'.format(context['broker'], context['type'], context['period'])
                msg['From'] = self.config.verified_email
                if email:
                    msg['To'] = COMMASPACE.join(email)
                    if (not self.config.notify_brokers) or (self.config.notify_brokers and context['broker'] in self.config.notify_brokers):
                        smtpserver.sendmail(self.verified_email, email,  msg.as_string())
                else:
                    msg['To'] = COMMASPACE.join(recipients)
                    if (not self.config.notify_brokers) or (self.config.notify_brokers and context['broker'] in self.config.notify_brokers):
                        smtpserver.sendmail(self.verified_email, recipients,  msg.as_string())
        finally:
            smtpserver.close()

    def send_from_timestamp(self, timestamp):
        cred = self.vault.s3()

        s3 = boto3.client(
            's3',
            aws_access_key_id=cred.get('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=cred.get('AWS_SECRET_ACCESS_KEY'),
            region_name=cred.get('AWS_DEFAULT_REGION')
        )
        for item in s3.list_objects(Bucket=self.config.bucket, Prefix=timestamp)['Contents']:
            entry = self.get_entry(os.path.basename(item['Key']))
            entry['link'] = s3.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': self.config.bucket, 'Key': item['Key']},
                    ExpiresIn=self.config.expires,
                )
            self.links.append(entry)
