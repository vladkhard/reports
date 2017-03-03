import pytest
import couchdb
import mock
import os.path
from reports.config import Config
from reports.modules import Tenders
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
    bids = Tenders(config)
    request.cls.ut = bids
    return bids


def params(funcarglist):
    def wrapper(function):
        function.funcarglist = funcarglist
        return function
    return wrapper


def pytest_generate_tests(metafunc):
    for funcargs in getattr(metafunc.function, 'funcarglist', ()):
        metafunc.addcall(funcargs=funcargs)


@pytest.mark.usefixtures("db", "ut")
class TestTendersModule(BaseBillingTest):

    @pytest.mark.parametrize("status",
                             ['complete', 'unsuccessful', 'cancelled'])
    def test_complete_lot(self, status):
        lot = test_lot.copy()
        lot['date'] = '2016-04-22T13:32:25.774673+02:00'
        lot['status'] = status
        bid = test_bid_valid.copy()
        bid['lotValues'] = [test_lot_values]
        data = {
            'numberOfBids': 1,
            'awardPeriod': test_award_period,
            "lots": [lot],
            "bids": [bid],
        }
        self.assertLen(1, data)
        response = next(self.ut.response)['value']
        assert response['tender'] == test_data['id']
        assert response['lot'] == lot['id']
        assert response['value'] == lot['value']['amount']

    def test_lot_cancelled_before_bids_disclosure(self):
        # lot.date < bids_disclosure_date
        lot = test_lot.copy()
        lot['date'] = '2016-04-01T13:32:25.774673+02:00'
        lot['status'] = 'cancelled'
        bid = test_bid_valid.copy()
        bid['lotValues'] = [test_lot_values]
        data = {
            'numberOfBids': 1,
            'awardPeriod': test_award_period,
            "lots": [lot],
            "bids": [bid],
        }
        self.assertLen(0, data)

    @pytest.mark.parametrize("status",
                             ['complete', 'unsuccessful', 'cancelled'])
    def test_tender_valid(self, status):
        data = {
            "status": status,
            "date": '2016-04-22T13:32:25.774673+02:00',
            'numberOfBids': 1,
            'awardPeriod': test_award_period,
            "bids": [test_bid_valid],
        }
        self.assertLen(1, data)

    @pytest.mark.parametrize("status",
                             ['cancelled'])
    def test_tender_invalid(self, status):
        data = {
            "status": status,
            "date": '2016-04-01T13:32:25.774673+02:00',
            'numberOfBids': 1,
            'awardPeriod': test_award_period,
            "bids": [test_bid_valid],
        }
        self.assertLen(0, data)

    @pytest.mark.parametrize("status",
                             ['complete', 'unsuccessful', 'cancelled'])
    def test_lot_no_bids(self, status):
        # default
        # if (count_lot_bids(lot, bids) > 0) == False
        lot = test_lot.copy()
        lot['date'] = '2016-04-30T13:32:25.774673+02:00'
        lot['status'] = 'status'
        data = {
            'numberOfBids': 0,
            'awardPeriod': test_award_period,
            "lots": [lot],
            "bids": [],
        }
        self.assertLen(0, data)

    @pytest.mark.parametrize("status", ['complete', 'unsuccessful', 'cancelled'])
    def test_tender_no_bids(self, status):
        # if (tender.numberOfBids > 0) == False
        data = {
            "status": status,
            "date": '2016-04-30T13:32:25.774673+02:00',
            'numberOfBids': 0,
            'awardPeriod': test_award_period,
            "bids": [],
        }
        self.assertLen(0, data)

    def test_invalid_date(self):
        data = {
            "status": 'complete',
            "date": '2016-04-22T13:32:25.774673+02:00',
            'numberOfBids': 1,
            "enquiryPeriod": {
                "startDate": '2016-03-17T13:32:25.774673+02:00',
            },
            'awardPeriod': test_award_period,
            "bids": [test_bid_valid],
        }
        self.assertLen(0, data)

    def test_tenders_view_invalid_method(self):
        data = {
            "procurementMethod": "limited",
        }
        self.assertLen(0, data)

    def test_bids_view_invalid_doc_type(self):
        data = {
            "doc_type": "Plan",
        }
        self.assertLen(0, data)

    @pytest.mark.parametrize("status", ['complete', 'unsuccessful', 'cancelled'])
    def test_invalid_mode(self, status):
        data = {
            "status": status,
            "mode": "test",
            "date": '2016-04-22T13:32:25.774673+02:00',
            'numberOfBids': 1,
            'awardPeriod': test_award_period,
            "bids": [test_bid_valid],
        }
        self.assertLen(0, data)

    @pytest.mark.skip
    def test_tenders_utility_output(self):
        data = {
            "owner": "test",
            "status": "complete",
            "date": '2016-04-22T13:32:25.774673+02:00',
            "procurementMethod": "open",
            'numberOfBids': 2,
            'awardPeriod': {'startDate': '2016-04-22T13:32:25.774673+02:00'},
            "enquiryPeriod": {
                "startDate": '2016-04-17T13:32:25.774673+02:00',
            },
            "contracts": [
                {
                    "status": "active",
                    "date": '2016-04-22T13:32:25.774673+02:00',
                    "dateSigned": '2016-05-22T13:32:25.774673+02:00',
                    "documents": [{
                        'datePublished': "2016-06-22T13:32:25.774673+02:00",
                    }]
                }
            ],
        }
        mock_csv = mock.mock_open()
        doc = copy(test_data)
        doc.update(data)
        self.ut.db.save(doc)
        with mock.patch('__builtin__.open', mock_csv):
            self.ut.run()
            row = [['0006651836f34bcda9a030c0bf3c0e6e,UA-2016-11-12-000150,,complete,,UAH,general,1000,,5.0'],]
            assert_csv(mock_csv, 'test/test@---tenders.csv')

    def test_tender_cancelled(self):
        data = {
            "status": "cancelled",
            "date": '2016-04-01T13:32:25.774673+02:00',
            'numberOfBids': 1,
            'awardPeriod': test_award_period,
            "bids": [test_bid_valid],
        }
        self.assertLen(0, data)

