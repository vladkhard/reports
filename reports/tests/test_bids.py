import pytest
import mock
from copy import copy
from dateutil.parser import parse
from reports.config import Config
from reports.modules import Bids
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
    config.broker = 'test'
    bids = Bids(config)
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
class TestBidsModule(BaseBillingTest):

    def test_bid_invalid_date(self):
        data = {
            "awardPeriod": test_award_period,
            "bids": [test_bid_invalid_date],
        }
        self.assertLen(0, data)

    def test_tender_test_mode(self):
        # doc.mode == 'test'
        data = {
            'mode': 'test',
            "awardPeriod": test_award_period,
            "bids": [test_bid_valid],
        }
        self.assertLen(0, data)

    def test_bid_invalid_status(self):
        # bid.status != 'active'
        data = {
            "procurementMethod": "open",
            "awardPeriod": test_award_period,
            'bids': [test_bid_invalid_status],
        }
        self.assertLen(0, data)

    def test_tender_invalid_procurement_method(self):
        # tender.procurementMethod != 'open'
        data = {
            "procurementMethod": "limited",
            "awardPeriod": test_award_period,
            'bids': [test_bid_valid],
        }
        self.assertLen(0, data)

    def test_doc_type_not_tender(self):
        # doc.doc_type != 'Tender'
        data = {
            "doc_type": "Plan",
        }
        self.assertLen(0, data)

    def test_no_disclojure_date(self):
        # !bids_disclosure_date {return}
        data = {
            "awardPeriod": {
                "startDate": "",
            },
            "bids": [test_bid_valid],
        }
        self.assertLen(0, data)

    def test_view_valid(self):
        data = {
            "awardPeriod": test_award_period,
            'bids': [test_bid_valid],
        }
        self.assertLen(1, data)
        response = list(self.ut.response)
        assert 1000 == response[0]['value']['value']
        assert test_bid_valid['id'] == response[0]['value']['bid']
        assert test_data['id'] == response[0]['value']['tender']
        assert test_data['tenderID'] == response[0]['value']['tenderID']
        assert test_data['value']['currency'] == response[0]['value']['currency']

    def test_tender_cancelled_before_award(self):
        # ((new Date(tender.date)) < (new Date(bids_disclojure_date))) == True
        data = {
            "status": "cancelled",
            "cancellations": [{
                "cancellationOf": "tender",
                "status": "active"
            }],
            "awardPeriod": test_award_period,
            'date': parse(test_award_period['startDate']).replace(day=1).isoformat(),
            "bids": [test_bid_valid],
        }
        self.assertLen(0, data)

    def test_tender_cancelled_after_award(self):
        # tender.date > bids_disclojure_date
        data = {
            "date": parse(test_award_period['startDate']).replace(month=6).isoformat(),
            "status": "cancelled",
            "cancellations": [{
                            "cancellationOf": "tender",
                            "date": "2016-04-13T15:10:00+02:00",
                            "status": "active"
            }],
            "awardPeriod": test_award_period,
            "bids": [test_bid_valid],
        }
        self.assertLen(1, data)

    def test_lot_cancelled_before_award(self):
        lot = test_lot.copy()
        lot['status'] = 'cancelled'
        lot['date'] = parse(test_award_period['startDate']).replace(day=1).isoformat()
        bid = test_bid_valid.copy()
        bid['lotValues'] = [test_lot_values]
        data = {
            "awardPeriod": test_award_period,
            "lots": [lot],
            "bids": [bid],
        }
        self.assertLen(0, data)

    def test_lots_with_invalid_bids(self):
        for bid in [test_bid_invalid_status]:
            lot = test_lot.copy()
            lot['date'] = parse(test_award_period['startDate']).replace(day=6).isoformat()
            bid['lotValues'] = [test_lot_values]
            data = {
                "awardPeriod": test_award_period,
                "lots": [lot],
                "bids": [bid],
            }
            self.assertLen(0, data)
            del self.db[test_data['id']]

    def test_view_with_lots(self):
        bid = test_bid_valid.copy()
        bid['lotValues'] = [test_lot_values]
        data = {
            "awardPeriod": test_award_period,
            "lots": [test_lot],
            "bids": [bid],
        }
        self.assertLen(1, data)

    def test_utility_output_with_lots(self):
        bid = test_bid_valid.copy()
        bid['lotValues'] = [test_lot_values]
        data = {
            "awardPeriod": test_award_period,
            "lots": [test_lot],
            "bids": [bid],
        }
        mock_csv = mock.mock_open()
        doc = copy(test_data)
        doc.update(data)
        self.ut.db.save(doc)
        with mock.patch('__builtin__.open', mock_csv):
            self.ut.run()
            print list(self.ut.response)
            row = [
                test_data['id'],
                test_data['tenderID'],
                test_lot['id'],
                test_lot['value']['amount'],
                test_lot['value']['currency'],
                bid['id'],
                '',
                self.ut.get_payment(test_lot['value']['amount']),
            ]
            assert_csv(mock_csv, 'test/test@---bids.csv', self.ut.headers, [row])

        def test_view_check_cancelled_related_lot(self):
            lot = test_lot.copy()
            lot['status'] = 'cancelled'
            data = {
                "procurementMethodType": "belowThreshold",
                "awardPeriod": {
                    "startDate": test_award_period,
                },
                "cancellations":[{
                            "status": "active",
                            "cancelationOf": "lot",
                            "relatedLot": "324d7b2dd7a54df29bad6d0b7c91b2e9",
                        }],
                "lots": [lot],
                "bids": test_bid_valid,
            }
            self.assertLen(1, data)

    def test_utility_output(self):
        data = {
            'awardPeriod': test_award_period,
            'bids': [test_bid_valid],
        }
        mock_csv = mock.mock_open()
        doc = copy(test_data)
        doc.update(data)
        self.db.save(doc)
        with mock.patch('__builtin__.open', mock_csv):
            self.ut.run()
            assert_csv(mock_csv, 'test/test@---bids.csv', self.ut.headers, [
                [
                    test_data['id'],
                    test_data['tenderID'],
                    '',
                    str(test_data['value']['amount']),
                    test_data['value']['currency'],
                    test_bid_valid['id'],
                    '',
                    str(self.ut.get_payment(test_data['value']['amount']))
                ]])

    @pytest.mark.skip
    def test_view_check_audit_documents(self):
        data = {
            "awardPeriod": test_award_period,
            "documents": [
                {
                    "format": "text/plain",
                    "title": "audit_{}.yaml".format(test_data['id']),
                    "documentOf": "tender",
                    "dateModified": "2016-11-13T15:15:00+02:00",
                    "id": "412e55ba06e847749c24b774fc75b805"
                }
            ],
            "bids": [test_bid_valid],
        }
        self.assertLen(1, data)
        response = list(self.ut.response)
        assert response[0]['value']['audits'] is not None
    
    @pytest.mark.skip
    def test_view_check_audit_2_documents_dateModified_check(self):
        data = {
            "status": "unsuccessful",
            "procurementMethodType": "belowThreshold",
            "awardPeriod": {
                "startDate": "2016-11-13T15:15:00+02:00",
            },
            "documents":[
                {
                   "format": "text/plain",
                   "title": "audit_0006651836f34bcda9a030c0bf3c0e6e_324d7b2dd7a54df29bad6d0b7c91b2e9.yaml",
                   "documentOf": "tender",
                   "datePublished": "2016-06-01T12:17:40.193283+03:00",
                   "dateModified": "2016-06-01T12:26:40.193305+03:00",
                   "id": "412e55ba06e847749c24b774fc75b805"
                },
                {
                   "format": "text/plain",
                   "title": "audit_0006651836f34bcda9a030c0bf3c0e6e_324d7b2dd7a54df29bad6d0b7c91b2e9.yaml",
                   "documentOf": "tender",
                   "datePublished": "2016-06-01T12:18:40.193283+03:00",
                   "dateModified": "2016-06-01T12:19:40.193305+03:00",
                   "id": "412e55ba06e847749c24b774fc75b805"
                }
            ],
            "lots": [
                {
                    "status": "unsuccessful",
                    "id": "324d7b2dd7a54df29bad6d0b7c91b2e9",
                    "value": {
                        "currency": "UAH",
                        "amount": 2000,
                        "valueAddedTaxIncluded": False,
                    },
                }
            ],
            "bids": [test_bid_valid for _ in range(2)],
        }
        self.assertLen(1, data)
        self.ut.get_response()
        raise
        self.ut.response = list(self.ut.response)
        response = list(self.ut.response)
        assert response[0]['value']['audits']['datePublished'] == "2016-06-01T12:18:40.193283+03:00"

    def test_view_period_edge_limit_check(self):
        self.ut.config.broker = 'test'
        data = {
            "_id": "10028cddd23540e5b6abb9efd2756de1",
            "awardPeriod": {
                "startDate": "2016-11-01T17:01:00+02:00",
            },
            'owner': 'teser',
            'bids': [test_bid_valid],
        }
        doc = copy(test_data)
        doc.update(data)
        self.ut.db.save(doc)
        data = {
            "_id": "10028cddd23540e3b6abb9efd2756de2",
            "awardPeriod": {
                "startDate": "2016-11-01T17:00:00+02:00",
            },
            'owner': 'teser',
            'bids': [test_bid_valid],
        }
        doc = copy(test_data)
        doc.update(data)
        self.ut.db.save(doc)
        data = {
            "_id": "10028cddd23540e3b60bb9efd2756de3",
            "awardPeriod": {
                "startDate": "2016-11-01T16:59:00+02:00",
            },
            'owner': 'teser',
            'bids': [test_bid_valid],
        }
        doc = copy(test_data)
        doc.update(data)
        self.ut.db.save(doc)
        data = {
            "_id": "10028cddd23520e3b6abb9efd2756de4",
            "awardPeriod": {
                "startDate": "2016-12-01T17:00:00+02:00",
            },
            'owner': 'teser',
            'bids': [test_bid_valid],
        }
        doc = copy(test_data)
        doc.update(data)
        self.ut.db.save(doc)
        data = {
            "_id": "10028cddd23540e3b50bb9efd2756de5",
            "awardPeriod": {
                "startDate": "2016-12-01T16:59:00+02:00",
            },
            'owner': 'teser',
            'bids': [test_bid_valid],
        }
        doc = copy(test_data)
        doc.update(data)
        self.ut.db.save(doc)
        data = {
            "_id": "00028aasd2isdfsde5b6abb9efd2756de6",
            "awardPeriod": {
                "startDate": "2016-12-01T17:01:00+02:00",
            },
            'owner': 'teser',
            'bids': [test_bid_valid],
        }
        doc = copy(test_data)
        doc.update(data)
        self.ut.db.save(doc)
        data = {
            "_id": "00028aasd2isdfsde5b6abb9efd2756de7",
            "awardPeriod": {
                "startDate": "2016-11-30T17:01:00+02:00",
            },
            'owner': 'teser',
            'bids': [test_bid_valid],
        }
        doc = copy(test_data)
        doc.update(data)
        self.ut.db.save(doc)

        self.ut.config.period = [
            "2016-11-01T15:00:00",
            "2016-12-01T15:00:00"
        ]
        # id ends on e1,e2,e5,e7
        assert 4 == len(list(self.ut.response))

    @pytest.mark.skip
    def test_view_period(self):
        self.ut.config.broker = 'test'
        data = {
            "awardPeriod": {
                "startDate": test_award_period,
            },
            'owner': 'teser',
            'bids': [test_bid_valid],
        }
        doc = copy(test_data)
        doc.update(data)
        self.ut.db.save(doc)
        data = {
            "_id": "10028cddd23540e5b6abb9efd2756d1d",
            "awardPeriod": {
                "startDate": "2016-11-09T15:00:00+02:00",
            },
            'owner': 'teser',
            'bids': [test_bid_valid],
        }
        doc = copy(test_data)
        doc.update(data)
        self.ut.db.save(doc)
        data = {
            "_id": "00028aasd2isdfsde5b6abb9efd2756d1d",
            "awardPeriod": {
                "startDate": "2016-11-30T15:00:00+02:00",
            },
            'owner': 'teser',
            'bids': [test_bid_valid],
        }
        doc = copy(test_data)
        doc.update(data)
        self.ut.db.save(doc)
        self.ut.config.period = ['', '']
        assert 3 == len(list(self.ut.response))
        self.ut.start_date = "2016-11-10T15:00:00"
        self.ut.end_date = ''
        self.ut.get_response()
        assert 1 == len(list(self.ut.response))
        self.ut.start_date = "2016-12-01T15:00:00"
        self.ut.end_date = ''
        self.ut.get_response()
        assert 0 == len(list(self.ut.response))
        self.ut.start_date = "2016-11-01T15:00:00"
        self.ut.end_date = "2016-12-01T15:00:00"
        self.ut.get_response()
        assert 2 == len(list(self.ut.response))

    @pytest.mark.skip
    def test_multiple_audits_no_lots(self):
        data = {
            "status": "unsuccessful",
            "procurementMethodType": "belowThreshold",
            "awardPeriod": {
                "startDate": "2016-11-13T15:15:00+02:00",
                "endDate": "2016-12-30T15:15:00+02:00",
            },
            "documents": [
                {
                   "format": "text/plain",
                   "title": "audit_0006651836f34bcda9a030c0bf3c0e6e_324d7b2dd7a54df29bad6d0b7c91b2e9.yaml",
                   "documentOf": "tender",
                   "datePublished": "2016-06-01T12:17:40.193283+03:00",
                   "dateModified": "2016-06-01T12:26:40.193305+03:00",
                   "id": "412e55ba06e847749c24b774fc75b805"
                },
                {
                   "format": "text/plain",
                   "title": "audit_0006651836f34bcda9a030c0bf3c0e6e_324d7b2dd7a54df29bad6d0b7c91b2e9.yaml",
                   "documentOf": "tender",
                   "datePublished": "2016-06-01T12:18:40.193283+03:00",
                   "dateModified": "2016-06-01T12:19:40.193305+03:00",
                   "id": "412e55ba06e847749c24b774fc75b805"
                }
            ],
            "bids": [test_bid_valid],
        }
        self.assertLen(1, data)
        response = list(self.ut.response)
        assert response[0]['value']['audits']['datePublished'] ==\
                "2016-06-01T12:18:40.193283+03:00"


