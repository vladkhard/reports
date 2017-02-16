import pytest
import mock
import couchdb
import os.path
from copy import copy
from reports.config import Config
from reports.utilities import bids, invoices, tenders, refunds
from reports.utilities.bids import BidsUtility
from reports.tests.utils import(
    get_mock_parser,
    test_data,
    assert_csv,
    db,
    assertLen
)

test_bids_invalid = [
    [{
        "owner": "test",
        "status": "invalid",
        "date": "2016-03-17T13:32:25.774673+02:00",
        "id": "44931d9653034837baff087cfc2fb5ac",
    }],
    [{
        "status": "invalid",
        "owner": "test",
        "date": "2016-04-17T13:32:25.774673+02:00",
        "id": "44931d9653034837baff087cfc2fb5ac"
    }]
]

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
        "status": "active",
        "owner": "test",
        "date": "2016-05-10T13:32:25.774673+02:00",
        "id": "f55962b1374b43ddb886821c0582bc7f"
    }],
    [{
        "status": "active",
        "owner": "test",
        "date": "2016-05-10T13:32:25.774673+02:00",
        "id": "f55962b1374b43ddb886821c0582bc7f"
    },
    {
        "status": "active",
        "owner": "test1",
        "date": "2016-05-10T13:42:25.774673+02:00",
        "id": "f55962b1374b83ddb886821c0582bc7f"
    }
    ]]

test_lots = [{
                "status": "cancelled",
                "id": "324d7b2dd7a54df29bad6d0b7c91b2e9",
                "value": {
                    "currency": "UAH",
                    "amount": 2000,
                    "valueAddedTaxIncluded": False,
                },
            }]

test_bids = [{
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
            }]

test_2_bids = [
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
            },
            {
                "date": "2016-04-07T16:46:58.983102+03:00",
                "owner": "te3st",
                "status": "active",
                "id": "a22ef2b1374b43ddb886821c0582bc7dj",
                "lotValues": [
                    {
                        "relatedLot": "324d7b2dd7a54df29bad6d0b7c91b2e9",
                        "date": "2016-04-07T16:36:58.983062+03:00",
                    }
                ],
            }
        ]

test_award_period = '2016-04-17T13:32:25.774673+02:00'

@pytest.fixture(scope='function')
def ut(request):
    mock_parse = get_mock_parser()
    with mock.patch('argparse.ArgumentParser.parse_args', mock_parse):
        utility = BidsUtility()
    return utility

def test_bids_view_invalid_date(db, ut):
    data = {
        "awardPeriod": {
            "startDate": test_award_period,
        },
        'owner': 'teser',
        "bids": test_bids_invalid[0],
    }
    assertLen(0, data, ut)

def test_bids_view_invalid_mode(db, ut):
    data = {
        'mode': 'test',
        "awardPeriod": {
            "startDate": test_award_period,
        },
        'owner': 'teser',
        "bids": test_bids_valid[0],
    }
    assertLen(0, data, ut)

def test_bids_view_invalid_status(db, ut):
    data = {
        "procurementMethod": "open",
        "awardPeriod": {
            "startDate": test_award_period,
        },
        'owner': 'teser',
        'bids': test_bids_invalid[1],
    }
    assertLen(0, data, ut)

def test_bids_view_invalid_method(db, ut):
    data = {
        "procurementMethod": "test",
        "awardPeriod": {
            "startDate": test_award_period,
        },
        'owner': 'teser',
        'bids': test_bids_valid[0],
    }
    assertLen(0, data, ut)

#  start new bids_view tests

def test_bids_view_invalid_doc_type(db, ut):
    # (doc.doc_type !== "Tender") {return;}
    data = {
        "doc_type": "new Tender",
        "awardPeriod": {
            "startDate": test_award_period,
        },
        'owner': 'teser',
        'bids': test_bids_valid[2],
    }
    assertLen(0, data, ut)

def test_bids_view_EUprocurement_type_valid_data(db, ut):
    # (count_lot_qualifications(tender.qualifications, lot.id) < 2) == False
    data = {
        "procurementMethodType": "aboveThresholdEU",
        "qualifications": [{
            "bidID": "f55962b1374b43ddb886821c0582bc7f"
        },
        {
            "bidID": "f55962b1374b83ddb886821c0582bc7f"
        }
        ],
        "awardPeriod": {
            "startDate": test_award_period,
        },
        "qualificationPeriod":{
            "startDate": "2016-11-13T15:15:00+02:00"
        },
        'owner': 'teser',
        'bids': test_bids_valid[3],
    }
    assertLen(1, data, ut)

