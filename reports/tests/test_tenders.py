import pytest
import couchdb
import mock
import os.path
from reports.config import Config
from reports.utilities.tenders import TendersUtility
from copy import copy
from reports.tests.utils import(
    get_mock_parser,
    test_data,
    assert_csv,
    db,
    assertLen
)
test_lots = [
                {
                    "status": "active",
                    "date": "2016-04-07T16:36:58.983102+03:00",
                    "id": "324d7b2dd7a54df29bad6d0b7c91b2e9",
                    "value": {
                        "currency": "UAH",
                        "amount": 2000,
                        "valueAddedTaxIncluded": "False",
                    },
                },
            ]

test_bids = [{
                "date": "2016-04-07T16:36:58.983102+03:00",
                
                "status": "active",
                "id": "a22ef2b1374b43ddb886821c0582bc7dk",
                "lotValues": [
                    {
                        "relatedLot": "324d7b2dd7a54df29bad6d0b7c91b2e9",
                        "date": "2016-04-07T16:36:58.983062+03:00",
                    }
                ],
            }]

test_contracts = [
            {
                "status": "active",
                 "awardID": "3d5182c5a0424a4f8508da712affa82f",
                "id": "1ac8c648538d4930918b0b0a1e884ef2",
                "date": '2016-04-22T13:32:25.774673+02:00',
                "dateSigned": '2016-05-22T13:32:25.774673+02:00',
                "documents": [{
                    'datePublished': "2016-06-22T13:32:25.774673+02:00",
                },]
            }
        ]

test_contracts_2 =  [
            {
                "status": "active",
                "awardID": "da6b3f912070460ca082b969a2f91e5d",
                "id": "1ac8c648538d4930918b0b0a1e884ef2",
                "date": '2016-04-22T13:32:25.774673+02:00',
                "dateSigned": '2016-05-22T13:32:25.774673+02:00',
                "documents": [{
                    'datePublished': "2016-06-22T13:32:25.774673+02:00",
                },]
            }
        ]

test_awards = [
               {
                   "complaintPeriod": {
                       "startDate": "2016-06-01T12:16:40.832321+03:00",
                       "endDate": "2016-06-14T18:31:52.162261+03:00"
                   },
                   "status": "active",
                   "lotID": "324d7b2dd7a54df29bad6d0b7c91b2e9",
                   "bid_id": "a22ef2b1374b43ddb886821c0582bc7dk",
                   "value": {
                       "currency": "UAH",
                       "amount": 2000,
                       "valueAddedTaxIncluded": "True"
                   },
                   "date": "2016-11-13T15:15:00+02:00",
                   "id": "da6b3f912070460ca082b969a2f91e5d"
                }
            ]

test_award_period = '2016-04-17T13:32:25.774673+02:00'



@pytest.fixture(scope='function')
def ut(request):    
    mock_parse = get_mock_parser()
    type(mock_parse.return_value).kind = mock.PropertyMock(
        return_value=['general'])
    with mock.patch('argparse.ArgumentParser.parse_args', mock_parse):
        utility = TendersUtility()
    return utility

def test_tenders_view_invalid_date(db, ut):
    data = {
        "enquiryPeriod": {
            "startDate": '2016-03-17T13:32:25.774673+02:00',
        },
        'owner': 'test',
        
        "contracts": [
            {
                "status": "active",
            }],
    }
    assertLen(0, data, ut)

def test_tenders_view_invalid_method(db, ut):
    data = {
        "procurementMethod": "test",
        "enquiryPeriod": {
            "startDate": '2016-04-17T13:32:25.774673+02:00',
        },
        'owner': 'test',
        "contracts": [
            {
                "status": "active",
            }],
    }
    assertLen(0, data, ut)

def test_tenders_view_invalid_mode(db, ut):
    data = {
        "mode": "test",        
        "enquiryPeriod": {
            "startDate": '2016-04-17T13:32:25.774673+02:00',
        },
        'owner': 'test',
        "contracts": [
            {
                "status": "active",
            }],
    }
    assertLen(0, data, ut)

def test_tenders_view_invalid_status(db, ut):
    data = {        
        "enquiryPeriod": {
            "startDate": '2016-04-17T13:32:25.774673+02:00',
        },
        'awardPeriod': {'startDate': '2016-04-22T13:32:25.774673+02:00'},
        "contracts": [{
            "status": "unsuccessful",
        }],
    }
    assertLen(0, data, ut)

# start new tests

def test_bids_view_invalid_doc_type(db, ut):
    data = {
        "doc_type": "new Tender",
        "awardPeriod": {
            "startDate": test_award_period,
        },
        'owner': 'teser',
    }
    assertLen(0, data, ut)

def test_tenders_view_comp_dialog_active(db, ut):
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
         
    assertLen(0, data, ut)

def test_tenders_view_check_lot_fail(db, ut):
    # (count_lot_bids(lot, bids) > 1) == False
    data = {        
        "status": "active",    
        "procurementMethodType": "aboveThresholdUA",
        "date": '2016-04-22T13:32:25.774673+02:00',        
        'numberOfBids': 2,
        'awardPeriod': {'startDate': '2016-04-22T13:32:25.774673+02:00'},
        "enquiryPeriod": {
            "startDate": '2016-04-17T13:32:25.774673+02:00',
        },
        "contracts": test_contracts,        
        "tenderPeriod": {
            "startDate": "2016-11-13T15:15:00+02:00",
        },
        "lots": test_lots,
        "bids": test_bids,
    }
    assertLen(0, data, ut)

def test_tenders_view_check_lot_fail_with_1_qualif(db, ut):
    # if (count_lot_qualifications((tender.qualifications || []), lot.id) > 1) == False
    data = {        
        "status": "active",    
        "procurementMethodType": "aboveThresholdEU",
        "date": '2016-04-22T13:32:25.774673+02:00',        
        'numberOfBids': 2,
        'awardPeriod': {'startDate': '2016-04-22T13:32:25.774673+02:00'},
        "enquiryPeriod": {
            "startDate": '2016-04-17T13:32:25.774673+02:00',
        },
        "qualifications": [{
            "lotID": "324d7b2dd7a54df29bad6d0b7c91b2e9"
        }],        
        "qualificationPeriod":{
            "startDate": "2016-11-13T15:15:00+02:00"
        },
        "contracts": test_contracts,        
        "tenderPeriod": {
            "startDate": "2016-11-13T15:15:00+02:00",
        },
        "lots": test_lots,
        "bids": test_bids,
    }
    assertLen(0, data, ut)

