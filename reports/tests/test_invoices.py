import pytest
import mock
import couchdb
import os.path
from reports.config import Config
from copy import copy
from reports.modules import (
    Invoices
)
from reports.tests.utils import (
    BaseBillingTest,
    test_data,
    assert_csv,
    db,
    test_config,
    test_bid_invalid_status,
    test_bid_invalid_date,
    test_eu_qualification_for_valid_bid,
    test_bid_valid,
    test_lot,
    test_award_period,
    test_lot_values
)




@pytest.fixture(scope='function')
def ut(request):
    config = Config(test_config)
    utility = Invoices(config)
    utility.broker = 'test'
    request.cls.ut = utility
    return utility


@pytest.mark.skip
@pytest.mark.usefixtures("db", "ut")
class TestInvoices(BaseBillingTest):

    def test_simple(self):
        data = {
            "awardPeriod": test_award_period,
            'bids': [test_bid_valid],
        }
        self.assertLen(1, data)
        mock_csv = mock.mock_open()
        with mock.patch('__builtin__.open', mock_csv):
            self.ut.run()
            assert self.ut.counter == [1, 0, 0, 0, 0]
            assert_csv(mock_csv, 'test/test@---invoices.csv', ut.headers, [ut.counter, ut.config.payments])

    def test_invoices_utility_handler_check(self):
        data = {
            "awardPeriod": test_award_period,
            'bids': [test_bids_valid],
        }
        doc = copy(test_data)
        doc.update(data)
        self.ut.db.save(doc)
        doc = ut.db[doc['_id']]
        doc.update({'value': {'amount': 25000, 'currency': 'UAH'}})
        self.ut.db.save(doc)
        mock_csv = mock.mock_open()
        with mock.patch('__builtin__.open', mock_csv):
            self.ut.run()
            assert self.ut.counter == [0, 1, 0, 0, 0]
            assert_csv(mock_csv, 'test/test@---invoices.csv', self.ut.headers, [self.ut.counter, self.ut.config.payments])

    def test_invoices_utility_middle_handler_check(self):
        data = {
            "awardPeriod": test_award_period,
            'bids': [test_bid_valid],
        }
        doc = copy(test_data)
        doc.update(data)
        self.ut.db.save(doc)
        doc = ut.db[doc['_id']]
        doc.update({'value': {'amount': 55000, 'currency': 'UAH'}})
        self.ut.db.save(doc)
        mock_csv = mock.mock_open()
        with mock.patch('__builtin__.open', mock_csv):
            self.ut.run()
            assert self.ut.counter == [0, 0, 1, 0, 0]
            assert_csv(mock_csv, 'test/test@---invoices.csv', self.ut.headers, [self.ut.counter, self.ut.config.payments])

    def test_invoices_utility_correct_handler_check(self):
        data = {
            "awardPeriod": test_award_period,
            'bids': test_bid_valid,
        }
        doc = copy(test_data)
        doc.update(data)
        self.ut.db.save(doc)
        doc = ut.db[doc['_id']]
        doc.update({'value': {'amount': 255000, 'currency': 'UAH'}})
        ut.db.save(doc)
        mock_csv = mock.mock_open()
        with mock.patch('__builtin__.open', mock_csv):
            self.ut.run()
            assert self.ut.counter == [0, 0, 0, 1, 0]
            assert_csv(mock_csv, 'test/test@---invoices.csv', self.ut.headers, [self.ut.counter, self.ut.config.payments])

    def test_invoices_utility_last_handler_check(self):
        data = {
            "awardPeriod": test_award_period,
            'bids': [test_bids_valid],
        }
        doc = copy(test_data)
        doc.update(data)
        self.ut.db.save(doc)
        doc = ut.db[doc['_id']]
        doc.update({'value': {'amount': 1255000, 'currency': 'UAH'}})
        self.ut.db.save(doc)
        mock_csv = mock.mock_open()
        with mock.patch('__builtin__.open', mock_csv):
            self.ut.run()
            assert self.ut.counter == [0, 0, 0, 0, 1]
            assert_csv(mock_csv, 'test/test@---invoices.csv', self.ut.headers, [self.ut.counter, self.ut.config.payments])

    def test_invoices_utility_all_handlers_check(self):
        doc = copy(test_data)
        data = {
            "awardPeriod":  test_award_period,
            'bids': [test_bid_valid],
        }
        doc.update(data)
        self.ut.db.save(doc)
        doc.update({
            '_id': 'sddsfsdd',
            'value': {'amount': 25000, 'currency': 'UAH'}
        })
        self.ut.db.save(doc)
        doc.update({
            '_id': 'sddsfsdf',
            'value': {'amount': 55000, 'currency': 'UAH'}
        })
        self.ut.db.save(doc)
        doc.update({
            '_id': 'sddsfsdfa',
            'value': {'amount': 255000, 'currency': 'UAH'}
        })
        self.ut.db.save(doc)
        doc.update({
            '_id': 'sddsfsdfb',
            'value': {'amount': 1255000, 'currency': 'UAH'}
        })
        self.ut.db.save(doc)
        mock_csv = mock.mock_open()
        with mock.patch('__builtin__.open', mock_csv):
            self.ut.run()
            assert self.ut.counter == [1, 1, 1, 1, 1]
            assert_csv(mock_csv, 'test/test@---invoices.csv', self.ut.headers, [self.ut.counter, self.ut.config.payments])
            del self.ut.db[doc['_id']]
