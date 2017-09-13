import os
import pytest
import mock
from mock import Mock, MagicMock
from mock import patch
import datetime
from reports.report import ReportConfig
from email.mime.text import MIMEText
from email.utils import COMMASPACE
from email.header import Header
from reports.modules.aws import AWSClient

test_config = os.path.join(os.path.dirname(__file__), 'tests.yaml')

ses_key = {
    'AWS_DEFAULT_REGION': 'test',
    'AWS_ACCESS_KEY_ID': 'test',
    'AWS_SECRET_ACCESS_KEY': 'test'
}
s3_key = {
    'AWS_DEFAULT_REGION': 'test',
    'AWS_ACCESS_KEY_ID': 'test',
    'AWS_SECRET_ACCESS_KEY': 'test'
}


TEST_RETURN = {
    "billig/s3": s3_key,
    "billig/ses": ses_key
}


class Vault(object):
    def s3(self):
        return s3_key

    def ses(self):
        return ses_key


@pytest.fixture(scope='function')
def client(request):
    config = ReportConfig(test_config)
    with patch('reports.modules.aws.Vault', return_value=Vault()):
        aws_client = AWSClient(config)
    request.cls.client = aws_client


@pytest.mark.usefixtures("client")
class TestSender(object):

    def test_get_entry(self):
        """Check correct result"""
        # if file_name correct
        file_name = 'broker1@2016-09-01--2016-10-01-bids-invoices.zip'
        result = self.client.get_entry(file_name)
        assert result == {'encrypted': True, 'type': 'bids and invoices',
             'period': '2016-09-01--2016-10-01', 'broker': 'broker1'}
        # check only one value
        file_name = 'test@2016-09-01--2016-10-01-bids.zip'
        result = self.client.get_entry(file_name)
        assert result['type'] == 'bids'
        # check encryption if no type bids
        file_name = 'test@2016-09-01--2016-10-01-invoices.zip'
        result = self.client.get_entry(file_name)
        assert result['encrypted'] == False
        # check all available values
        file_name = 'test@2016-09-01--2016-10-01-bids-invoices-tenders-refunds.zip'
        result = self.client.get_entry(file_name)
        assert result['type'] == 'bids, invoices, tenders, refunds'

    def test_render_email_with_encrypt(self):
        context = {'link': 'test_url', 'encrypted': True, 'type': 'bids and invoices', 'period': '2016-09-01--2016-10-01', 'broker': 'broker1'}
        result = self.client._render_email(context)
        assert 'test_url' in result
        assert "Zip archive is encryped by password you've received earlier. Please use this password to decrypt the file." in result
        assert 'bids and invoices' in result
        assert '2016-09-01--2016-10-01' in result
        assert 'broker1'in result

    def test_render_email_without_encrypt(self):
        context = {'link': 'test_url', 'encrypted': False, 'type': 'bids and invoices', 'period': '2016-09-01--2016-10-01', 'broker': 'broker1'}
        result = self.client._render_email(context)
        assert 'test_url' in result
        assert "Zip archive is encryped by password you've received earlier. Please use this password to decrypt the file." not in result
        assert 'bids and invoices' in result
        assert '2016-09-01--2016-10-01'in result
        assert 'broker1'in result

    def test_send_files_withTS(self):
        # when timestamp is set
        files = ['broker1@2016-09-01--2016-10-01-bids-invoices.zip']
        timestamp = '2016-11-21/13-07-39-406832'
        key = '/'.join([timestamp, 'broker1@2016-09-01--2016-10-01-bids-invoices.zip'])
        with mock.patch('reports.modules.aws.boto3.client') as s:
            self.client.send_files(files, timestamp)
            s.return_value.upload_file.assert_called_with(
                'broker1@2016-09-01--2016-10-01-bids-invoices.zip',
                self.client.config.bucket,
                key
            )
            s.return_value.generate_presigned_url.assert_called_with(
                'get_object',
                ExpiresIn=1209600,
                Params={'Bucket': 'billing',
                        'Key': '2016-11-21/13-07-39-406832/broker1@2016-09-01--2016-10-01-bids-invoices.zip'})

    @pytest.mark.skip
    def test_send_files_withoutTS(self):
        # when timestamp isn`t set
        files = ['broker1@2016-09-01--2016-10-01-bids-invoices.zip']
        mock_datatime = MagicMock()
        key = '/'.join(['2011-11-11/11-11-11-000011', 'broker1@2016-09-01--2016-10-01-bids-invoices.zip'])
        with mock.patch('reports.modules.aws.boto3.client', mock_datatime) as d:
            d.now.return_value = datetime.datetime(year=2011, month=11, day=11, hour=11, minute=11, second=11, microsecond=11)
            with mock.patch('reports.modules.aws.boto3.client') as s:
                self.client.send_files(files)
                s.return_value.upload_file.assert_called_with('broker1@2016-09-01--2016-10-01-bids-invoices.zip', self.client.config.bucket, key)
                s.return_value.generate_presigned_url.assert_called_with('get_object', ExpiresIn='1209600', Params={'Bucket': 'some-name', 'Key': '2011-11-11/11-11-11-000011/broker1@2016-09-01--2016-10-01-bids-invoices.zip'})
    @pytest.mark.skip
    def test_send_test_emails(self):
        # if email present
        file_name = 'broker1@2016-09-01--2016-10-01-bids-invoices.zip'
        email = ['test1@test.com', 'test2@test.com']

        entry = self.client.get_entry(file_name)
        entry['link'] = 'test_url'
        self.client.links.append(entry)

        msg = MIMEText(self.client._render_email(entry), 'html', 'utf-8')
        msg['Subject'] = Header('Rialto Billing: {} {} ({})'.format('broker1', 'bids and invoices', '2016-09-01--2016-10-01'))
        msg['From'] = 'test@test.com'
        msg['To'] = COMMASPACE.join(email)

        with mock.patch('smtplib.SMTP') as s:
            server = s.return_value
            self.client.send_emails(email)
            server.sendmail.assert_called_with('test@mail.org', email, msg.as_string())

    @pytest.mark.skip
    def test_send_real_emails(self):
        # if email isn`t present
        file_name = 'broker1@2016-09-01--2016-10-01-bids-invoices.zip'

        entry = self.client.get_entry(file_name)
        entry['link'] = 'test_url'
        self.client.links.append(entry)

        msg = MIMEText(self.client._render_email(entry), 'html', 'utf-8')
        msg['Subject'] = 'Prozorro Billing: {} {} ({})'.format('broker1', 'bids and invoices', '2016-09-01--2016-10-01')
        msg['From'] = self.client.config.verified_email
        msg['To'] = COMMASPACE.join(self.client.config.emails['broker1'])

        with mock.patch('smtplib.SMTP') as s:
            server = s.return_value
            self.client.send_emails()
            server.sendmail.assert_called_with(self.client.config.verified_email, self.client.config.emails['broker1'], msg.as_string())

    def test_send_from_timestamp(self):
        timestamp = '2016-09-13/13-59-56-779740'
        file_name = '2016-09-13/13-59-56-779740/broker1@2016-09-01--2016-10-01-bids-invoices.zip'
        m = Mock()
        m.list_objects.return_value  = {'Contents': [ {'Key': '2016-09-13/13-59-56-779740/broker1@2016-09-01--2016-10-01-bids-invoices.zip' }  ], 'Prefix': '2016-09-13/13-59-56-779740',  'EncodingType': 'url'}
        s3 = MagicMock()
        s3.return_value = m

        with mock.patch('reports.modules.aws.boto3.client', s3):
            entry = self.client.get_entry(os.path.basename('2016-09-13/13-59-56-779740/broker1@2016-09-01--2016-10-01-bids-invoices.zip'))
            self.client.send_from_timestamp(timestamp)
            assert entry == {'encrypted': True, 'type': 'bids and invoices', 'period': '2016-09-01--2016-10-01', 'broker': 'broker1'}
            assert self.client.links[0]['broker'] == 'broker1'
            res_dict = self.client.links[-1]
            link = res_dict.get('link')
            assert link != None
            m.generate_presigned_url.assert_called_with('get_object', ExpiresIn=1209600, Params={'Bucket': self.client.config.bucket, 'Key': '2016-09-13/13-59-56-779740/broker1@2016-09-01--2016-10-01-bids-invoices.zip'})