def test_tenders_view_check_lot_2_qualif(db, ut):
    # if (count_lot_qualifications((tender.qualifications || []), lot.id) > 1) == True
    data = {        
        "status": "active",    
        "procurementMethodType": "aboveThresholdEU",
        "date": '2016-04-22T13:32:25.774673+02:00',        
        'numberOfBids': 2,
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
        "lots": [
                {
                    "status": "complete",
                    "date": "2016-04-07T16:36:58.983102+03:00",
                    "id": "324d7b2dd7a54df29bad6d0b7c91b2e9",
                    "value": {
                        "currency": "UAH",
                        "amount": 2000,
                        "valueAddedTaxIncluded": "False",
                    },
                },
            ],    
        "bids": test_bids,
    }
    assertLen(1, data, ut)

def test_tenders_view_check_lot_fail_UA_def(db, ut):
    # (((count_lot_bids(lot, bids) < 2 ) && (lot_awards.length === 0))) == True
    data = {        
        "status": "active",    
        "procurementMethodType": "aboveThresholdUA.defense",
        "date": '2016-04-22T13:32:25.774673+02:00',        
        'numberOfBids': 2,
        'awardPeriod': {'startDate': '2016-04-22T13:32:25.774673+02:00'},
        "enquiryPeriod": {
            "startDate": '2016-04-17T13:32:25.774673+02:00',
        },
        "contracts": test_contracts,        
        "tenderPeriod": {
            "startDate": "2016-11-13T15:15:00+02:00",
        },
        "lots": test_lots,
        "bids": test_bids,
    }
    assertLen(0, data, ut)

def test_tenders_view_check_lot_UA_def_with_award(db, ut):
    # (((count_lot_bids(lot, bids) < 2 ) && (lot_awards.length === 0))) == False
    # if (count_lot_bids(lot, bids) > 0)  == True
    data = {        
        "status": "complete",    
        "procurementMethodType": "aboveThresholdUA.defense",
        "date": '2016-04-22T13:32:25.774673+02:00',        
        'numberOfBids': 2,
        'awardPeriod': {'startDate': '2016-04-22T13:32:25.774673+02:00'},
        "awards": [
               {
                   "status": "active",
                   "lotID": "324d7b2dd7a54df29bad6d0b7c91b2e9",
                   "bid_id": "a22ef2b1374b43ddb886821c0582bc7dk",
                   "value": {
                       "currency": "UAH",
                       "amount": 2000,
                       "valueAddedTaxIncluded": "True"
                   },
                   "date": "2016-11-13T15:15:00+02:00",
                   "id": "da6b3f912070460ca082b969a2f91e5d"
                }
            ],
        "enquiryPeriod": {
            "startDate": '2016-04-17T13:32:25.774673+02:00',
        },
        "contracts": test_contracts,        
        "tenderPeriod": {
            "startDate": "2016-11-13T15:15:00+02:00",
        },        
        "bids": test_bids,
    }
    assertLen(1, data, ut)

def test_tenders_view_check_lot_default(db, ut):
    # default  
    # if (count_lot_bids(lot, bids) > 0) == True
    data = {        
        "status": "complete",    
        "procurementMethodType": "belowThreshold",
        "date": '2016-04-22T13:32:25.774673+02:00',        
        'numberOfBids': 2,
        'awardPeriod': {'startDate': '2016-04-22T13:32:25.774673+02:00'},
        "enquiryPeriod": {
            "startDate": '2016-04-17T13:32:25.774673+02:00',
        },
        "contracts": test_contracts,        
        "tenderPeriod": {
            "startDate": "2016-11-13T15:15:00+02:00",
        },
        "lots": [
                {
                    "status": "complete",
                    "date": "2016-04-07T16:36:58.983102+03:00",
                    "id": "324d7b2dd7a54df29bad6d0b7c91b2e9",
                    "value": {
                        "currency": "UAH",
                        "amount": 2000,
                        "valueAddedTaxIncluded": "False",
                    },
                },
            ],        
        "bids": test_bids,
    }
    assertLen(1, data, ut)

def test_tenders_view_check_lot_default_fail(db, ut):
    # default  
    # if (count_lot_bids(lot, bids) > 0) == False
    data = {        
        "status": "complete",    
        "procurementMethodType": "belowThreshold",
        "date": '2016-04-22T13:32:25.774673+02:00',        
        'numberOfBids': 2,
        'awardPeriod': {'startDate': '2016-04-22T13:32:25.774673+02:00'},
        "enquiryPeriod": {
            "startDate": '2016-04-17T13:32:25.774673+02:00',
        },
        "contracts": test_contracts,        
        "tenderPeriod": {
            "startDate": "2016-11-13T15:15:00+02:00",
        },
        "lots": [
                {
                    "status": "complete",
                    "date": "2016-04-07T16:36:58.983102+03:00",
                    "id": "324d7b2dd7a54df29bad6d0b7c91b2e9",
                    "value": {
                        "currency": "UAH",
                        "amount": 2000,
                        "valueAddedTaxIncluded": "False",
                    },
                },
            ],
    }
    assertLen(0, data, ut)
       
def test_tenders_view_check_tender_default_fail_by_date(db, ut):
    # if (handler.tender_date < handler.bids_disclosure_standstill) == True { return; }
    data = {        
        "status": "cancelled",    
        "procurementMethodType": "belowThreshold",
        "date": '2016-04-12T13:32:25.774673+02:00',        
        'numberOfBids': 2,
        'awardPeriod': {'startDate': '2016-04-22T13:32:25.774673+02:00'},
        "enquiryPeriod": {
            "startDate": '2016-04-17T13:32:25.774673+02:00',
        },
        "contracts": test_contracts,        
        "tenderPeriod": {
            "startDate": "2016-11-13T15:15:00+02:00",
        },
        "bids": test_bids,
    }
    assertLen(0, data, ut)

def test_tenders_view_check_tender_default_fail_by_numberOfBids(db, ut):
    # if (tender.numberOfBids > 0) == False
    data = {        
        "status": "cancelled",    
        "procurementMethodType": "belowThreshold",
        "date": '2016-04-12T13:32:25.774673+02:00',        
        'numberOfBids': 0,
        'awardPeriod': {'startDate': '2016-04-22T13:32:25.774673+02:00'},
        "enquiryPeriod": {
            "startDate": '2016-04-17T13:32:25.774673+02:00',
        },
        "contracts": test_contracts,        
        "tenderPeriod": {
            "startDate": "2016-11-13T15:15:00+02:00",
        },
        "bids": test_bids,
    }
    assertLen(0, data, ut)