def test_bids_view_procurement_typeEU_without_qualifications(db, ut):
    # (count_lot_qualifications(tender.qualifications, lot.id) < 2) == True
    data = {
        "procurementMethodType": "aboveThresholdEU",
        "awardPeriod": {
            "startDate": test_award_period,
        },
        "qualificationPeriod":{
            "startDate": "2016-11-13T15:15:00+02:00"
        },
        'owner': 'teser',
        'bids': test_bids_valid[3],
    }
    assertLen(0, data, ut)

def test_bids_view_have_no_disclojure_date(db, ut):
    # var bids_disclojure_date = (doc.qualificationPeriod || {}).startDate || (doc.awardPeriod || {}).startDate || null;
    # if(!bids_disclojure_date) { return; }
    data = {
        "awardPeriod": {
            "startDate": "",
        },
        'owner': 'teser',
        "bids": test_bids_valid[0],
    }
    assertLen(0, data, ut)

def test_bids_view_compet_dialog_stage2_fail_check(db, ut):
    # if (['competitiveDialogueEU.stage2', 'competitiveDialogueUA.stage2'].indexOf(doc.procurementMethodType) !== -1) {
    # log('Skipping tender stage2 ' + doc._id)        return;    }
    data = {
        "procurementMethodType": "competitiveDialogueEU.stage2",
        "awardPeriod": {
            "startDate": test_award_period,
        },
        "qualificationPeriod": {
                    "startDate": "",
                },
        'owner': 'teser',
        "bids": test_bids_valid[0],
    }
    assertLen(0, data, ut)

def test_bids_view_cancelled_tender(db, ut):
    # (tender_cancellations.length > 1)
    data = {
        "status": "cancelled",
        "cancellations":[{
                        "cancellationOf": "tender",
                        "status": "active"
                    },{
                        "cancellationOf": "tender",
                        "status": "active"
                    }],
        "awardPeriod": {
            "startDate": test_award_period,
        },
        'owner': 'teser',
        "bids": test_bids_valid[0],
    }
    assertLen(1, data, ut)

def test_bids_view_cancelled_tender_invalid_time(db, ut):
    # without tender.date
    # (max_date( cancel ) < (new Date( bids_disclojure_date ))) == True
    data = {
        "status": "cancelled",
        "cancellations":[{
                        "cancellationOf": "tender",
                        "date": "2016-11-13T15:10:00+02:00",
                        "status": "active"
                    },{
                        "cancellationOf": "tender",
                        "date": "2016-11-13T15:10:00+02:00",
                        "status": "active"
                    }],
        "awardPeriod": {
            "startDate": test_award_period,
        },
        "qualificationPeriod": {
                    "startDate": "2016-11-13T15:15:00+02:00",
                },
        'owner': 'teser',
        "bids": test_bids_valid[0],
    }
    assertLen(0, data, ut)

def test_bids_view_cancelled_tender_before_award(db, ut):
    # ((new Date(tender.date)) < (new Date(bids_disclojure_date))) == True
    data = {
        "date": "2016-10-31T19:00:00+03:00",
        "status": "cancelled",
        "cancellations":[{
                        "cancellationOf": "tender",
                        "date": "2016-11-13T15:10:00+02:00",
                        "status": "active"
                    }],
        "awardPeriod": {
            "startDate": '2016-11-17T13:32:25.774673+02:00',
        },
        'owner': 'teser',
        "bids": test_bids_valid[0],
    }
    assertLen(0, data, ut)

def test_bids_view_cancelled_tender_after_award(db, ut):
    # ((new Date(tender.date)) < (new Date(bids_disclojure_date))) == False
    data = {
        "date": "2016-11-25T19:00:00+03:00",
        "status": "cancelled",
        "cancellations":[{
                        "cancellationOf": "tender",
                        "date": "2016-11-13T15:10:00+02:00",
                        "status": "active"
                    }],
        "awardPeriod": {
            "startDate": '2016-11-17T13:32:25.774673+02:00',
        },
        'owner': 'teser',
        "bids": test_bids_valid[0],
    }
    assertLen(1, data, ut)

