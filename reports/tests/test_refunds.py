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
    config.broker = 'tester'
    utility = Refunds(config)
    request.cls.ut = utility
    return utility


@pytest.mark.usefixtures("db", "ut")
class TestRefunds(BaseBillingTest):

    def test_utility_output(self):
        data = {
            "date": '2016-04-22T13:32:25.774673+02:00',
            'numberOfBids': 1,
            'awardPeriod': test_award_period,
            "bids": [test_bid_valid],
        }

        self.assertLen(1, data)
        mock_csv = mock.mock_open()
        with mock.patch('__builtin__.open', mock_csv):
            self.ut.run()
            assert self.ut.counter == [1, 0, 0, 0, 0]
            assert_csv(mock_csv, 'test/tester@---refunds.csv', self.ut.headers, [self.ut.counter, self.ut.config.payments])

    def test_handler_check(self):
        data = {
            "date": '2016-04-22T13:32:25.774673+02:00',
            'numberOfBids': 1,
            'awardPeriod': test_award_period,
            "bids": [test_bid_valid],
            "value": {'amount': 25000, 'currency': 'UAH'}
        }
        self.assertLen(1, data)
        mock_csv = mock.mock_open()
        with mock.patch('__builtin__.open', mock_csv):
            self.ut.run()
            assert self.ut.counter == [0, 1, 0, 0, 0]
            assert_csv(mock_csv, 'test/tester@---refunds.csv', self.ut.headers, [self.ut.counter, self.ut.config.payments])

    def test_refunds_utility_middle_handler_check(self):
        data = {
            "date": '2016-04-22T13:32:25.774673+02:00',
            'numberOfBids': 1,
            'awardPeriod': test_award_period,
            "bids": [test_bid_valid],
            "value": {'amount': 55000, 'currency': 'UAH'}
        }
        self.assertLen(1, data)

        mock_csv = mock.mock_open()
        with mock.patch('__builtin__.open', mock_csv):
            self.ut.run()
            assert self.ut.counter == [0, 0, 1, 0, 0]
            assert_csv(mock_csv, 'test/tester@---refunds.csv', self.ut.headers, [self.ut.counter, self.ut.config.payments])

    def test_refunds_utility_correct_handler_check(self):
        data = {
            "date": '2016-04-22T13:32:25.774673+02:00',
            'numberOfBids': 1,
            'awardPeriod': test_award_period,
            "bids": [test_bid_valid],
            "value": {'amount': 255000, 'currency': 'UAH'}
        }
        self.assertLen(1, data)

        mock_csv = mock.mock_open()
        with mock.patch('__builtin__.open', mock_csv):
            self.ut.run()
            assert self.ut.counter == [0, 0, 0, 1, 0]
            assert_csv(mock_csv, 'test/tester@---refunds.csv', self.ut.headers, [self.ut.counter, self.ut.config.payments])

    def test_refunds_utility_last_handler_check(self):
        data = {
            "date": '2016-04-22T13:32:25.774673+02:00',
            'numberOfBids': 1,
            'awardPeriod': test_award_period,
            "bids": [test_bid_valid],
            "value": {'amount': 1255000, 'currency': 'UAH'}
        }
        self.assertLen(1, data)

        mock_csv = mock.mock_open()
        with mock.patch('__builtin__.open', mock_csv):
            self.ut.run()
            assert self.ut.counter == [0, 0, 0, 0, 1]
            assert_csv(mock_csv, 'test/tester@---refunds.csv', self.ut.headers, [self.ut.counter, self.ut.config.payments])

    def test_refunds_utility_all_handlers_check(self):
        _doc = copy(test_data)
        for id, value in zip(['1', '2', '3', '4', '5'], [1000, 25000, 55000, 255000, 1255000]):
            doc = copy(_doc)
            doc.update({
                "_id": id,
                "date": '2016-04-22T13:32:25.774673+02:00',
                'numberOfBids': 1,
                'awardPeriod': test_award_period,
                "bids": [test_bid_valid],
                "value": {'amount': value, 'currency': 'UAH'}
            })
            self.ut.db.save(doc)
        mock_csv = mock.mock_open()
        with mock.patch('__builtin__.open', mock_csv):
            self.ut.run()
            assert self.ut.counter == [1, 1, 1, 1, 1]
            assert_csv(mock_csv, 'test/tester@---refunds.csv', self.ut.headers, [self.ut.counter, self.ut.config.payments])
