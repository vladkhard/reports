import pytest
import couchdb
import mock
import os.path
from reports.config import Config
from reports.modules.tenders import Refunds
from copy import copy
from reports.tests.utils import(
    get_mock_parser,
    test_data,
    assert_csv,
    db
)
test_config = os.path.join(os.path.dirname(__file__), 'tests.yaml')
test_bids = [
                    {
                        "date": "2016-04-07T16:36:58.983102+03:00",
                        "owner": "test",
                        "status": "active",
                        "id": "a22ef2b1374b43ddb886821c0582bc7dk",
                        "lotValues": [
                            {
                                "relatedLot": "324d7b2dd7a54df29bad6d0b7c91b2e9",
                                "date": "2016-04-07T16:36:58.983062+03:00",
                            }
                        ],
                    }
                ]
test_lots = [
                    {
                        "status": "complete",
                        "id": "324d7b2dd7a54df29bad6d0b7c91b2e9",
                        "date": '2016-04-17T13:32:25.774673+02:00',
                        "value": {
                            "currency": "UAH",
                            "amount": 2000,
                            "valueAddedTaxIncluded": False,
                        },
                    }
                ]

@pytest.fixture(scope='function')
def ut(request):
    config = Config(test_config)
    config.broker = 'test'
    config.kind = 'general'
    bids = Refunds(config)
    return bids

def test_refunds_utility_output(db, ut):
    data = { "awardPeriod": {
                "startDate": '2016-04-17T13:32:25.774673+02:00',
            },
            "lots": test_lots,
            "bids": test_bids,
    }
    mock_csv = mock.mock_open()
    doc = copy(test_data)
    doc.update(data)
    ut.db.save(doc)
    with mock.patch('__builtin__.open', mock_csv):
        ut.run()
        assert ut.counter == [1, 0, 0, 0, 0]
        assert_csv(mock_csv, 'test/test@---refunds.csv', ut.headers, [ut.counter, ut.config.payments])

def test_refunds_utility_handler_check(db, ut):
    data = { "awardPeriod": {
                "startDate": '2016-04-17T13:32:25.774673+02:00',
            },
            "lots": test_lots,
            "bids": test_bids,
    }
    doc = copy(test_data)
    doc.update(data)
    ut.db.save(doc)
    doc = ut.db[doc['_id']]
    doc['lots'][0]['value'] = {'amount': 25000, 'currency': 'UAH'}
    ut.db.save(doc)
    mock_csv = mock.mock_open()
    with mock.patch('__builtin__.open', mock_csv):
        ut.run()
        assert ut.counter == [0, 1, 0, 0, 0]
        assert_csv(mock_csv, 'test/test@---refunds.csv', ut.headers, [ut.counter, ut.config.payments])

def test_refunds_utility_middle_handler_check(db, ut):
    data = { "awardPeriod": {
                "startDate": '2016-04-17T13:32:25.774673+02:00',
            },
            "lots": test_lots,
            "bids": test_bids,
    }
    doc = copy(test_data)
    doc.update(data)
    ut.db.save(doc)
    doc = ut.db[doc['_id']]
    doc['lots'][0]['value'] = {'amount': 55000, 'currency': 'UAH'}
    ut.db.save(doc)

    mock_csv = mock.mock_open()
    with mock.patch('__builtin__.open', mock_csv):
        ut.run()
        assert ut.counter == [0, 0, 1, 0, 0]
        assert_csv(mock_csv, 'test/test@---refunds.csv', ut.headers, [ut.counter, ut.config.payments])

def test_refunds_utility_correct_handler_check(db, ut):
    data = { "awardPeriod": {
                "startDate": '2016-04-17T13:32:25.774673+02:00',
            },
            "lots": test_lots,
            "bids": test_bids,
    }
    doc = copy(test_data)
    doc.update(data)
    ut.db.save(doc)
    doc = ut.db[doc['_id']]
    doc['lots'][0]['value'] = {'amount': 255000, 'currency': 'UAH'}
    ut.db.save(doc)
    mock_csv = mock.mock_open()
    with mock.patch('__builtin__.open', mock_csv):
        ut.run()
        assert ut.counter == [0, 0, 0, 1, 0]
        assert_csv(mock_csv, 'test/test@---refunds.csv', ut.headers, [ut.counter, ut.config.payments])

def test_refunds_utility_last_handler_check(db, ut):
    data = { "awardPeriod": {
                "startDate": '2016-04-17T13:32:25.774673+02:00',
            },
            "lots": test_lots,
            "bids": test_bids,
    }
    doc = copy(test_data)
    doc.update(data)
    ut.db.save(doc)
    doc = ut.db[doc['_id']]
    doc['lots'][0]['value'] = {'amount': 1255000, 'currency': 'UAH'}
    ut.db.save(doc)
    mock_csv = mock.mock_open()
    with mock.patch('__builtin__.open', mock_csv):
        ut.run()
        assert ut.counter == [0, 0, 0, 0, 1]
        assert_csv(mock_csv, 'test/test@---refunds.csv', ut.headers, [ut.counter, ut.config.payments])
        del ut.db[doc['_id']]

def test_refunds_utility_all_handlers_check(db, ut):
    data = { 
            "awardPeriod": {
                "startDate": '2016-04-17T13:32:25.774673+02:00',
            },
            "lots": test_lots,
            "bids": test_bids,
    }
    doc = copy(test_data)
    doc.update(data)
    ut.db.save(doc)
    doc.update({'_id': 'sddsfsdd'})
    doc['lots'][0]['value'] = {'amount': 25000, 'currency': 'UAH'}

    ut.db.save(doc)
    doc.update({'_id': 'sddsfsdf'})
    doc['lots'][0]['value'] = {'amount': 55000, 'currency': 'UAH'}

    ut.db.save(doc)
    doc.update({'_id': 'sddsfsdfa'})
    doc['lots'][0]['value'] = {'amount': 255000, 'currency': 'UAH'}

    ut.db.save(doc)
    doc.update({'_id': 'sddsfsdfb'})
    doc['lots'][0]['value'] = {'amount': 1255000, 'currency': 'UAH'}

    ut.db.save(doc)
    mock_csv = mock.mock_open()
    ut.counter = [0 for _ in ut.config.payments]
    with mock.patch('__builtin__.open', mock_csv):
        ut.run()
        assert ut.counter == [1, 1, 1, 1, 1]
        assert_csv(mock_csv, 'test/test@---refunds.csv', ut.headers, [ut.counter, ut.config.payments])
        del ut.db[doc['_id']]