def test_bids_view_cancelled_tender_without_cancellations(db, ut):
    # tender_cancellations.length === 0
    data = {
        "status": "cancelled",
        "awardPeriod": {
            "startDate": '2016-11-17T13:32:25.774673+02:00',
        },
        'owner': 'teser',
        "bids": test_bids_valid[0],
    }
    assertLen(0, data, ut)

def test_bids_view_cancelled_tender_few_tenders_before_disclojure_date(db, ut):
    # (max_date( tender_cancellations[0] ) < (new Date( bids_disclojure_date ))) == True
    data = {
        "status": "cancelled",
        "cancellations":[{
                        "cancellationOf": "tender",
                        "date": "2016-11-13T15:10:00+02:00",
                        "status": "active"
                    }],
        "awardPeriod": {
            "startDate": "2016-12-13T15:10:00+02:00",
        },
        'owner': 'teser',
        "bids": test_bids_valid[0],
    }
    assertLen(0, data, ut)

def test_bids_view_cancelled_few_tenders_after_disclojure_date(db, ut):
    # (max_date( tender_cancellations[0] ) < (new Date( bids_disclojure_date ))) == False
    data = {
        "status": "cancelled",
        "cancellations":[{
                        "cancellationOf": "tender",
                        "date": "2016-11-13T15:10:00+02:00",
                        "status": "active"
                    }],
        "awardPeriod": {
            "startDate": test_award_period,
        },
        'owner': 'teser',
        "bids": test_bids_valid[0],
    }
    assertLen(1, data, ut)

def test_bids_view_check_tender_bids_UA(db, ut):
    # if (tender.numberOfBids < 2) == True
    data = {
        "status": "cancelled",
        "procurementMethodType": "aboveThresholdUA",
        "numberOfBids": 1,
        "cancellations":[{
                        "cancellationOf": "tender",
                        "date": "2016-11-13T15:17:00+02:00",
                        "status": "active"
                    }],
        "awardPeriod": {
            "startDate": test_award_period,
        },
        'owner': 'teser',
        'bids': test_bids_valid[3],
    }
    assertLen(0, data, ut)

def test_bids_view_check_tender_bids_EU(db, ut):
    # if ((tender.qualifications || []).length < 2) == false
    data = {
        "status": "cancelled",
        "procurementMethodType": "aboveThresholdEU",
        "cancellations":[{
                        "cancellationOf": "tender",
                        "date": "2016-11-13T15:17:00+02:00",
                        "status": "active"
                    }],
        "qualifications": [{
            "bidID": "f55962b1374b43ddb886821c0582bc7f"
        },
        {
            "bidID": "f55962b1374b83ddb886821c0582bc7f"
        }
        ],
        "awardPeriod": {
            "startDate": test_award_period,
        },
        "qualificationPeriod":{
            "startDate": "2016-11-13T15:15:00+02:00"
        },
        'owner': 'teser',
        'bids': test_bids_valid[3],
    }
    assertLen(1, data, ut)


def test_bids_view_check_tender_bids_UA_defense(db, ut):
    # if ((tender.numberOfBids < 2) && !('awards' in tender)) == False
    data = {
        "status": "cancelled",
        "numberOfBids": 2,
        "procurementMethodType": "aboveThresholdUA.defense",
        "cancellations":[{
                        "cancellationOf": "tender",
                        "date": "2016-11-13T15:17:00+02:00",
                        "status": "active"
                    }],
        "awardPeriod": {
            "startDate": test_award_period,
        },
        'owner': 'teser',
        'bids': test_bids_valid[3],
    }
    assertLen(1, data, ut)

def test_bids_view_check_tender_bids_UA_defense_0_bids(db, ut):
    # if ((tender.numberOfBids < 2) && !('awards' in tender)) == True
    data = {
        "status": "cancelled",
        "numberOfBids": 0,
        "procurementMethodType": "aboveThresholdUA.defense",
        "cancellations":[{
                        "cancellationOf": "tender",
                        "date": "2016-11-13T15:17:00+02:00",
                        "status": "active"
                    }],
        "awardPeriod": {
            "startDate": test_award_period,
        },
        'owner': 'teser',
        'bids': test_bids_valid[3],
    }
    assertLen(0, data, ut)

