import os.path
from ConfigParser import ConfigParser

import boto3
from botocore.exceptions import ClientError

from abc import ABCMeta, abstractmethod
from pkg_resources import iter_entry_points

from reports.helpers import use_credentials
from reports.log import getLogger


PKG_NAMESPACE = 'billing.storages'
REGISTRY = {}
LOGGER = getLogger("BILLING")


class Config(object):
    def __init__(self, config_file_path):
        self.config = ConfigParser()
        self.config.read(config_file_path)
        type = self.config.get('storage', 'type')
        self.bucket = self.config.get(type, 'bucket')
        self.expires = self.config.get(type, 'expires')
        self.password_prefix = self.config.get(type, 'password_prefix')


class BaseStorate(object):
    __metaclass__ = ABCMeta

    def __init__(self, config):
        """"""

    @abstractmethod
    def list_objects(self, key):
        """Get list of available objects mached key
           Used to send emails with links to existing objects
        """

    @abstractmethod
    def upload_file(self, file):
        """
        Upload file to remote storage
        """

    @abstractmethod
    def generate_presigned_url(self, file):
        """
        Generage public url to file
        """


class S3Storage(BaseStorate):

    client = boto3.client

    def __init__(self, config):
        self.config = Config(config)
        with use_credentials(self.config.password_prefix) as user_pass:
            self.storage = self.client(
                's3',
                aws_access_key_id=user_pass.get('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=user_pass.get('AWS_SECRET_ACCESS_KEY'),
                region_name=user_pass.get('AWS_DEFAULT_REGION')
                )

    def generate_presigned_url(self, key):
        return self.client.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': self.config.bucket, 'Key': key},
                    ExpiresIn=self.config.expires,
                    )

    def upload_file(self, file, timestamp):
        # timestamp aka full path prefix
        # accepts only full system path to the file
        assert timestamp
        key = '/'.join((timestamp, os.path.basename(file)))
        try:
            self.storage.upload_file(
                file,
                self.config.bucket,
                key
                )
        except ClientError as e:
            LOGGER.fatal(
                "Falied to upload file {}. Error {}".format(file, e)
                )
            return ""
        try:
            return self.generate_presigned_url(key)
        except Exception as e:
            LOGGER.fatal(
                'Falied to sign url for file {}. Error: {}'.format(key, e)
                )
            return ""

    def list_objects(self, prefix):
        return self.client.list_objects(
                Bucket=self.config.bucket,
                Prefix=prefix
                )['Contents']


for storage in iter_entry_points(PKG_NAMESPACE):
    REGISTRY[storage.name] = storage.load()