def test_tenders_view_check_tender_default(db, ut):
    # default  
    # if (count_lot_bids(lot, bids) > 0) == True
    data = {        
        "status": "complete",    
        "procurementMethodType": "belowThreshold",
        "date": '2016-04-22T13:32:25.774673+02:00',        
        'numberOfBids': 2,
        'awardPeriod': {'startDate': '2016-04-22T13:32:25.774673+02:00'},
        "enquiryPeriod": {
            "startDate": '2016-04-17T13:32:25.774673+02:00',
        },
        "contracts": test_contracts,        
        "tenderPeriod": {
            "startDate": "2016-11-13T15:15:00+02:00",
        },
        "bids": test_bids,
    }
    assertLen(1, data, ut)

def test_tenders_view_check_tender_UA_pass(db, ut):
    #  if (tender.numberOfBids > 1) == True
    data = {        
        "status": "cancelled",    
        "procurementMethodType": "aboveThresholdUA",
        "date": '2016-04-22T13:32:25.774673+02:00',        
        'numberOfBids': 2,
        'awardPeriod': {'startDate': '2016-04-22T13:32:25.774673+02:00'},
        "enquiryPeriod": {
            "startDate": '2016-04-17T13:32:25.774673+02:00',
        },
        "contracts": test_contracts,        
        "tenderPeriod": {
            "startDate": "2016-11-13T15:15:00+02:00",
        },
        "bids": test_bids,
    }
    assertLen(1, data, ut)

def test_tenders_view_check_tender_UA_fail(db, ut):
    #  if (tender.numberOfBids > 1) == False
    data = {        
        "status": "cancelled",    
        "procurementMethodType": "aboveThresholdUA",
        "date": '2016-04-22T13:32:25.774673+02:00',        
        'numberOfBids': 1,
        'awardPeriod': {'startDate': '2016-04-22T13:32:25.774673+02:00'},
        "enquiryPeriod": {
            "startDate": '2016-04-17T13:32:25.774673+02:00',
        },
        "contracts": test_contracts,        
        "tenderPeriod": {
            "startDate": "2016-11-13T15:15:00+02:00",
        },
        "bids": test_bids,
    }
    assertLen(0, data, ut)