def test_bids_view_check_tender_bids_CD_EU(db, ut):
    #  if ((tender.qualifications || []).length < 3) == False
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
            "bidID": "f55962b1374b83ddb886821c0582bc7f"
        },
        {
            "bidID": "f55962b2374b83ddb886821c0582bc7f"
        }
        ],
        "awardPeriod": {
            "startDate": test_award_period,
        },
        "qualificationPeriod":{
            "startDate": "2016-11-13T15:15:00+02:00"
        },
        'owner': 'teser',
        'bids': test_bids_valid[3],
    }
    assertLen(1, data, ut)

def test_bids_view_check_tender_bids_CD_EU_two_qual(db, ut):
    #  if ((tender.qualifications || []).length < 3) == True
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
        "awardPeriod": {
            "startDate": test_award_period,
        },
        "qualificationPeriod":{
            "startDate": "2016-11-13T15:15:00+02:00"
        },
        'owner': 'teser',
        'bids': test_bids_valid[3],
    }
    assertLen(0, data, ut)

def test_bids_view_check_tender_unsuccesfull(db, ut):
    # if (! check_tender_bids(tender)) == True
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
        'owner': 'teser',
        'bids': test_bids_valid[3],
    }
    assertLen(1, data, ut)

def test_bids_view_check_tender_unsuccesfull_invalid(db, ut):
    # if (! check_tender_bids(tender)) == True
    data = {
        "status": "unsuccessful",
        "procurementMethodType": "competitiveDialogueEU",
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
        'owner': 'teser',
        'bids': test_bids_valid[3],
    }
    assertLen(0, data, ut)

def test_bids_view_check_cancelled_lot(db, ut):
    # if ('date' in lot) == False
    # lot_cancellation = 0
    data = {
        "procurementMethodType": "belowThreshold",
        "awardPeriod": {
            "startDate": test_award_period,
        },
        "lots": test_lots,
        "bids": test_bids,
        "owner": "teser"
    }
    assertLen(1, data, ut)

def test_bids_view_check_cancelled_lot_with_date_fail(db, ut):
    # if ('date' in lot) == True
    #  ((new Date(lot.date)) < (new Date(bids_disclojure_date))) == True
    data = {
        "procurementMethodType": "belowThreshold",
        "awardPeriod": {
            "startDate": test_award_period,
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
        "owner": "teser"
    }
    assertLen(0, data, ut)

def test_bids_view_check_cancelled_lot_with_date_pass(db, ut):
    # if ('date' in lot) == True
    #  ((new Date(lot.date)) < (new Date(bids_disclojure_date))) == True
    data = {
        "procurementMethodType": "belowThreshold",
        "awardPeriod": {
            "startDate": test_award_period,
        },
        "lots": [
            {
                "status": "cancelled",
                "date": "2016-04-27T16:36:58.983102+03:00",
                "id": "324d7b2dd7a54df29bad6d0b7c91b2e9",
                "value": {
                    "currency": "UAH",
                    "amount": 2000,
                    "valueAddedTaxIncluded": False,
                },
            }
        ],
        "bids": test_bids,
        "owner": "teser"
    }
    assertLen(1, data, ut)

def test_bids_view_check_cancelled_related_lot(db, ut):
    # ((cancellation.status === 'active') && (cancellation.cancellationOf === 'lot') && (cancellation.relatedLot === lot.id)) == True
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
        "lots": test_lots,
        "bids": test_bids,
        "owner": "teser"
    }
    assertLen(1, data, ut)

def test_bids_view_check_cancelled_lot_1_cancellation_fail(db, ut):
    # (max_date(lot_cancellation[0]) < (new Date(bids_disclojure_date))) == True
    data = {
        "procurementMethodType": "belowThreshold",
        "awardPeriod": {
            "startDate": "2016-12-13T15:10:00+02:00",
        },
        "cancellations":[{
                        "cancellationOf": "lot",
                        "date": "2016-11-13T15:10:00+02:00",
                        "status": "active",
                       "relatedLot": "324d7b2dd7a54df29bad6d0b7c91b2e9",
                    }],
        "lots": test_lots,
        "bids": test_bids,
        "owner": "teser"
    }
    assertLen(0, data, ut)