@pytest.mark.usefixtures("db", "ut")
class TestUAProcedure(BaseBillingTest):

    def test_defence_bids_check(self):
        #   (tender.numberOfBids < 2) && !('awards' in tender)) == False
        data = {
            "procurementMethodType": "aboveThresholdUA.defense",
            "date": '2016-04-30T13:32:25.774673+02:00',
            'numberOfBids': 2,
            'awardPeriod': test_award_period,
            "bids": [test_bid_valid.copy() for _ in range(2)],
        }
        self.assertLen(1, data)

    def test_defence_one_bid_with_award(self):
        #   (tender.numberOfBids < 2) && !('awards' in tender)) == False
        data = {
            "procurementMethodType": "aboveThresholdUA.defense",
            "date": '2016-04-30T13:32:25.774673+02:00',
            'numberOfBids': 1,
            'awardPeriod': test_award_period,
            "awards": [{ "status": "active", }],
            "bids": [test_bid_valid],
        }
        self.assertLen(1, data)

    def test_defence_one_bid_without_awards(self):
        data = {
            "procurementMethodType": "aboveThresholdUA.defense",
            "date": '2016-04-30T13:32:25.774673+02:00',
            'numberOfBids': 1,
            'awardPeriod': test_award_period,
            "bids": [test_bid_valid],
        }
        self.assertLen(0, data)

    def test_check_bids_success(self):
        #  if (tender.numberOfBids > 1) == True
        data = {
            "procurementMethodType": "aboveThresholdUA",
            "date": '2016-04-22T13:32:25.774673+02:00',
            'numberOfBids': 2,
            'awardPeriod': test_award_period,
            "bids": [test_bid_valid for _ in range(2)],
        }
        self.assertLen(1, data)

    def test_check_bids_fail(self):
        #  if (tender.numberOfBids > 1) == False
        data = {
            "procurementMethodType": "aboveThresholdUA",
            "date": '2016-04-22T13:32:25.774673+02:00',
            'numberOfBids': 1,
            'awardPeriod': test_award_period,
            "bids": [test_bid_valid],
        }
        self.assertLen(0, data)

    def test_check_lot_bids_fail(self):
        # (count_lot_bids(lot, bids) > 1) == False
        bid = test_bid_valid.copy()
        bid['lotValues'] = [test_lot_values]
        data = {
            "procurementMethodType": "aboveThresholdUA",
            "date": '2016-04-30T13:32:25.774673+02:00',
            'numberOfBids': 2,
            'awardPeriod': test_award_period,
            "lots": [test_lot],
            "bids": [bid],
        }
        self.assertLen(0, data)

    def test_check_lot_bids_success(self):
        lot = test_lot.copy()
        lot['date'] = '2016-04-30T13:32:25.774673+02:00'
        lot['status'] = 'complete'
        bid = test_bid_valid.copy()
        bid['lotValues'] = [test_lot_values]
        data = {
            "procurementMethodType": "aboveThresholdUA",
            "date": '2016-04-30T13:32:25.774673+02:00',
            'numberOfBids': 2,
            'awardPeriod': test_award_period,
            "lots": [lot],
            "bids": [bid.copy() for _ in range(2)],
        }
        self.assertLen(1, data)