@pytest.mark.usefixtures("db", "ut")
class TestUAProcedure(BaseBillingTest):

    def test_UA_tender_one_bid(self):
        data = {
            "procurementMethodType": "aboveThresholdUA",
            "numberOfBids": 1,
            "awardPeriod": {
                "startDate": test_award_period,
            },
            'bids': [test_bid_valid],
        }
        self.assertLen(0, data)

    def test_defense_test_no_bids(self):
        data = {
            "numberOfBids": 0,
            "procurementMethodType": "aboveThresholdUA.defense",
            "awardPeriod": test_award_period,
        }
        self.assertLen(0, data)

    @pytest.mark.parametrize("c", [1, 2])
    def test_check_number_of_bids_defense(self, c):
        data = {
            "numberOfBids": c,
            "procurementMethodType": "aboveThresholdUA.defense",
            "awardPeriod": test_award_period,
            #"awards": [{"status": "active"}u]
            "bids": [test_bid_valid for _ in range(c)]
        }
        self.assertLen(c, data)

    @pytest.mark.parametrize("p_type", ["aboveThresholdUA.defense",
                                        "aboveThresholdUA"])
    def test_unsuccessfull_lot_no_bids(self, p_type):
        lot = test_lot.copy()
        lot['status'] = 'unsuccessful'
        data = {
            "procurementMethodType": p_type,
            "awardPeriod": test_award_period,
            "lots": [lot]
        }
        self.assertLen(0, data)

    @pytest.mark.parametrize("p_type", ["aboveThresholdUA.defense",
                                        "aboveThresholdUA"])
    def test_unsuccessfull_lot_one_bid(self, p_type):
        lot = test_lot.copy()
        lot['status'] = 'unsuccessful'
        bid = test_bid_valid.copy()
        bid['lotValues'] = [test_lot_values]

        data = {
            "procurementMethodType": p_type,
            "awardPeriod": test_award_period,
            "lots": [lot],
            "bids": [bid]
        }
        self.assertLen(0, data)

    @pytest.mark.parametrize("p_type", ["aboveThresholdUA.defense",
                                        "aboveThresholdUA"])
    def test_unsuccessfull_lot_with_bids(self, p_type):
        lot = test_lot.copy()
        lot['status'] = 'unsuccessful'
        bid = test_bid_valid.copy()
        bid['lotValues'] = [test_lot_values]
        data = {
            "procurementMethodType": p_type,
            "awardPeriod": test_award_period,
            "lots": [lot],
            "bids": [bid for _ in range(2)],
        }
        self.assertLen(2, data)

    def test_defense_one_bid_now_award(self):
        # (((count_lot_bids(lot, tender) < 2) && (lot_awards.length === 0))) == False
        bid = test_bid_valid.copy()
        bid['lotValues'] = [test_lot_values]
        data = {
            "procurementMethodType": "aboveThresholdUA.defense",
            "awardPeriod": test_award_period,
            "awards": [
               {
                   "status": "active",
                   "lotID": "324d7b2dd7a54df29bad6d0b7c91b2e9",
                   "bid_id": "a22ef2b1374b43ddb886821c0582bc7dk",
                   "date": "2016-11-13T15:15:00+02:00",
                   "id": "da6b3f912070460ca082b969a2f91e5d"
                }
            ],
            "lots": [test_lot],
            "bids": [bid],
        }
        self.assertLen(1, data)



