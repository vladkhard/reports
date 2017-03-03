import pytest
import couchdb
import mock
import os.path
from reports.config import Config
from reports.modules import Refunds
from copy import copy
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
    utility = Refunds(config)
    utility.broker = 'test'
    request.cls.ut = utility
    return utility

@pytest.mark.skip
@pytest.mark.usefixtures("db", "ut")
class TestRefunds(BaseBillingTest):

    def test_refunds_utility_output(self):
        data = {
            "awardPeriod": test_award_period, 
            "lots": [test_lot],
            "bids": [test_bid_valid],
        }
        mock_csv = mock.mock_open()
        doc = copy(test_data)
        doc.update(data)
        self.ut.db.save(doc)
        with mock.patch('__builtin__.open', mock_csv):
            self.ut.run()
            assert self.ut.counter == [1, 0, 0, 0, 0]
            assert_csv(mock_csv, 'test/test@---refunds.csv', self.ut.headers, [self.ut.counter, self.ut.config.payments])

    def test_refunds_utility_handler_check(self):
        data = {
            "awardPeriod": test_award_period,
            "lots": [test_lot],
            "bids": [test_bid_valid],
        }
        doc = copy(test_data)
        doc.update(data)
        self.ut.db.save(doc)
        doc = self.ut.db[doc['_id']]
        doc['lots'][0]['value'] = {'amount': 25000, 'currency': 'UAH'}
        self.ut.db.save(doc)
        mock_csv = mock.mock_open()
        with mock.patch('__builtin__.open', mock_csv):
            self.ut.run()
            assert self.ut.counter == [0, 1, 0, 0, 0]
            assert_csv(mock_csv, 'test/test@---refunds.csv', self.ut.headers, [self.ut.counter, sefl.ut.config.payments])

    def test_refunds_utility_middle_handler_check(self):
        data = {
            "awardPeriod": test_award_period,
            "lots": [test_lot],
            "bids": [test_bid_valid],
        }
        doc = copy(test_data)
        doc.update(data)
        self.ut.db.save(doc)
        doc = self.ut.db[doc['_id']]
        doc['lots'][0]['value'] = {'amount': 55000, 'currency': 'UAH'}
        self.ut.db.save(doc)

        mock_csv = mock.mock_open()
        with mock.patch('__builtin__.open', mock_csv):
            self.ut.run()
            assert self.ut.counter == [0, 0, 1, 0, 0]
            assert_csv(mock_csv, 'test/test@---refunds.csv', self.ut.headers, [self.ut.counter, self.ut.config.payments])

    def test_refunds_utility_correct_handler_check(self):
        data = {
            "awardPeriod": test_award_period,
            "lots": [test_lot],
            "bids": [test_bid_valid],
        }
        doc = copy(test_data)
        doc.update(data)
        self.ut.db.save(doc)
        doc = ut.db[doc['_id']]
        doc['lots'][0]['value'] = {'amount': 255000, 'currency': 'UAH'}
        self.ut.db.save(doc)
        mock_csv = mock.mock_open()
        with mock.patch('__builtin__.open', mock_csv):
            self.ut.run()
            assert self.ut.counter == [0, 0, 0, 1, 0]
            assert_csv(mock_csv, 'test/test@---refunds.csv', self.ut.headers, [self.ut.counter, self.ut.config.payments])

    def test_refunds_utility_last_handler_check(self):
        data = {
            "awardPeriod": test_award_period,
            "lots": [test_lot],
            "bids": [test_bid_valid],
        }
        doc = copy(test_data)
        doc.update(data)
        self.ut.db.save(doc)
        doc = ut.db[doc['_id']]
        doc['lots'][0]['value'] = {'amount': 1255000, 'currency': 'UAH'}
        self.ut.db.save(doc)
        mock_csv = mock.mock_open()
        with mock.patch('__builtin__.open', mock_csv):
            self.ut.run()
            assert self.ut.counter == [0, 0, 0, 0, 1]
            assert_csv(mock_csv, 'test/test@---refunds.csv', self.ut.headers, [self.ut.counter, self.ut.config.payments])

    def test_refunds_utility_all_handlers_check(self):
        data = {
                "awardPeriod": {
                    "startDate": '2016-04-17T13:32:25.774673+02:00',
                },
                "lots": [test_lot],
                "bids": [test_bid_valid],
        }
        doc = copy(test_data)
        doc.update(data)
        self.ut.db.save(doc)
        doc.update({'_id': 'sddsfsdd'})
        doc['lots'][0]['value'] = {'amount': 25000, 'currency': 'UAH'}

        self.ut.db.save(doc)
        doc.update({'_id': 'sddsfsdf'})
        doc['lots'][0]['value'] = {'amount': 55000, 'currency': 'UAH'}

        self.ut.db.save(doc)
        doc.update({'_id': 'sddsfsdfa'})
        doc['lots'][0]['value'] = {'amount': 255000, 'currency': 'UAH'}

        self.ut.db.save(doc)
        doc.update({'_id': 'sddsfsdfb'})
        doc['lots'][0]['value'] = {'amount': 1255000, 'currency': 'UAH'}

        self.ut.db.save(doc)
        mock_csv = mock.mock_open()
        self.ut.counter = [0 for _ in self.ut.config.payments]
        with mock.patch('__builtin__.open', mock_csv):
            self.ut.run()
            assert self.ut.counter == [1, 1, 1, 1, 1]
            assert_csv(mock_csv, 'test/test@---refunds.csv', self.ut.headers, [self.ut.counter, self.ut.config.payments])
