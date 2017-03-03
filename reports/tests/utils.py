# coding: utf-8
import os.path
import pytest
import couchdb
from copy import copy
from reports.config import Config


test_config = os.path.join(os.path.dirname(__file__), 'tests.yaml')

test_data = {
    "procurementMethod": "open",
    "status": "complete",
    "owner": "tester",
    "bids": [],
    "doc_type": "Tender",
    "id": "0006651836f34bcda9a030c0bf3c0e6e",
    "_id": "0006651836f34bcda9a030c0bf3c0e6e",
    "tenderID": "UA-2016-11-12-000150",
    "dateModified": "2016-11-31T19:03:53.704712+03:00",
    "tenderPeriod": {
        "startDate": "2016-11-13T15:15:00+02:00",
    },
    "enquiryPeriod": {
        "startDate": "2016-11-13T15:15:00+02:00",
    },
    "value": {
        "currency": "UAH",
        "amount": 1000,
    },
    "procuringEntity": {
        'kind': 'general',
    },
    "procurementMethodType": "belowThreshold",
}


test_contract = {
    "status": "active",
    "id": "1ac8c648538d4930918b0b0a1e884ef2",
    "awardID": "3d5182c5a0424a4f8508da712affa82f"
}

test_bid_invalid_status = {
    "owner": "test",
    "status": "invalid",
    "date": "2016-03-17T13:32:25.774673+02:00",
    "id": "44931d9653034837baff087cfc2fb5ac",
}

test_bid_invalid_date = {
    "status": "active",
    "owner": "test",
    "date": "2016-03-17T13:32:25.774673+02:00",
    "id": "44931d9653034837baff087cfc2fb5ac"
}

test_bid_valid = {
    "owner": "test",
    "status": "active",
    "date": "2016-04-17T13:32:25.774673+02:00",
    "id": "44931d9653034837baff087cfc2fb5ac",
}

test_lot = {
    "id": "324d7b2dd7a54df29bad6d0b7c91b2e9",
    "status": "active",
    "value": {
        "currency": "UAH",
        "amount": 2000,
        "valueAddedTaxIncluded": False,
    }
}

test_eu_qualification_for_valid_bid = {
    "bidID": "44931d9653034837baff087cfc2fb5ac",
    "lotID": test_lot['id']
}

test_lot_values = {
    "relatedLot": "324d7b2dd7a54df29bad6d0b7c91b2e9",
    "date": "2016-04-07T16:36:58.983062+03:00",
}


test_award_period = {
    "startDate": '2016-04-17T13:32:25.774673+02:00'
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


def assert_csv(csv, name, headers, rows):
    csv.assert_called_once_with(name, 'w')
    handler = csv()
    handler.write.assert_any_call('{}{}'.format(
        ','.join(headers), '\r\n'
    ))
    for row in rows:
        handler.write.assert_any_call('{}{}'.format(
            ','.join([str(i) for i in row]), '\r\n'
        ))

class BaseBillingTest(object):

    def assertLen(self, count, data):
        doc = copy(test_data)
        doc.update(data)
        self.ut.db.save(doc)
        response = list(self.ut.response)
        assert count == len(response)


@pytest.fixture(scope='function')
def db(request):
    conf = Config(test_config)
    server = couchdb.Server(os.path.dirname(conf.db_url))
    db_name = os.path.basename(conf.db_url)
    if db_name not in server:
        server.create(db_name)

    def delete():
        server.delete(db_name)
    request.cls.db = server[db_name]
    request.addfinalizer(delete)