@pytest.mark.usefixtures("db", "ut")
class TestEUProcedure(BaseBillingTest):

    def test_no_qualifications(self):
        data = {
            "procurementMethodType": "aboveThresholdEU",
            "awardPeriod": test_award_period,
            "qualificationPeriod": {
                "startDate": "2016-11-13T15:15:00+02:00"
            },
            'bids': [test_bid_valid for _ in range(3)],
        }
        self.assertLen(0, data)

    def test_no_qualification_period(self):
        data = {
            "procurementMethodType": "aboveThresholdEU",
            "qualifications": [test_eu_qualification_for_valid_bid,
                               test_eu_qualification_for_valid_bid],

            'bids': [test_bid_valid for _ in range(3)],
        }
        self.assertLen(0, data)

    def test_cancelled_before_pre_qualification(self):
        # (tender.date < (new Date( bids_disclojure_date ))) == True
        data = {
            "status": "cancelled",
            "procurementMethodType": "aboveThresholdEU",
            "cancellations":[{
                            "cancellationOf": "tender",
                            "date": "2016-11-13T15:10:00+02:00",
                            "status": "active"
                        }],
            "awardPeriod": test_award_period,
            "qualificationPeriod": test_award_period,
            "qualifications": [test_eu_qualification_for_valid_bid,
                               test_eu_qualification_for_valid_bid],
            'date': parse(test_award_period['startDate']).replace(day=1).isoformat(),
            "bids": [test_bid_valid for _ in range(2)],
        }
        self.assertLen(0, data)

    def test_view_check_tender_bids_EU_success(self):
        data = {
            "procurementMethodType": "aboveThresholdEU",
            "qualifications": [test_eu_qualification_for_valid_bid
                               for _ in range(2)],
            "awardPeriod": test_award_period,
            "qualificationPeriod": {
                "startDate": parse(test_award_period['startDate']).replace(day=1).isoformat()
            },
            'bids': [test_bid_valid for _ in range(2)],
        }
        self.assertLen(2, data)

    def test_EU_1_qualification(self):
        data = {
            "status": "unsuccessful",
            "procurementMethodType": "aboveThresholdEU",
            "qualifications": [test_eu_qualification_for_valid_bid],
            "awardPeriod": test_award_period,
            "qualificationPeriod":{
                "startDate": "2016-11-13T15:15:00+02:00"
            },
            "lots": [test_lot],
            "bids": [test_bid_valid for _ in range(5)],
        }
        self.assertLen(0, data)


