import pytest
import mock
import couchdb
import os.path
from reports.config import Config
from copy import copy
from reports.utilities.invoices import InvoicesUtility
from reports.tests.utils import(
    get_mock_parser,
    test_data,
    assert_csv,
    db
)

test_bids_valid = [
    [{
        "owner": "test",
        "status": "active",
        "date": "2016-04-17T13:32:25.774673+02:00",
        "id": "44931d9653034837baff087cfc2fb5ac",
    }],
    [{
        "owner": "test",
        "status": "active",
        "date": "2016-05-05T13:32:25.774673+02:00",
        "id": "44931d9653034837baff087cfc2fb5ac",
    }],

    [{
        "owner": "test",
        "status": "active",
        "date": "2016-05-10T13:32:25.774673+02:00",
        "id": "f55962b1374b43ddb886821c0582bc7f"
    }]]

test_award_period = '2016-04-17T13:32:25.774673+02:00'

@pytest.fixture(scope='function')
def ut(request):    
    mock_parse = get_mock_parser()
    with mock.patch('argparse.ArgumentParser.parse_args', mock_parse):
        utility = InvoicesUtility()
    ut.counter = [0 for _ in utility.config.payments]
    return utility

def test_invoices_utility_output(db, ut):
    data = {
        "awardPeriod": {
            "startDate": test_award_period,
        },
        "enquiryPeriod": {
            "startDate": test_award_period,
        },
        'owner': 'test',
        'bids': test_bids_valid[0],
    }
    
    doc = copy(test_data)
    doc.update(data)
    ut.db.save(doc)
    mock_csv = mock.mock_open()
    with mock.patch('__builtin__.open', mock_csv):
        ut.run()
        assert ut.counter == [1, 0, 0, 0, 0]
        assert_csv(mock_csv, 'test/test@---invoices.csv', ut.headers, [ut.counter, ut.config.payments])
   
def test_invoices_utility_handler_check(db, ut):
    data = {
        "awardPeriod": {
            "startDate": test_award_period,
        },
        "enquiryPeriod": {
            "startDate": test_award_period,
        },
        'owner': 'test',
        'bids': test_bids_valid[0],
    }    
    doc = copy(test_data)
    doc.update(data)
    ut.db.save(doc)
    doc = ut.db[doc['_id']]
    doc.update({'value': {'amount': 25000, 'currency': 'UAH'}})
    ut.db.save(doc)
    mock_csv = mock.mock_open()
    with mock.patch('__builtin__.open', mock_csv):
        ut.run()
        assert ut.counter == [0, 1, 0, 0, 0]
        assert_csv(mock_csv, 'test/test@---invoices.csv', ut.headers, [ut.counter, ut.config.payments])
        
def test_invoices_utility_middle_handler_check(db, ut):
    data = {
        "awardPeriod": {
            "startDate": test_award_period,
        },
        "enquiryPeriod": {
            "startDate": test_award_period,
        },
        'owner': 'test',
        'bids': test_bids_valid[0],
    }
    doc = copy(test_data)
    doc.update(data)
    ut.db.save(doc)
    doc = ut.db[doc['_id']]
    doc.update({'value': {'amount': 55000, 'currency': 'UAH'}})
    ut.db.save(doc)
    mock_csv = mock.mock_open()
    with mock.patch('__builtin__.open', mock_csv):
        ut.run()
        assert ut.counter == [0, 0, 1, 0, 0]
        assert_csv(mock_csv, 'test/test@---invoices.csv', ut.headers, [ut.counter, ut.config.payments])
        
def test_invoices_utility_correct_handler_check(db, ut):
    data = {
        "awardPeriod": {
            "startDate": test_award_period,
        },
        "enquiryPeriod": {
            "startDate": test_award_period,
        },
        'owner': 'test',
        'bids': test_bids_valid[0],
    }
    doc = copy(test_data)
    doc.update(data)
    ut.db.save(doc)
    doc = ut.db[doc['_id']]
    doc.update({'value': {'amount': 255000, 'currency': 'UAH'}})
    ut.db.save(doc)
    mock_csv = mock.mock_open()
    with mock.patch('__builtin__.open', mock_csv):
        ut.run()
        assert ut.counter == [0, 0, 0, 1, 0]
        assert_csv(mock_csv, 'test/test@---invoices.csv', ut.headers, [ut.counter, ut.config.payments])

def test_invoices_utility_last_handler_check(db, ut):
    data = {
        "awardPeriod": {
            "startDate": test_award_period,
        },
        "enquiryPeriod": {
            "startDate": test_award_period,
        },
        'owner': 'test',
        'bids': test_bids_valid[0],
    }
    doc = copy(test_data)
    doc.update(data)
    ut.db.save(doc)
    doc = ut.db[doc['_id']]
    doc.update({'value': {'amount': 1255000, 'currency': 'UAH'}})
    ut.db.save(doc)
    mock_csv = mock.mock_open()
    with mock.patch('__builtin__.open', mock_csv):
        ut.run()
        assert ut.counter == [0, 0, 0, 0, 1]
        assert_csv(mock_csv, 'test/test@---invoices.csv', ut.headers, [ut.counter, ut.config.payments])

def test_invoices_utility_all_handlers_check(db, ut):
    doc = copy(test_data)
    data = {
        "awardPeriod": {
            "startDate": test_award_period,
        },
        "enquiryPeriod": {
            "startDate": test_award_period,
        },
        'owner': 'test',
        'bids': test_bids_valid[0],
    }
    doc.update(data)
    ut.db.save(doc)
    doc.update({
        '_id': 'sddsfsdd',
        'value': {'amount': 25000, 'currency': 'UAH'}
    })
    ut.db.save(doc)
    doc.update({
        '_id': 'sddsfsdf',
        'value': {'amount': 55000, 'currency': 'UAH'}
    })
    ut.db.save(doc)
    doc.update({
        '_id': 'sddsfsdfa',
        'value': {'amount': 255000, 'currency': 'UAH'}
    })
    ut.db.save(doc)
    doc.update({
        '_id': 'sddsfsdfb',
        'value': {'amount': 1255000, 'currency': 'UAH'}
    })
    ut.db.save(doc)
    mock_csv = mock.mock_open()
    with mock.patch('__builtin__.open', mock_csv):
        ut.run()
        assert ut.counter == [1, 1, 1, 1, 1]
        assert_csv(mock_csv, 'test/test@---invoices.csv', ut.headers, [ut.counter, ut.config.payments])
        del ut.db[doc['_id']]
