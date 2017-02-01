# coding: utf-8
import mock
import os.path
import pytest
import couchdb
from copy import copy
from reports.config import Config
from reports.helpers import create_db_url


test_config = os.path.join(os.path.dirname(__file__), 'tests.ini')
test_data = {
    "procurementMethod": "open",
    "status": "complete",
    "owner": "test",
    "doc_type": "Tender",
    'tender': '0006651836f34bcda9a030c0bf3c0e6e',
    "_id": "0006651836f34bcda9a030c0bf3c0e6e",
    "tenderID": "UA-2016-11-12-000150",
    "dateModified": "2016-04-31T19:03:53.704712+03:00",
    "tenderPeriod": {
        "startDate": "2016-11-13T15:15:00+02:00",
    },
    "enquiryPeriod": {
        "startDate": "2016-11-13T15:15:00+02:00",
    },
    "contracts": [{
        "status": "",
        "id": "1ac8c648538d4930918b0b0a1e884ef2",
        "awardID": "3d5182c5a0424a4f8508da712affa82f"
    }],
    "bids": [{
        "owner": "test",
        "date": "data",
        "id": "some_id"
    }],
    "value": {
        "currency": "UAH",
        "amount": 1000,
    },
    "procuringEntity": {
        'kind': 'general',
    },
}


class MockCurrencyResponce(object):
    text = u'''[
     {"r030":643,"txt":"Російський рубль",
     "rate":2,"cc":"RUB","exchangedate":"16.05.2016"},
     {"r030":978,"txt":"Євро",
     "rate":2,"cc":"EUR","exchangedate":"16.05.2016"},
     {"r030":840,"txt":"Долар США",
     "rate":2,"cc":"USD","exchangedate":"16.05.2016"}]
    '''


def get_mock_parser():
    mock_parse = mock.MagicMock()
    type(mock_parse.return_value).config = mock.PropertyMock(
        return_value=test_config)
    type(mock_parse.return_value).broker = mock.PropertyMock(
        return_value='test')
    type(mock_parse.return_value).period = mock.PropertyMock(
        return_value=[])
    type(mock_parse.return_value).kind = mock.PropertyMock(
        return_value=['kind', 'general'])
    type(mock_parse.return_value).status = mock.PropertyMock(
        return_value={'action': '', 'statuses': ['complete', 'active']})

    return mock_parse


def assert_csv(csv, name , headers, rows):
    csv.assert_called_once_with(name, 'w')
    handler = csv()
    handler.write.assert_any_call('{}{}'.format(
        ','.join(headers), '\r\n'
    ))
    for row in rows:
        handler.write.assert_any_call('{}{}'.format(
            ','.join([str(i) for i in row]), '\r\n'
        ))


def assertLen(count, data, utility):  
    doc = copy(test_data)
    doc.update(data)
    utility.db.save(doc)
    utility.get_response()
    utility.response = list(utility.response)
    assert count == len(utility.response)


@pytest.fixture(scope='function')
def db(request):
    conf = Config(test_config)
    host = conf.get_option('db', 'host')
    port = conf.get_option('db', 'port')
    user = conf.get_option('admin', 'username')
    passwd = conf.get_option('admin', 'password')

    db_name = conf.get_option('db', 'name')
    server = couchdb.Server(
        create_db_url(host, port, user, passwd)
    )
    if db_name not in server:
        server.create(db_name)
    def delete():
        server.delete(db_name)
    request.addfinalizer(delete)