@pytest.mark.skip
@pytest.mark.usefixtures("db", "ut")
class TestCDProcedure(BaseBillingTest):
    def test_stage2_skip(self):
        data = {
            "procurementMethodType": "competitiveDialogueEU.stage2",
            "awardPeriod": test_award_period,
            "qualificationPeriod": test_award_period,
            "qualifications": [test_eu_qualification_for_valid_bid
                               for _ in range(5)],
            "bids": [test_bid_valid for _ in range(5)],
        }
        self.assertLen(0, data)

    def test_check_bids_CD_EU(self):
        data = {
            "procurementMethodType": "competitiveDialogueEU",
            "qualifications": [test_eu_qualification_for_valid_bid in range(5)],
            "awardPeriod": test_award_period,
            "qualificationPeriod": test_award_period,
            'bids': [test_bid_valid for _ in range(5)],
        }
        self.assertLen(5, data)

    def test_view_check_tender_bids_CD_EU_two_qual(self):
        data = {
            "status": "cancelled",
            "procurementMethodType": "competitiveDialogueEU",
            "cancellations":[{
                            "cancellationOf": "tender",
                            "date": "2016-11-13T15:17:00+02:00",
                            "status": "active"
                        }],
            "qualifications": [{
                "bidID": "f55962b1374b43ddb886821c0582bc7f"
            },
                {
                    "bidID": "f55962b2374b83ddb886821c0582bc7f"
                }
            ],
            "awardPeriod": test_award_period,
            "qualificationPeriod": test_award_period,
            'bids': [test_bid_valid],
        }
        self.assertLen(0, data)

    def test_view_check_tender_unsuccesfull(self):
        data = {
            "status": "unsuccessful",
            "procurementMethodType": "competitiveDialogueEU",
            "qualifications": [{
                "bidID": "f55962b1374b43ddb886821c0582bc7f"
            },
            {
                "bidID": "f55962b2374b83ddb886821c0582bc7f"
            },
            {
                "bidID": "f55962b2374b83ddb886821c0582bc7e"
            }
            ],
            "awardPeriod": {
                "startDate": test_award_period,
            },
            "qualificationPeriod":{
                "startDate": "2016-11-13T15:15:00+02:00"
            },
            'bids': [test_bid_valid],
        }
        self.assertLen(1, data)

    def test_view_check_tender_unsuccesfull_invalid(self):
        data = {
            "status": "unsuccessful",
            "procurementMethodType": "competitiveDialogueEU",
            "cancellations":[{
                            "cancellationOf": "tender",
                            "date": "2016-11-13T15:17:00+02:00",
                            "status": "active"
                        }],
            "qualifications": [{
                "bidID": "f55962b1374b43ddb886821c0582bc7f"
            },
            {
                "bidID": "f55962b2374b83ddb886821c0582bc7e"
            }
            ],
            "awardPeriod": {
                "startDate": test_award_period,
            },
            "qualificationPeriod":{
                "startDate": "2016-11-13T15:15:00+02:00"
            },
            'bids': test_bid_valid,
        }
        self.assertLen(0, data)

    def test_view_check_lot_bids_unsuccessfull_EU(self):
        lot = test_lot.copy()
        lot['status'] = 'unsuccessful'
        data = {
            "procurementMethodType": "aboveThresholdEU",
            "qualifications": [test_eu_qualification_for_valid_bid for _ in range(2)],
            "awardPeriod": test_award_period,
            "qualificationPeriod":{
                "startDate": "2016-11-13T15:15:00+02:00"
            },
            "lots": [
                {
                    "status": "unsuccessful",
                    "id": "324d7b2dd7a54df29bad6d0b7c91b2e9",
                    "value": {
                        "currency": "UAH",
                        "amount": 2000,
                        "valueAddedTaxIncluded": False,
                    },
                }
            ],
            "bids": [test_bid_valid for _ in range(2)],
        }
        self.assertLen(2, data)

    def test_view_check_lot_bids_unsuccessfull_competitiveDialogueEU(self):
        data = {
            "status": "unsuccessful",
            "procurementMethodType": "competitiveDialogueEU",
            "qualifications": [{
                "bidID": "a22ef2b1374b43ddb886821c0582bc7dk",
                "lotID": "324d7b2dd7a54df29bad6d0b7c91b2e9"
                },
                {
                "bidID": "a22ef2b1374b43ddb886821c0582bc7dj",
                "lotID": "324d7b2dd7a54df29bad6d0b7c91b2e9"
                },
                {
                "bidID": "a22ef2b1374b43ddb886821c0582bc7dj",
                "lotID": "324d7b2dd7a54df29bad6d0b7c91b2e9"
            }],
            "awardPeriod": {
                "startDate": "2016-11-13T15:15:00+02:00",
            },
            "qualificationPeriod":{
                "startDate": "2016-11-13T15:15:00+02:00"
            },
            "lots": [
                {
                    "status": "unsuccessful",
                    "id": "324d7b2dd7a54df29bad6d0b7c91b2e9",
                    "value": {
                        "currency": "UAH",
                        "amount": 2000,
                        "valueAddedTaxIncluded": False,
                    },
                }
            ],
            "bids": [test_bid_valid for _ in range(2)],
        }
        self.assertLen(1, data)

    def test_view_check_lot_bids_unsuccessfull_competitiveDialogueEU_fail_with_2_qualifications(self):
        data = {
            "status": "unsuccessful",
            "procurementMethodType": "competitiveDialogueEU",
            "qualifications": [{
                "bidID": "a22ef2b1374b43ddb886821c0582bc7dk",
                "lotID": "324d7b2dd7a54df29bad6d0b7c91b2e9"
            },
                {
                    "bidID": "a22ef2b1374b43ddb886821c0582bc7dj",
                    "lotID": "324d7b2dd7a54df29bad6d0b7c91b2e9"
                }
            ],
            "awardPeriod": {
                "startDate": "2016-11-13T15:15:00+02:00",
            },
            "qualificationPeriod":{
                "startDate": "2016-11-13T15:15:00+02:00"
            },
            "lots": [
                {
                    "status": "unsuccessful",
                    "id": "324d7b2dd7a54df29bad6d0b7c91b2e9",
                    "value": {
                        "currency": "UAH",
                        "amount": 2000,
                        "valueAddedTaxIncluded": False,
                    },
                }
            ],
            "bids": [test_bid_valid for _ in range(2)],
        }
        self.assertLen(0, data)