@pytest.mark.skip
class TestCDProcedure(BaseBillingTest):
    def test_tenders_view_check_tender_DIALOG_pass(self):
        #   (((tender.qualifications || []).length) > 2) == True
        data = {
            "status": "cancelled",
            "procurementMethodType": "competitiveDialogueEU",
            "date": '2016-04-22T13:32:25.774673+02:00',
            'numberOfBids': 1,
            'awardPeriod': {'startDate': '2016-04-22T13:32:25.774673+02:00'},
            "enquiryPeriod": {
                "startDate": '2016-04-17T13:32:25.774673+02:00',
            },
            "qualifications": [{
                "lotID": "324d7b2dd7a54df29bad6d0b7c91b2e9"
            },
            {
                "lotID": "324d7b2dd7a54df29bad6d0b7c91b2e9"
            },
            {
                "lotID": "324d7b2dd7a54df29bad6d0b7c91b2e9"
            }],
            "qualificationPeriod":{
                "startDate": "2016-04-13T15:15:00+02:00"
            },
            "contracts": test_contracts,
            "tenderPeriod": {
                "startDate": "2016-11-13T15:15:00+02:00",
            },
            "bids": test_bids,
        }
        assertLen(1, data, ut)

    def test_tenders_view_check_tender_DIALOG_fail(sefl):
        #   (((tender.qualifications || []).length) > 2) == False
        data = {
            "status": "cancelled",
            "procurementMethodType": "competitiveDialogueEU",
            "date": '2016-04-22T13:32:25.774673+02:00',
            'numberOfBids': 1,
            'awardPeriod': {'startDate': '2016-04-22T13:32:25.774673+02:00'},
            "enquiryPeriod": {
                "startDate": '2016-04-17T13:32:25.774673+02:00',
            },
            "qualifications": [{
                "lotID": "324d7b2dd7a54df29bad6d0b7c91b2e9"
            },
            {
                "lotID": "324d7b2dd7a54df29bad6d0b7c91b2e9"
            }],
            "qualificationPeriod":{
                "startDate": "2016-04-13T15:15:00+02:00"
            },
            "contracts": test_contracts,
            "tenderPeriod": {
                "startDate": "2016-11-13T15:15:00+02:00",
            },
            "bids": test_bids,
        }
        assertLen(0, data, ut)

    def test_tenders_view_comp_dialog_active(self):
         # if (['competitiveDialogueEU', 'competitiveDialogueUA'].indexOf(doc.procurementMethodType) !== -1) == True &
         # if (['unsuccessful', 'cancelled'].indexOf(doc.status) === -1) == True
        data = {
            "status": "complete",
            "procurementMethodType": "competitiveDialogueEU",
            "date": '2016-04-22T13:32:25.774673+02:00',
            "qualifications": [{
                "lotID": "324d7b2dd7a54df29bad6d0b7c91b2e9"
            },
            {
                "lotID": "324d7b2dd7a54df29bad6d0b7c91b2e9"
            }],
            "qualificationPeriod":{
                "startDate": "2016-04-13T15:15:00+02:00"
            },
            'numberOfBids': 2,
            'awardPeriod': {'startDate': '2016-04-22T13:32:25.774673+02:00'},
            "enquiryPeriod": {
                "startDate": '2016-04-17T13:32:25.774673+02:00',
            },
            "contracts": [
                {
                    "status": "active",
                    "date": '2016-04-22T13:32:25.774673+02:00',
                    "dateSigned": '2016-05-22T13:32:25.774673+02:00',
                    "documents": [{
                        'datePublished': "2016-06-22T13:32:25.774673+02:00",
                    }]
                }
            ],
        }
        self.assertLen(0, data)


