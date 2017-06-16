import boto3
import argparse
import os.path
import logging
import os
import subprocess
import smtplib
import re
import sys
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import COMMASPACE
from jinja2 import Environment, PackageLoader
from botocore.exceptions import ClientError
from logging.config import fileConfig
from ConfigParser import ConfigParser
from reports.helpers import get_operations, get_send_args_parser
from datetime import datetime

Logger = None



class AWSClient(object):

    def __init__(self, config):
        fileConfig(config)
        self.config = ConfigParser()
        self.config.read(config)
        self.Logger = logging.getLogger('AWS')
        self.bucket = self.config.get('aws', 'bucket')
        self.expires = self.config.get('aws', 'expires')
        self.s3_cred_path = self.config.get('aws', 's3_pass_path')
        self.ses_cred_path = self.config.get('aws', 'ses_pass_path')
        self.smtp_server = self.config.get('email', 'smtp_server')
        self.smtp_port = self.config.get('email', 'smtp_port')
        self.verified_email = self.config.get('email', 'verified_email')
        self.use_auth = self.config.get('email', 'use_auth') or False
        self.emails_to = dict((key, field.split(',')) for key, field in self.config.items('brokers_emails'))
        self.template_env = Environment(
                loader=PackageLoader('reports', 'templates'))
        self.links = []
        self._brokers = []

    @property
    def brokers(self):
        return self._brokers

    @brokers.setter
    def brokers(self, brokers):
        self._brokers = brokers

    def _update_credentials(self, path):
        cmd = "pass {}".format(path)
        cred = dict(item.split('=') for item in
                    subprocess.check_output(cmd, shell=True).split('\n')
                    if item)
        return cred

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
        cred = self._update_credentials(self.s3_cred_path)

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
                    self.bucket,
                    key)
                entry['link'] = s3.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': self.bucket, 'Key': key},
                    ExpiresIn=self.expires,
                )
                self.links.append(entry)
            except ClientError as e:
                print "Error during uploading file {}. Error {}".format(f, e)

    def send_emails(self):
        cred = self._update_credentials(self.ses_cred_path)
        user = cred.get('AWS_ACCESS_KEY_ID')
        password = cred.get('AWS_SECRET_ACCESS_KEY')
        smtpserver = smtplib.SMTP(self.smtp_server, self.smtp_port)

        if self.use_auth and (user and password):
            smtpserver.ehlo()
            smtpserver.starttls()
            smtpserver.ehlo()
            smtpserver.login(user, password)

        try:
            for context in self.links:
                recipients = self.emails_to[context['broker']]
                msg = MIMEText(self._render_email(context), 'html', 'utf-8')
                msg['Subject'] = 'Prozorro Billing: {} {} ({})'.format(context['broker'], context['type'], context['period'])
                msg['From'] = self.verified_email
                msg['To'] = COMMASPACE.join(recipients)
                if (not self.brokers) or (self.brokers and context['broker'] in self.brokers):
                    smtpserver.sendmail(self.verified_email, recipients,  msg.as_string())
        finally:
            smtpserver.close()

    def send_from_timestamp(self, timestamp):
        cred = self._update_credentials(self.s3_cred_path)

        s3 = boto3.client(
            's3',
            aws_access_key_id=cred.get('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=cred.get('AWS_SECRET_ACCESS_KEY'),
            region_name=cred.get('AWS_DEFAULT_REGION')
        )
        for item in s3.list_objects(Bucket=self.bucket, Prefix=timestamp)['Contents']:
            entry = self.get_entry(os.path.basename(item['Key']))
            entry['link'] = s3.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': self.bucket, 'Key': item['Key']},
                    ExpiresIn=self.expires,
                )
            self.links.append(entry)


def run():
    parser = get_send_args_parser()
    args = parser.parse_args()
    client = AWSClient(args.config)

    if args.brokers:
        client.brokers = args.brokers

    if args.exists:
        if not args.timestamp:
            print "Timestamp is required"
            sys.exit(1)
        client.send_from_timestamp(args.timestamp)
    else:
        client.send_files(args.files, args.timestamp)
    for broker in client.links:
        if (not client.brokers) or (client.brokers and broker['broker'] in client.brokers):
            print "Url for {} ==> {}\n".format(broker['broker'], broker['link'])
    if args.notify:
        client.send_emails()


if __name__ == '__main__':
    run()