def test_tenders_view_check_tender_EU_2qual_pass(db, ut):
    #  (((tender.qualifications || []).length) > 1) == True
    data = {        
        "status": "cancelled",    
        "procurementMethodType": "aboveThresholdEU",
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
    assertLen(1, data, ut)

def test_tenders_view_check_tender_EU_1qual_fail(db, ut):
    #  (((tender.qualifications || []).length) > 1) == False
    data = {        
        "status": "cancelled",    
        "procurementMethodType": "aboveThresholdEU",
        "date": '2016-04-22T13:32:25.774673+02:00',        
        'numberOfBids': 1,
        'awardPeriod': {'startDate': '2016-04-22T13:32:25.774673+02:00'},
        "enquiryPeriod": {
            "startDate": '2016-04-17T13:32:25.774673+02:00',
        },
        "qualifications": [{
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

def test_tenders_view_check_tender_DEF_pass_numberOfBids(db, ut):
    #   (tender.numberOfBids < 2) && !('awards' in tender)) == False
    data = {        
        "status": "cancelled",    
        "procurementMethodType": "aboveThresholdUA.defense",
        "date": '2016-04-22T13:32:25.774673+02:00',        
        'numberOfBids': 2,
        'awardPeriod': {'startDate': '2016-04-22T13:32:25.774673+02:00'},
        "enquiryPeriod": {
            "startDate": '2016-04-17T13:32:25.774673+02:00',
        },
        "contracts": test_contracts,        
        "tenderPeriod": {
            "startDate": "2016-11-13T15:15:00+02:00",
        },
        "bids": test_bids,
    }
    assertLen(1, data, ut)

def test_tenders_view_check_tender_DEF_pass_awards(db, ut):
    #   (tender.numberOfBids < 2) && !('awards' in tender)) == False
    data = {        
        "status": "cancelled",    
        "procurementMethodType": "aboveThresholdUA.defense",
        "date": '2016-04-22T13:32:25.774673+02:00',        
        'numberOfBids': 1,
        'awardPeriod': {'startDate': '2016-04-22T13:32:25.774673+02:00'},
        "enquiryPeriod": {
            "startDate": '2016-04-17T13:32:25.774673+02:00',
        },
        "awards": [
           {
               "status": "active",
               "lotID": "324d7b2dd7a54df29bad6d0b7c91b2e9",
               "bid_id": "a22ef2b1374b43ddb886821c0582bc7dk",
               "value": {
                   "currency": "UAH",
                   "amount": 2000,
                   "valueAddedTaxIncluded": True
               },
               "date": "2016-11-13T15:15:00+02:00",
               "id": "da6b3f912070460ca082b969a2f91e5d"
            }
        ],
        "contracts": test_contracts,        
        "tenderPeriod": {
            "startDate": "2016-11-13T15:15:00+02:00",
        },
        "bids": test_bids,
    }
    assertLen(1, data, ut)

def test_tenders_view_check_tender_DEF_fail(db, ut):
    #   (tender.numberOfBids < 2) && !('awards' in tender)) == True
    data = {        
        "status": "cancelled",    
        "procurementMethodType": "aboveThresholdUA.defense",
        "date": '2016-04-22T13:32:25.774673+02:00',        
        'numberOfBids': 1,
        'awardPeriod': {'startDate': '2016-04-22T13:32:25.774673+02:00'},
        "enquiryPeriod": {
            "startDate": '2016-04-17T13:32:25.774673+02:00',
        },
        "contracts": test_contracts,        
        "tenderPeriod": {
            "startDate": "2016-11-13T15:15:00+02:00",
        },
        "bids": test_bids,
    }
    assertLen(0, data, ut)

def test_tenders_view_check_tender_DIALOG_pass(db, ut):
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

def test_tenders_view_check_tender_DIALOG_fail(db, ut):
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

# Handler tests 

def test_tenders_view_check_handler_cancelled_default_fail_date(db, ut):
    # if ((new Date(tender.date)) < this.bids_disclosure_standstill) == True
    # this.tender_date = null;
    data = {        
        "status": "cancelled",    
        "procurementMethodType": "belowThreshold",
        "date": '2016-04-22T13:32:25.774673+02:00',        
        'numberOfBids': 2,
        'awardPeriod': {'startDate': '2016-12-12T13:32:25.774673+02:00'},
        "enquiryPeriod": {
            "startDate": '2016-04-17T13:32:25.774673+02:00',
        },
        "contracts": test_contracts,        
        "tenderPeriod": {
            "startDate": "2016-11-13T15:15:00+02:00",
        },
        "bids": test_bids,
    }
    assertLen(0, data, ut)

def test_tenders_view_check_handler_cancelled_default_pass(db, ut):
    # if ((new Date(tender.date)) < this.bids_disclosure_standstill) == False
    data = {        
        "status": "cancelled",    
        "procurementMethodType": "belowThreshold",
        "date": '2016-04-22T13:32:25.774673+02:00',        
        'numberOfBids': 2,
        'awardPeriod': {'startDate': '2016-04-12T13:32:25.774673+02:00'},
        "enquiryPeriod": {
            "startDate": '2016-04-17T13:32:25.774673+02:00',
        },
        "contracts": test_contracts,        
        "tenderPeriod": {
            "startDate": "2016-11-13T15:15:00+02:00",
        },
        "bids": test_bids,
    }
    assertLen(1, data, ut)

def test_tenders_view_check_handler_active_default_fail(db, ut):
    # if date in tender == True
    # this.tender_date = null
    data = {        
        "status": "active",    
        "procurementMethodType": "belowThreshold",
        "date": '2016-04-22T13:32:25.774673+02:00',        
        'numberOfBids': 2,
        'awardPeriod': {'startDate': '2016-04-12T13:32:25.774673+02:00'},
        "enquiryPeriod": {
            "startDate": '2016-04-17T13:32:25.774673+02:00',
        },
        "contracts": test_contracts,        
        "tenderPeriod": {
            "startDate": "2016-11-13T15:15:00+02:00",
        },
        "bids": test_bids,
    }
    assertLen(0, data, ut)

def test_tenders_view_check_handler_active_default_without_date_fail(db, ut):
    # if date in tender == False
    # this.tender_date = null
    data = {        
        "status": "active",    
        "procurementMethodType": "belowThreshold",
        'numberOfBids': 2,
        'awardPeriod': {'startDate': '2016-04-12T13:32:25.774673+02:00'},
        "enquiryPeriod": {
            "startDate": '2016-04-17T13:32:25.774673+02:00',
        },
        "contracts": test_contracts,        
        "tenderPeriod": {
            "startDate": "2016-11-13T15:15:00+02:00",
        },
        "bids": test_bids,
    }
    assertLen(0, data, ut)

def test_tenders_view_check_handler_complete_default_contracts_date_pass(db, ut):
    # if date in tender == False
    #  this.tender_date = return max_date(c);
    # max_date function check
    data = {        
        "status": "complete",    
        "procurementMethodType": "belowThreshold",
        'numberOfBids': 2,
        'awardPeriod': {'startDate': '2016-04-12T13:32:25.774673+02:00'},
        "enquiryPeriod": {
            "startDate": '2016-04-17T13:32:25.774673+02:00',
        },
        "contracts": test_contracts,        
        "tenderPeriod": {
            "startDate": "2016-11-13T15:15:00+02:00",
        },
        "bids": test_bids,
    }
    assertLen(1, data, ut)

def test_tenders_view_check_handler_complete_default_without_contracts_date_fail(db, ut):
    # if date in tender == False
    #  this.tender_date = return max_date(c); == Invalid Date
    # max_date function check
    data = {        
        "status": "complete",    
        "procurementMethodType": "belowThreshold",
        'numberOfBids': 2,
        'awardPeriod': {'startDate': '2016-04-12T13:32:25.774673+02:00'},
        "enquiryPeriod": {
            "startDate": '2016-04-17T13:32:25.774673+02:00',
        },        
        "tenderPeriod": {
            "startDate": "2016-11-13T15:15:00+02:00",
        },
        "bids": test_bids,
    }
    assertLen(0, data, ut)

def test_tenders_view_check_handler_unsuccesful_award_complaintPeriod_pass(db, ut):
    # if date in tender == False
    #  this.tender_date = find_awards_max_date(tender.awards);
    # find_awards_max_date function check
    data = {        
        "status": "unsuccessful",    
        "procurementMethodType": "belowThreshold",
        'numberOfBids': 2,
        'awardPeriod': {'startDate': '2016-04-12T13:32:25.774673+02:00'},
        "enquiryPeriod": {
            "startDate": '2016-04-17T13:32:25.774673+02:00',
        },
        "awards": test_awards,
        "contracts": test_contracts,        
        "tenderPeriod": {
            "startDate": "2016-11-13T15:15:00+02:00",
        },
        "bids": test_bids,
    }
    assertLen(1, data, ut)

def test_tenders_view_check_handler_unsuccesful_award_without_complaintPeriod_fail(db, ut):
    # if date in tender == False
    #  this.tender_date = find_awards_max_date(tender.awards);
    # find_awards_max_date function check
    data = {        
        "status": "unsuccessful",    
        "procurementMethodType": "belowThreshold",
        'numberOfBids': 2,
        'awardPeriod': {'startDate': '2016-04-12T13:32:25.774673+02:00'},
        "enquiryPeriod": {
            "startDate": '2016-04-17T13:32:25.774673+02:00',
        },
        "awards": [
               {
                   "status": "active",
                   "lotID": "324d7b2dd7a54df29bad6d0b7c91b2e9",
                   "bid_id": "a22ef2b1374b43ddb886821c0582bc7dk",
                   "value": {
                       "currency": "UAH",
                       "amount": 2000,
                       "valueAddedTaxIncluded": "True"
                   },
                   "date": "2016-11-13T15:15:00+02:00",
                   "id": "da6b3f912070460ca082b969a2f91e5d"
                }
            ],
        "contracts": test_contracts,        
        "tenderPeriod": {
            "startDate": "2016-11-13T15:15:00+02:00",
        },
        "bids": test_bids,
    }
    assertLen(0, data, ut)

def test_tenders_view_check_handler_cancelled_fail(db, ut):
    # if date in tender == False
    # (cancellation_date < this.bids_disclosure_standstill) == False
    # find_cancellation_max_date function check
    data = {        
        "status": "cancelled",    
        "procurementMethodType": "belowThreshold",
        'numberOfBids': 2,
        'awardPeriod': {'startDate': '2016-12-12T13:32:25.774673+02:00'},
        "enquiryPeriod": {
            "startDate": '2016-04-17T13:32:25.774673+02:00',
        },
        "cancellations":[{
                        "cancellationOf": "tender",
                        "date": "2016-11-13T15:10:00+02:00",
                        "status": "active"
                    },{
                        "cancellationOf": "tender",
                        "date": "2016-11-13T15:10:00+02:00",
                        "status": "active"
                    }],
        "contracts": test_contracts,        
        "tenderPeriod": {
            "startDate": "2016-11-13T15:15:00+02:00",
        },
        "bids": test_bids,
    }
    assertLen(0, data, ut)

# LotHandler check

def test_tenders_view_check_lothandler_cancelled_default_date_pass(db, ut):
    # if date in lot == True
    #   ((new Date(lot.date)) < this.tender_handler.bids_disclosure_standstill) ==False
    data = {        
        "status": "complete",    
        "procurementMethodType": "belowThreshold",
        'numberOfBids': 2,
        'awardPeriod': {'startDate': '2016-04-12T13:32:25.774673+02:00'},
        "enquiryPeriod": {
            "startDate": '2016-04-17T13:32:25.774673+02:00',
        },
        "contracts": test_contracts,        
        "tenderPeriod": {
            "startDate": "2016-11-13T15:15:00+02:00",
        },
        "lots": [
            {
                "status": "cancelled",
                "date": "2016-04-25T16:36:58.983102+03:00",
                "id": "324d7b2dd7a54df29bad6d0b7c91b2e9",
                "value": {
                    "currency": "UAH",
                    "amount": 2000,
                    "valueAddedTaxIncluded": False,
                },
            }
        ],
        "bids": test_bids,
    }
    assertLen(1, data, ut)

def test_tenders_view_check_lothandler_cancelled_default_date_fail(db, ut):
    # if date in lot == True
    #   ((new Date(lot.date)) < this.tender_handler.bids_disclosure_standstill) == True
    data = {        
        "status": "complete",    
        "procurementMethodType": "belowThreshold",
        'numberOfBids': 2,
        'awardPeriod': {'startDate': '2016-04-12T13:32:25.774673+02:00'},
        "enquiryPeriod": {
            "startDate": '2016-04-17T13:32:25.774673+02:00',
        },
        "contracts": test_contracts,        
        "tenderPeriod": {
            "startDate": "2016-11-13T15:15:00+02:00",
        },
        "lots": [
            {
                "status": "cancelled",
                "date": "2016-04-07T16:36:58.983102+03:00",
                "id": "324d7b2dd7a54df29bad6d0b7c91b2e9",
                "value": {
                    "currency": "UAH",
                    "amount": 2000,
                    "valueAddedTaxIncluded": False,
                },
            }
        ],
        "bids": test_bids,
    }
    assertLen(0, data, ut)

def test_tenders_view_check_lothandler_unsuccesful_default_with_date_pass(db, ut):
    # if date in lot == True
    # (this.status === 'cancelled') == False
    data = {        
        "status": "complete",    
        "procurementMethodType": "belowThreshold",
        'numberOfBids': 2,
        'awardPeriod': {'startDate': '2016-04-12T13:32:25.774673+02:00'},
        "enquiryPeriod": {
            "startDate": '2016-04-17T13:32:25.774673+02:00',
        },
        "contracts": test_contracts,        
        "tenderPeriod": {
            "startDate": "2016-11-13T15:15:00+02:00",
        },
        "lots": [
            {
                "status": "unsuccessful",
                "date": "2016-04-07T16:36:58.983102+03:00",
                "id": "324d7b2dd7a54df29bad6d0b7c91b2e9",
                "value": {
                    "currency": "UAH",
                    "amount": 2000,
                    "valueAddedTaxIncluded": "False",
                },
            }
        ],
        "bids": test_bids,
    }
    assertLen(1, data, ut)

def test_tenders_view_check_lothandler_unsuccesful_default_without_date_pass(db, ut):
    # if date in lot == False
    # (award.lotID === lot.id) == True                
    data = {        
        "status": "complete",    
        "procurementMethodType": "belowThreshold",
        'numberOfBids': 2,
        'awardPeriod': {'startDate': '2016-04-12T13:32:25.774673+02:00'},
        "enquiryPeriod": {
            "startDate": '2016-04-17T13:32:25.774673+02:00',
        },
        "awards": [
               {    "complaintPeriod": {
                       "startDate": "2016-06-01T12:16:40.832321+03:00",
                       "endDate": "2016-06-14T18:31:52.162261+03:00"
                    },
                    "status": "active",
                    "lotID": "324d7b2dd7a54df29bad6d0b7c91b2e9",
                    "bid_id": "a22ef2b1374b43ddb886821c0582bc7dk",
                    "value": {
                        "currency": "UAH",
                        "amount": 2000,
                        "valueAddedTaxIncluded": "True"
                    },
                    "date": "2016-11-13T15:15:00+02:00",
                    "id": "da6b3f912070460ca082b969a2f91e5d"
                }
            ],
        "contracts": test_contracts,        
        "tenderPeriod": {
            "startDate": "2016-11-13T15:15:00+02:00",
        },
        "lots": [
            {
                "status": "unsuccessful",
                "id": "324d7b2dd7a54df29bad6d0b7c91b2e9",
                "value": {
                    "currency": "UAH",
                    "amount": 2000,
                    "valueAddedTaxIncluded": "False",
                },
            }
        ],
        "bids": test_bids,
    }
    assertLen(1, data, ut)

def test_tenders_view_check_lothandler_unsuccesful_default_fail(db, ut):
    # if date in lot == False
    # (award.lotID === lot.id) == False              
    data = {        
        "status": "complete",    
        "procurementMethodType": "belowThreshold",
        'numberOfBids': 2,
        'awardPeriod': {'startDate': '2016-04-12T13:32:25.774673+02:00'},
        "enquiryPeriod": {
            "startDate": '2016-04-17T13:32:25.774673+02:00',
        },
        "awards": [
               {    "complaintPeriod": {
                       "startDate": "2016-06-01T12:16:40.832321+03:00",
                       "endDate": "2016-06-14T18:31:52.162261+03:00"
                    },
                    "status": "active",
                    "lotID": "324d7b2dd7a54df29bad6d0b7c91b2e8",
                    "bid_id": "a22ef2b1374b43ddb886821c0582bc7dk",
                    "value": {
                        "currency": "UAH",
                        "amount": 2000,
                        "valueAddedTaxIncluded": "True"
                    },
                    "date": "2016-11-13T15:15:00+02:00",
                    "id": "da6b3f912070460ca082b969a2f91e5d"
                }
            ],
        "contracts": test_contracts,        
        "tenderPeriod": {
            "startDate": "2016-11-13T15:15:00+02:00",
        },
        "lots": [
            {
                "status": "unsuccessful",
                "id": "324d7b2dd7a54df29bad6d0b7c91b2e9",
                "value": {
                    "currency": "UAH",
                    "amount": 2000,
                    "valueAddedTaxIncluded": "False",
                },
            }
        ],
        "bids": test_bids,
    }
    assertLen(0, data, ut)

def test_tenders_view_check_lothandler_lot_cancelled_default_date_fail(db, ut):
    # if date in lot == False
    # ((cancellation.status === 'active') && (cancellation.cancellationOf === 'lot') && (cancellation.relatedLot === lot.id)) == True                
    # ((lot_cancellation !== null) && (lot_cancellation > this.tender_handler.bids_disclosure_standstill)) == False             
    data = {        
        "status": "complete",    
        "procurementMethodType": "belowThreshold",
        'numberOfBids': 2,
        'awardPeriod': {'startDate': '2016-12-12T13:32:25.774673+02:00'},
        "enquiryPeriod": {
            "startDate": '2016-04-17T13:32:25.774673+02:00',
        },
        "cancellations":[{
                        "cancellationOf": "lot",
                        "date": "2016-11-13T15:10:00+02:00",
                        "relatedLot": "324d7b2dd7a54df29bad6d0b7c91b2e9",
                        "status": "active"
                    },{
                        "cancellationOf": "lot",
                        "relatedLot": "324d7b2dd7a54df29bad6d0b7c91b2e9",
                        "date": "2016-11-13T15:10:00+02:00",
                        "status": "active"
                    }],
        "contracts": test_contracts,        
        "tenderPeriod": {
            "startDate": "2016-11-13T15:15:00+02:00",
        },
        "lots": [
            {
                "status": "cancelled",
                "id": "324d7b2dd7a54df29bad6d0b7c91b2e9",
                "value": {
                    "currency": "UAH",
                    "amount": 2000,
                    "valueAddedTaxIncluded": "False",
                },
            }
        ],
        "bids": test_bids,
    }
    assertLen(0, data, ut)

def test_tenders_view_check_lothandler_lot_cancelled_default_correct_date_fail(db, ut):
    # if date in lot == False
    # (cancellation.status === 'active') == False
    # ((cancellation.status === 'active') && (cancellation.cancellationOf === 'lot') && (cancellation.relatedLot === lot.id)) == False               
    # ((lot_cancellation !== null) && (lot_cancellation > this.tender_handler.bids_disclosure_standstill)) == False             
    data = {        
        "status": "complete",    
        "procurementMethodType": "belowThreshold",
        'numberOfBids': 2,
        'awardPeriod': {'startDate': '2016-04-12T13:32:25.774673+02:00'},
        "enquiryPeriod": {
            "startDate": '2016-04-17T13:32:25.774673+02:00',
        },
        "cancellations":[{
                        "cancellationOf": "lot",
                        "date": "2016-11-13T15:10:00+02:00",
                        "relatedLot": "324d7b2dd7a54df29bad6d0b7c91b2e9",
                        "status": "complete"
                    },{
                        "cancellationOf": "lot",
                        "relatedLot": "324d7b2dd7a54df29bad6d0b7c91b2e9",
                        "date": "2016-11-13T15:10:00+02:00",
                        "status": "complete"
                    }],
        "contracts": test_contracts,        
        "tenderPeriod": {
            "startDate": "2016-11-13T15:15:00+02:00",
        },
        "lots": [
            {
                "status": "cancelled",
                "id": "324d7b2dd7a54df29bad6d0b7c91b2e9",
                "value": {
                    "currency": "UAH",
                    "amount": 2000,
                    "valueAddedTaxIncluded": "False",
                },
            }
        ],
        "bids": test_bids,
    }
    assertLen(0, data, ut)

def test_tenders_view_check_lothandler_lot_complete_default_pass(db, ut):
    # if date in lot == False
    # this.lot_date = contract_date                         
    data = {        
        "status": "complete",    
        "procurementMethodType": "belowThreshold",
        'numberOfBids': 2,
        'awardPeriod': {'startDate': '2016-04-12T13:32:25.774673+02:00'},
        "enquiryPeriod": {
            "startDate": '2016-04-17T13:32:25.774673+02:00',
        },
        "awards": test_awards,
        "contracts":test_contracts_2,        
        "tenderPeriod": {
            "startDate": "2016-11-13T15:15:00+02:00",
        },
        "lots": [
            {
                "status": "complete",
                "id": "324d7b2dd7a54df29bad6d0b7c91b2e9",
                "value": {
                    "currency": "UAH",
                    "amount": 2000,
                    "valueAddedTaxIncluded": "False",
                },
            }
        ],
        "bids": test_bids,
    }
    assertLen(1, data, ut)

def test_tenders_view_check_lothandler_lot_complete_default_fail_by_awardID(db, ut):
    # if date in lot == False
    # (award.id === contract.awardID) == False
    # this.lot_date = null;                        
    data = {        
        "status": "complete",    
        "procurementMethodType": "belowThreshold",
        'numberOfBids': 2,
        'awardPeriod': {'startDate': '2016-04-12T13:32:25.774673+02:00'},
        "enquiryPeriod": {
            "startDate": '2016-04-17T13:32:25.774673+02:00',
        },
        "awards": test_awards,
        "contracts": [
            {
                "status": "active",
                "awardID": "da6b3f912070460ca082b969a2f91e6d",
                "id": "1ac8c648538d4930918b0b0a1e884ef2",
                "date": '2016-04-22T13:32:25.774673+02:00',
                "dateSigned": '2016-05-22T13:32:25.774673+02:00',
                "documents": [{
                    'datePublished': "2016-06-22T13:32:25.774673+02:00",
                },]
            }
        ],        
        "tenderPeriod": {
            "startDate": "2016-11-13T15:15:00+02:00",
        },
        "lots": [
            {
                "status": "complete",
                "id": "324d7b2dd7a54df29bad6d0b7c91b2e9",
                "value": {
                    "currency": "UAH",
                    "amount": 2000,
                    "valueAddedTaxIncluded": "False",
                },
            }
        ],
        "bids": test_bids,
    }
    assertLen(0, data, ut)

def test_tenders_view_check_lothandler_lot_complete_default_fail_by_lotID(db, ut):
    # if date in lot == False
    # (award.lotID === lot.id) == False
    # this.lot_date = null;                         
    data = {        
        "status": "complete",    
        "procurementMethodType": "belowThreshold",
        'numberOfBids': 2,
        'awardPeriod': {'startDate': '2016-04-12T13:32:25.774673+02:00'},
        "enquiryPeriod": {
            "startDate": '2016-04-17T13:32:25.774673+02:00',
        },
        "awards": [
               {
                   "complaintPeriod": {
                       "startDate": "2016-06-01T12:16:40.832321+03:00",
                       "endDate": "2016-06-14T18:31:52.162261+03:00"
                   },
                   "status": "active",
                   "lotID": "324d7b2dd7a54df29bad6d0b7c91b2e0",
                   "bid_id": "a22ef2b1374b43ddb886821c0582bc7dk",
                   "value": {
                       "currency": "UAH",
                       "amount": 2000,
                       "valueAddedTaxIncluded": "True"
                   },
                   "date": "2016-11-13T15:15:00+02:00",
                   "id": "da6b3f912070460ca082b969a2f91e5d"
                }
            ],
        "contracts":test_contracts_2,        
        "tenderPeriod": {
            "startDate": "2016-11-13T15:15:00+02:00",
        },
        "lots": [
            {
                "status": "complete",
                "id": "324d7b2dd7a54df29bad6d0b7c91b2e9",
                "value": {
                    "currency": "UAH",
                    "amount": 2000,
                    "valueAddedTaxIncluded": "False",
                },
            }
        ],
        "bids": test_bids,
    }
    assertLen(0, data, ut)

def test_tenders_view_check_lothandler_lot_active_default_pass(db, ut):
    # if date in lot == False
    # this.lot_date = lotDate                         
    data = {        
        "status": "complete",    
        "procurementMethodType": "belowThreshold",
        'numberOfBids': 2,
        'awardPeriod': {'startDate': '2016-04-12T13:32:25.774673+02:00'},
        "enquiryPeriod": {
            "startDate": '2016-04-17T13:32:25.774673+02:00',
        },
        "awards": test_awards,
        "contracts":test_contracts_2,        
        "tenderPeriod": {
            "startDate": "2016-11-13T15:15:00+02:00",
        },
        "lots": [
            {
                "status": "active",
                "id": "324d7b2dd7a54df29bad6d0b7c91b2e9",
                "value": {
                    "currency": "UAH",
                    "amount": 2000,
                    "valueAddedTaxIncluded": "False",
                },
            }
        ],
        "bids": test_bids,
    }
    assertLen(1, data, ut)

def test_tenders_view_check_lothandler_lot_active_default_fail_by_lotID(db, ut):
    # if date in lot == False
    # (award.lotID === lot.id) == False
    # this.lot_date = null;                        
    data = {        
        "status": "complete",    
        "procurementMethodType": "belowThreshold",
        'numberOfBids': 2,
        'awardPeriod': {'startDate': '2016-04-12T13:32:25.774673+02:00'},
        "enquiryPeriod": {
            "startDate": '2016-04-17T13:32:25.774673+02:00',
        },
        "awards": [
               {
                   "complaintPeriod": {
                       "startDate": "2016-06-01T12:16:40.832321+03:00",
                       "endDate": "2016-06-14T18:31:52.162261+03:00"
                   },
                   "status": "active",
                   "lotID": "324d7b2dd7a54df29bad6d0b7c91b2e0",
                   "bid_id": "a22ef2b1374b43ddb886821c0582bc7dk",
                   "value": {
                       "currency": "UAH",
                       "amount": 2000,
                       "valueAddedTaxIncluded": "True"
                   },
                   "date": "2016-11-13T15:15:00+02:00",
                   "id": "da6b3f912070460ca082b969a2f91e5d"
                }
            ],
        "contracts": [
            {
                "status": "active",
                "awardID": "da6b3f912070460ca082b969a2f91e6d",
                "id": "1ac8c648538d4930918b0b0a1e884ef2",
                "date": '2016-04-22T13:32:25.774673+02:00',
                "dateSigned": '2016-05-22T13:32:25.774673+02:00',
                "documents": [{
                    'datePublished': "2016-06-22T13:32:25.774673+02:00",
                },]
            }
        ],        
        "tenderPeriod": {
            "startDate": "2016-11-13T15:15:00+02:00",
        },
        "lots": [
            {
                "status": "active",
                "id": "324d7b2dd7a54df29bad6d0b7c91b2e9",
                "value": {
                    "currency": "UAH",
                    "amount": 2000,
                    "valueAddedTaxIncluded": "False",
                },
            }
        ],
        "bids": test_bids,
    }
    assertLen(0, data, ut)

def test_tenders_view_check_lothandler_lot_active_default_fail_by_awardID(db, ut):
    # if date in lot == False
    # (award.id === contract.awardID) == False
    # this.lot_date = null;                         
    data = {        
        "status": "complete",    
        "procurementMethodType": "belowThreshold",
        'numberOfBids': 2,
        'awardPeriod': {'startDate': '2016-04-12T13:32:25.774673+02:00'},
        "enquiryPeriod": {
            "startDate": '2016-04-17T13:32:25.774673+02:00',
        },
        "awards": [
               {
                   "complaintPeriod": {
                       "startDate": "2016-06-01T12:16:40.832321+03:00",
                       "endDate": "2016-06-14T18:31:52.162261+03:00"
                   },
                   "status": "active",
                   "lotID": "324d7b2dd7a54df29bad6d0b7c91b2e0",
                   "bid_id": "a22ef2b1374b43ddb886821c0582bc7dk",
                   "value": {
                       "currency": "UAH",
                       "amount": 2000,
                       "valueAddedTaxIncluded": "True"
                   },
                   "date": "2016-11-13T15:15:00+02:00",
                   "id": "da6b3f912070460ca082b969a2f91e5d"
                }
            ],
        "contracts":test_contracts_2,        
        "tenderPeriod": {
            "startDate": "2016-11-13T15:15:00+02:00",
        },
        "lots": [
            {
                "status": "active",
                "id": "324d7b2dd7a54df29bad6d0b7c91b2e9",
                "value": {
                    "currency": "UAH",
                    "amount": 2000,
                    "valueAddedTaxIncluded": "False",
                },
            }
        ],
        "bids": test_bids,
    }
    assertLen(0, data, ut)

def test_tenders_view_check_lothandler_lot_complete_default_fail_by_contract_status(db, ut):
    # if date in lot == False
    # (contract.status === 'active') == False
    # contract.status == cancelled
    # this.lot_date = null;                        
    data = {        
        "status": "complete",    
        "procurementMethodType": "belowThreshold",
        'numberOfBids': 2,
        'awardPeriod': {'startDate': '2016-04-12T13:32:25.774673+02:00'},
        "enquiryPeriod": {
            "startDate": '2016-04-17T13:32:25.774673+02:00',
        },
        "awards": [
               {
                   "complaintPeriod": {
                       "startDate": "2016-06-01T12:16:40.832321+03:00",
                       "endDate": "2016-06-14T18:31:52.162261+03:00"
                   },
                   "status": "active",
                   "lotID": "324d7b2dd7a54df29bad6d0b7c91b2e0",
                   "bid_id": "a22ef2b1374b43ddb886821c0582bc7dk",
                   "value": {
                       "currency": "UAH",
                       "amount": 2000,
                       "valueAddedTaxIncluded": "True"
                   },
                   "date": "2016-11-13T15:15:00+02:00",
                   "id": "da6b3f912070460ca082b969a2f91e5d"
                }
            ],
        "contracts": [
            {
                "status": "cancelled",
                "awardID": "da6b3f912070460ca082b969a2f91e5d",
                "id": "1ac8c648538d4930918b0b0a1e884ef2",
                "date": '2016-04-22T13:32:25.774673+02:00',
                "dateSigned": '2016-05-22T13:32:25.774673+02:00',
                "documents": [{
                    'datePublished': "2016-06-22T13:32:25.774673+02:00",
                },]
            }
        ],        
        "tenderPeriod": {
            "startDate": "2016-11-13T15:15:00+02:00",
        },
        "lots": [
            {
                "status": "active",
                "id": "324d7b2dd7a54df29bad6d0b7c91b2e9",
                "value": {
                    "currency": "UAH",
                    "amount": 2000,
                    "valueAddedTaxIncluded": "False",
                },
            }
        ],
        "bids": test_bids,
    }
    assertLen(0, data, ut)

def test_tenders_view_check_lothandler_lot_tenderCancelled_active_default_fail_by_cancellation_status(db, ut):
    # if date in lot == False
    # (tender.status === 'cancelled') == True  
    # (this.tender_handler.tender_date !== null) == False  (cancellation status - "pending")
    data =  {        
        "status": "cancelled",    
        "procurementMethodType": "belowThreshold",
        'numberOfBids': 2,
        'awardPeriod': {'startDate': '2016-04-12T13:32:25.774673+02:00'},
        "enquiryPeriod": {
            "startDate": '2016-04-17T13:32:25.774673+02:00',
        },
        "awards": test_awards,
        "cancellations":[{
                        "cancellationOf": "tender",
                        "date": "2016-11-13T15:10:00+02:00",
                        "status": "pending"
                    },{
                        "cancellationOf": "tender",
                        "date": "2016-11-13T15:10:00+02:00",
                        "status": "pending"
                    }],
        "contracts":test_contracts_2,        
        "tenderPeriod": {
            "startDate": "2016-11-13T15:15:00+02:00",
        },
        "lots": [
            {
                "status": "active",
                "id": "324d7b2dd7a54df29bad6d0b7c91b2e9",
                "value": {
                    "currency": "UAH",
                    "amount": 2000,
                    "valueAddedTaxIncluded": "False",
                },
            }
        ],
        "bids": test_bids,
    }
    assertLen(0, data, ut)

def test_tenders_view_check_lothandler_lot_tenderCancelled_active_default_fail_by_date(db, ut):
    # if date in lot == False
    # (tender.status === 'cancelled') == True  
    # ( this.tender_handler.tender_date > this.tender_handler.bids_disclosure_standstill) == False  
    data =  {        
        "status": "cancelled",    
        "procurementMethodType": "belowThreshold",
        "date": '2016-04-10T13:01:25.774673+02:00',
        'numberOfBids': 2,
        'awardPeriod': {'startDate': '2016-04-12T13:32:25.774673+02:00'},
        "enquiryPeriod": {
            "startDate": '2016-04-17T13:32:25.774673+02:00',
        },
        "awards": test_awards,
        "cancellations":[{
                        "cancellationOf": "tender",
                        "date": "2016-11-13T15:10:00+02:00",
                        "status": "active"
                    },{
                        "cancellationOf": "tender",
                        "date": "2016-11-13T15:10:00+02:00",
                        "status": "active"
                    }],
        "contracts":test_contracts_2,        
        "tenderPeriod": {
            "startDate": "2016-11-13T15:15:00+02:00",
        },
        "lots": [
            {
                "status": "active",
                "id": "324d7b2dd7a54df29bad6d0b7c91b2e9",
                "value": {
                    "currency": "UAH",
                    "amount": 2000,
                    "valueAddedTaxIncluded": "False",
                },
            }
        ],
        "bids": test_bids,
    }
    assertLen(0, data, ut)



#  end new tests
def test_tenders_view_valid(db, ut):
    data = {        
        "status": "complete",
        "date": '2016-04-22T13:32:25.774673+02:00',        
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
    assertLen(1, data, ut)
    ut.get_response()
    ut.response = list(ut.response)
    response = list(ut.response)
    assert u"2016-04-22T11:32:25.774" == response[0]['key'][1]

def test_tenders_utility_output(db, ut):
    data = {        
        "status": "complete",
        "date": '2016-04-22T13:32:25.774673+02:00',        
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
    ut.db.save(doc)
    with mock.patch('__builtin__.open', mock_csv):
        ut.run()
        row = [['0006651836f34bcda9a030c0bf3c0e6e,UA-2016-11-12-000150,,complete,,UAH,general,1000,,5.0'],]
        assert_csv(mock_csv, 'test/test@---tenders.csv', ut.headers, row)
        