@pytest.mark.usefixtures("db", "ut")
class TestEUProcedure(BaseBillingTest):
    def test_check_qualifications(self):
        #  (((tender.qualifications || []).length) > 1) == True
        data = {
            "procurementMethodType": "aboveThresholdEU",
            "date": '2016-04-22T13:32:25.774673+02:00',
            'numberOfBids': 2,
            'awardPeriod': test_award_period,
            "qualifications": [test_eu_qualification_for_valid_bid
                               for _ in range(2)],
            "qualificationPeriod": test_award_period,
            "bids": [test_bid_valid for _ in range(2)],
        }
        self.assertLen(1, data)

    def test_check_qualifications_fail(self):
        #  (((tender.qualifications || []).length) > 1) == False
        data = {
            "procurementMethodType": "aboveThresholdEU",
            "date": '2016-04-22T13:32:25.774673+02:00',
            'numberOfBids': 2,
            'awardPeriod': test_award_period,
            "qualifications": [test_eu_qualification_for_valid_bid
                               ],
            "qualificationPeriod": test_award_period,
            "bids": [test_bid_valid for _ in range(2)],
        }
        self.assertLen(0, data)

    def test_check_lot_qualifications_fail(self):
        # if (count_lot_qualifications((tender.qualifications || []), lot.id) > 1) == False
        lot = test_lot.copy()
        lot['status'] = 'complete'
        lot["date"] = '2016-04-30T13:32:25.774673+02:00'
        bid = test_bid_valid.copy()
        bid['lotValues'] = [test_lot_values]
        qual = test_eu_qualification_for_valid_bid.copy()
        qual['bidID'] = 'slkfldskfdlskfdsklf'
        qual['lotID'] = 'lkxv;aivaoidfj'
        data = {
            "procurementMethodType": "aboveThresholdEU",
            "date": '2016-04-22T13:32:25.774673+02:00',
            'numberOfBids': 2,
            'awardPeriod': test_award_period,
            "qualifications": [test_eu_qualification_for_valid_bid,
                               qual],
            "qualificationPeriod": test_award_period,
            'lots': [lot],
            "bids": [bid.copy() for _ in range(2)],
        }
        self.assertLen(0, data)

    def test_check_lot_qualifications(self):
        # if (count_lot_qualifications((tender.qualifications || []), lot.id) > 1) == True
        lot = test_lot.copy()
        lot['status'] = 'complete'
        lot["date"] = '2016-04-30T13:32:25.774673+02:00'
        bid = test_bid_valid.copy()
        bid['lotValues'] = [test_lot_values]
        data = {
            "procurementMethodType": "aboveThresholdEU",
            "date": '2016-04-22T13:32:25.774673+02:00',
            'numberOfBids': 2,
            'awardPeriod': test_award_period,
            "qualifications": [test_eu_qualification_for_valid_bid
                               for _ in range(2)],
            "qualificationPeriod": test_award_period,
            'lots': [lot],
            "bids": [bid.copy() for _ in range(2)],
        }
        self.assertLen(1, data)