def test_bids_view_check_cancelled_lot_1_cancellation(db, ut):
    # (max_date(lot_cancellation[0]) < (new Date(bids_disclojure_date))) == False
    data = {
        "procurementMethodType": "belowThreshold",
        "awardPeriod": {
            "startDate": test_award_period,
        },
        "cancellations":[{
                        "cancellationOf": "lot",
                        "date": "2016-12-13T15:10:00+02:00",
                        "status": "active",
                       "relatedLot": "324d7b2dd7a54df29bad6d0b7c91b2e9",
                    }],
        "lots": test_lots,
        "bids": test_bids,
        "owner": "teser"
    }
    assertLen(1, data, ut)


def test_bids_view_check_cancelled_lot_2_cancellations_fail(db, ut):
    # if (max_date(cancel) < (new Date(bids_disclojure_date))) == True
    data = {
        "procurementMethodType": "belowThreshold",
        "awardPeriod": {
            "startDate": "2016-12-13T15:10:00+02:00",
        },
        "cancellations":[{
                        "cancellationOf": "lot",
                        "status": "active",
                        "date": "2016-11-13T15:10:00+02:00",
                        "relatedLot": "324d7b2dd7a54df29bad6d0b7c91b2e9",
                    },{
                        "cancellationOf": "lot",
                        "status": "active",
                        "date": "2016-11-13T15:10:00+02:00",
                        "relatedLot": "324d7b2dd7a54df29bad6d0b7c91b2e9",
                    }],
        "lots": test_lots,
        "bids": test_bids,
        "owner": "teser"
    }
    assertLen(0, data, ut)

def test_bids_view_check_cancelled_lot_2_cancellations(db, ut):
    # if (max_date(cancel) < (new Date(bids_disclojure_date))) == False
    data = {
        "procurementMethodType": "belowThreshold",
        "awardPeriod": {
            "startDate": "2016-11-13T15:15:00+02:00",
        },
        "cancellations":[{
                        "cancellationOf": "lot",
                        "status": "active",
                        "date": "2016-11-13T15:20:00+02:00",
                        "relatedLot": "324d7b2dd7a54df29bad6d0b7c91b2e9",
                    },{
                        "cancellationOf": "lot",
                        "status": "active",
                        "date": "2016-11-13T15:20:00+02:00",
                        "relatedLot": "324d7b2dd7a54df29bad6d0b7c91b2e9",
                    }],
        "lots": [
            {
                "status": "cancelled",
                "id": "324d7b2dd7a54df29bad6d0b7c91b2e9",
                "value": {
                    "currency": "UAH",
                    "amount": 2000,
                    "valueAddedTaxIncluded": False,
                },
            }
        ],
        "bids": test_bids,
        "owner": "teser"
    }
    assertLen(1, data, ut)

def test_bids_view_check_unsuccessfull(db, ut):
    # if (! check_lot_bids(tender, lot)) == False
    data = {
        "procurementMethodType": "belowThreshold",
        "awardPeriod": {
            "startDate": "2016-11-13T15:15:00+02:00",
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
        "bids": test_bids,
        "owner": "teser"
    }
    assertLen(1, data, ut)

def test_bids_view_check_unsuccessfull_fail(db, ut):
    # if (! check_lot_bids(tender, lot)) == True
    data = {
        "procurementMethodType": "aboveThresholdUA.defense",
        "awardPeriod": {
            "startDate": "2016-11-13T15:15:00+02:00",
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
        "bids": test_bids,
        "owner": "teser"
    }
    assertLen(0, data, ut)

def test_bids_view_check_lot_bids_unsuccessfull_UA(db, ut):
    #  if (count_lot_bids(lot, tender) < 2) == False
    data = {
        "procurementMethodType": "aboveThresholdUA",
        "awardPeriod": {
            "startDate": "2016-11-13T15:15:00+02:00",
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
        "bids": test_2_bids,
        "owner": "teser"
    }
    assertLen(1, data, ut)

def test_bids_view_check_lot_bids_unsuccessfull_UA_fail(db, ut):
    #  if (count_lot_bids(lot, tender) < 2) == True
    data = {
        "procurementMethodType": "aboveThresholdUA",
        "awardPeriod": {
            "startDate": "2016-11-13T15:15:00+02:00",
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
        "bids": test_bids,
        "owner": "teser"
    }
    assertLen(0, data, ut)

def test_bids_view_check_lot_bids_unsuccessfull_EU(db, ut):
    # if (count_lot_qualifications(tender.qualifications, lot.id) < 2) == False
    data = {
        "status": "unsuccessful",
        "procurementMethodType": "aboveThresholdEU",
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
        "bids": test_2_bids,
        "owner": "teser"
    }
    assertLen(1, data, ut)

def test_bids_view_check_lot_bids_unsuccessfull_EU_1_qual_fail(db, ut):
    # if (count_lot_qualifications(tender.qualifications, lot.id) < 2) == True
    data = {
        "status": "unsuccessful",
        "procurementMethodType": "aboveThresholdEU",
        "qualifications": [
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
        "bids": test_2_bids,
        "owner": "teser"
    }
    assertLen(0, data, ut)

def test_bids_view_check_lot_bids_unsuccessfull_UAdef(db, ut):
    # (((count_lot_bids(lot, tender) < 2) && (lot_awards.length === 0))) == False
    data = {
        "procurementMethodType": "aboveThresholdUA.defense",
        "awardPeriod": {
            "startDate": "2016-11-13T15:15:00+02:00",
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
        "bids": test_2_bids,
        "owner": "teser"
    }
    assertLen(1, data, ut)

def test_bids_view_check_lot_bids_unsuccessfull_UA_def_fail(db, ut):
    # (((count_lot_bids(lot, tender) < 2) && (lot_awards.length === 0))) == True
    data = {
        "procurementMethodType": "aboveThresholdUA.defense",
        "awardPeriod": {
            "startDate": "2016-11-13T15:15:00+02:00",
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
        "bids": test_bids,
        "owner": "teser"
    }
    assertLen(0, data, ut)

def test_bids_view_check_lot_bids_unsuccessfull_UA_def_with_award_and_1_bid(db, ut):
    # (((count_lot_bids(lot, tender) < 2) && (lot_awards.length === 0))) == False
    data = {
        "procurementMethodType": "aboveThresholdUA.defense",
        "awardPeriod": {
            "startDate": "2016-11-13T15:15:00+02:00",
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
        "bids": test_bids,
        "owner": "teser"
    }
    assertLen(1, data, ut)

def test_bids_view_check_lot_bids_unsuccessfull_competitiveDialogueEU(db, ut):
    # if (count_lot_qualifications(tender.qualifications, lot.id) < 3) == False
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
        "bids": test_2_bids,
        "owner": "teser"
    }
    assertLen(1, data, ut)

def test_bids_view_check_lot_bids_unsuccessfull_competitiveDialogueEU_fail_with_2_qualifications(db, ut):
    # if (count_lot_qualifications(tender.qualifications, lot.id) < 3) == True
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
        "bids": test_2_bids,
        "owner": "teser"
    }
    assertLen(0, data, ut)

def test_bids_view_check_audit_documents(db, ut):
    # if(is_multilot) == True
    # var audits = (tender.documents || []).filter(function(tender_doc) {
    # return tender_doc.title.indexOf("audit_" + id + "_" + lot.id) === 0; });
    # audit = audits[0]
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
        "bids": test_2_bids,
        "owner": "teser"
    }
    assertLen(1, data, ut)
    ut.get_response()
    ut.response = list(ut.response)
    response = list(ut.response)
    assert response[0]['value']['audits'] != None

def test_bids_view_check_audit_2_documents_dateModified_check(db, ut):
    # if(is_multilot) == True
    # if (audits.length > 1) { audit = audits.reduce(function(prev_doc, curr_doc) {return (prev_doc.dateModified > curr_doc.dateModified) ? curr_doc : prev_doc;});
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
        "bids": test_2_bids,
        "owner": "teser"
    }
    assertLen(1, data, ut)
    ut.get_response()
    ut.response = list(ut.response)
    response = list(ut.response)
    assert response[0]['value']['audits']['datePublished'] == "2016-06-01T12:18:40.193283+03:00"

def test_bids_view_check_audit_2_documents_dateModified_check_without_lots(db, ut):
    # if(is_multilot) == False
    # if (audits.length > 1) == True
    data = {
        "status": "unsuccessful",
        "procurementMethodType": "belowThreshold",
        "awardPeriod": {
            "startDate": "2016-11-13T15:15:00+02:00",
            "endDate": "2016-12-30T15:15:00+02:00",
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
        "bids": test_2_bids,
        "owner": "teser"
    }
    assertLen(1, data, ut)

    ut.get_response()
    ut.response = list(ut.response)
    response = list(ut.response)
    assert response[0]['value']['audits']['datePublished'] == "2016-06-01T12:18:40.193283+03:00"
    
def test_bids_view_check_audit_1_document_dateModified_check_without_lots(db, ut):
    # if(is_multilot) == False
    # if (audits.length > 1) == False
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
               "datePublished": "2016-06-01T12:18:40.193283+03:00",
               "dateModified": "2016-06-01T12:19:40.193305+03:00",
               "id": "412e55ba06e847749c24b774fc75b805"
            }
        ],
        "bids": test_bids,
        "owner": "teser"
    }
    assertLen(1, data, ut)
    ut.get_response()
    ut.response = list(ut.response)
    response = list(ut.response)
    assert response[0]['value']['audits'] != None

#  end of new tests

def test_bids_view_valid(db, ut):
    data = {
        "awardPeriod": {
            "startDate": test_award_period,
        },
        'owner': 'teser',
        'bids': test_bids_valid[0],
    }
    assertLen(1, data, ut)
    ut.get_response()
    ut.response = list(ut.response)
    response = list(ut.response)
    assert 1000 == response[0]['value']['value']
    assert "44931d9653034837baff087cfc2fb5ac"== response[0]['value']['bid']
    assert "0006651836f34bcda9a030c0bf3c0e6e"== response[0]['value']['tender']
    assert "UA-2016-11-12-000150"== response[0]['value']['tenderID']
    assert u"UAH"== response[0]['value']['currency']

def test_bids_view_period(db, ut):
    ut.owner = 'test'
    data = {
        "awardPeriod": {
            "startDate": test_award_period,
        },
        'owner': 'teser',
        'bids': test_bids_valid[0],
    }
    doc = copy(test_data)
    doc.update(data)
    ut.db.save(doc)
    data = {
        "_id": "10028cddd23540e5b6abb9efd2756d1d",
        "awardPeriod": {
            "startDate": "2016-11-09T15:00:00+02:00",
        },
        'owner': 'teser',
        'bids': test_bids_valid[1],

    }
    doc = copy(test_data)
    doc.update(data)
    ut.db.save(doc)
    data = {
        "_id": "00028aasd2isdfsde5b6abb9efd2756d1d",
        "awardPeriod": {
            "startDate": "2016-11-30T15:00:00+02:00",
        },
        'owner': 'teser',
        'bids': test_bids_valid[2],
    }
    doc = copy(test_data)
    doc.update(data)
    ut.db.save(doc)

    ut.start_date = ''
    ut.end_date = ''
    ut.get_response()
    assert 3 == len(list(ut.response))

    ut.start_date = "2016-11-10T15:00:00"
    ut.end_date = ''
    ut.get_response()
    assert 1 == len(list(ut.response))
    ut.start_date = "2016-12-01T15:00:00"
    ut.end_date = ''
    ut.get_response()
    assert 0 == len(list(ut.response))
    ut.start_date = "2016-11-01T15:00:00"
    ut.end_date = "2016-12-01T15:00:00"
    ut.get_response()
    assert 2 == len(list(ut.response))

def test_bids_view_period_edge_limit_check(db, ut):
    ut.owner = 'test'
    data = {
        "_id": "10028cddd23540e5b6abb9efd2756de1",
        "awardPeriod": {
            "startDate": "2016-11-01T17:01:00+02:00",
        },
        'owner': 'teser',
        'bids': test_bids_valid[1],
    }
    doc = copy(test_data)
    doc.update(data)
    ut.db.save(doc)
    data = {
        "_id": "10028cddd23540e3b6abb9efd2756de2",
        "awardPeriod": {
            "startDate": "2016-11-01T17:00:00+02:00",
        },
        'owner': 'teser',
        'bids': test_bids_valid[1],
    }
    doc = copy(test_data)
    doc.update(data)
    ut.db.save(doc)
    data = {
        "_id": "10028cddd23540e3b60bb9efd2756de3",
        "awardPeriod": {
            "startDate": "2016-11-01T16:59:00+02:00",
        },
        'owner': 'teser',
        'bids': test_bids_valid[1],

    }
    doc = copy(test_data)
    doc.update(data)
    ut.db.save(doc)
    data = {
        "_id": "10028cddd23520e3b6abb9efd2756de4",
        "awardPeriod": {
            "startDate": "2016-12-01T17:00:00+02:00",
        },
        'owner': 'teser',
        'bids': test_bids_valid[1],

    }
    doc = copy(test_data)
    doc.update(data)
    ut.db.save(doc)
    data = {
        "_id": "10028cddd23540e3b50bb9efd2756de5",
        "awardPeriod": {
            "startDate": "2016-12-01T16:59:00+02:00",
        },
        'owner': 'teser',
        'bids': test_bids_valid[1],
    }
    doc = copy(test_data)
    doc.update(data)
    ut.db.save(doc)
    data = {
        "_id": "00028aasd2isdfsde5b6abb9efd2756de6",
        "awardPeriod": {
            "startDate": "2016-12-01T17:01:00+02:00",
        },
        'owner': 'teser',
        'bids': test_bids_valid[2],
    }
    doc = copy(test_data)
    doc.update(data)
    ut.db.save(doc)
    data = {
        "_id": "00028aasd2isdfsde5b6abb9efd2756de7",
        "awardPeriod": {
            "startDate": "2016-11-30T17:01:00+02:00",
        },
        'owner': 'teser',
        'bids': test_bids_valid[2],
    }
    doc = copy(test_data)
    doc.update(data)
    ut.db.save(doc)

    ut.start_date = "2016-11-01T15:00:00"
    ut.end_date = "2016-12-01T15:00:00"
    ut.get_response()
    # id ends on e1,e2,e5,e7
    assert 4 == len(list(ut.response))

def test_bids_view_with_lots(db, ut):
    data = {
        "enquiryPeriod": {
            "startDate": '2016-04-17T13:32:25.774673+02:00',
        },
        "awardPeriod": {
            "startDate": test_award_period,
        },

        "lots": [
            {
                "status": "active",
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

def test_bids_utility_output(db, ut):
    data = {
        'awardPeriod': {'startDate': test_award_period },
        'bids': test_bids_valid[0],
        "enquiryPeriod": {
            "startDate": '2016-04-17T13:32:25.774673+02:00',
        }
    }
    mock_csv = mock.mock_open()
    doc = copy(test_data)
    doc.update(data)
    ut.db.save(doc)
    with mock.patch('__builtin__.open', mock_csv):
        ut.run()
        row = [['0006651836f34bcda9a030c0bf3c0e6e,UA-2016-11-12-000150,,1000,UAH,44931d9653034837baff087cfc2fb5ac,,7.0'],]
        assert_csv(mock_csv, 'test/test@---bids.csv', ut.headers, row)

def test_bids_utility_output_with_lots(db, ut):
    data = {
        "enquiryPeriod": {
            "startDate": '2016-04-17T13:32:25.774673+02:00',
        },
        "awardPeriod": {
            "startDate": test_award_period,
        },

        "lots": [
            {
                "status": "active",
                "id": "324d7b2dd7a54df29bad6d0b7c91b2e9",
                "value": {
                    "currency": "UAH",
                    "amount": 2000,
                    "valueAddedTaxIncluded": False,
                },
            }
        ],
        "bids": [
            {
                "date": "2016-04-07T16:36:58.983102+03:00",
                "status": "active",
                "owner": "test",
                "id": "a22ef2b1374b43ddb886821c0582bc7dk",
                "lotValues": [
                    {
                        "relatedLot": "324d7b2dd7a54df29bad6d0b7c91b2e9",
                        "date": "2016-04-07T16:36:58.983062+03:00",
                    }
                ],
            }
        ],
    }
    mock_csv = mock.mock_open()
    doc = copy(test_data)
    doc.update(data)
    ut.db.save(doc)
    with mock.patch('__builtin__.open', mock_csv):
        ut.run()
        row = [["0006651836f34bcda9a030c0bf3c0e6e,UA-2016-11-12-000150,324d7b2dd7a54df29bad6d0b7c91b2e9,2000,UAH,a22ef2b1374b43ddb886821c0582bc7dk,,7.0"],]
        assert_csv(mock_csv, 'test/test@---bids.csv', ut.headers, row)