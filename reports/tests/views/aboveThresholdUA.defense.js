"use strict";

let tenders = require("../../design/lib/tenders");
let bids = require("../../design/lib/bids");
let assert = require("../../../src/node_modules/chai").assert;

let tender = {
    procurementMethodType: "aboveThresholdUA.defense"
};
let lot = {
    id: "lot_id"
};
let bid = {
    id: "bid_id"
}

describe("aboveThresholdUA.defense", () => {
    describe("check_lot", () => {
        it("tender awards is empty array and tender has one bid - should return false.", () => {
            tender.bids = [{
                date: "2017-11-09T00:00:00Z",
                status: "active",
                lotValues: [{
                    relatedLot: lot.id
                }]
            }];
            tender.awards = [];
            assert.isFalse(tenders.check_lot(lot, tender));
        });

        it("tender has valid awards and one bid - should return true.", () => {
            tender.awards.push({
                lotID: lot.id
            });
            assert.isTrue(tenders.check_lot(lot, tender));
        });
        
        it("tender awards is empty array and tender has two bids - should return true.", () => {
            tender.bids.push(tender.bids[0]);
            tender.awards = [];
            assert.isTrue(tenders.check_lot(lot, tender));
        });

        it("tender bids is empty array - should return false.", () => {
            tender.bids = [];
            assert.isFalse(tenders.check_lot(lot, tender));
        });
    });

    describe("check_tender", () => {
        it("tender 'procurementMethodType' field is 'aboveThresholdUA.defense', 'numberOfBids' is less than '2' and no 'awards' - should return false.", () => {
            if ("awards" in tender) {
                delete tender.awards;
            }
            tender.numberOfBids = 1;
            tender.procurementMethodType = "aboveThresholdUA.defense";
            assert.isFalse(tenders.check_tender(tender));
        });

        it("tender 'procurementMethodType' field is 'aboveThresholdUA.defense', 'numberOfBids' is less than '2' and has 'awards' - should return true.", () => {
            tender.awards = undefined;
            assert.isTrue(tenders.check_tender(tender));
        });

        it("tender 'procurementMethodType' field is 'aboveThresholdUA.defense', 'numberOfBids' field is '2' and no 'awards' field - should return true.", () => {
            tender.numberOfBids = 2;
            delete tender.awards;
            assert.isTrue(tenders.check_tender(tender));
        });

        it("tender 'procurementMethodType' field is 'aboveThresholdUA.defense' and 'numberOfBids' field is '0' - should return false.", () => {
            tender.numberOfBids = 0;
            assert.isFalse(tenders.check_tender(tender));
        });
    });

    describe("get_bids", () => {
        it("should return filter_bids(tender.bids || [])", () => {
            tender.bids = [];
            assert.deepEqual(bids.get_bids(tender), bids.filter_bids(tender.bids || []));
            tender.bids = [{
                date: "2016-11-21T00:00:00Z",
                status: "cancelled"
            }];
            assert.deepEqual(bids.get_bids(tender), bids.filter_bids(tender.bids || []));
            tender.bids[0].status = "active";
            assert.deepEqual(bids.get_bids(tender), bids.filter_bids(tender.bids || []));
            tender.bids[0].date = "2017-11-21T00:00:00Z";
            assert.deepEqual(bids.get_bids(tender), bids.filter_bids(tender.bids || []));
        })
    });

    describe("check_bids_from_bt_atu", () => {
        it("should always return true", () => {
            assert.isTrue(bids.check_bids_from_bt_atu(tender, lot));
            assert.isTrue(bids.check_bids_from_bt_atu(tender));
        });
    });

    describe("check_tender_bids", () => {
        it("no awards in tender", () => {
            if ("awards" in tender) {
                delete tender.awards;
            }
            assert.strictEqual(bids.check_bids_from_bt_atu(tender), bids.check_tender_bids(tender));
            if ("lots" in tender) { 
                delete tender.lots;
            }
            tender.numberOfBids = 2;
            assert.strictEqual(bids.check_bids_from_bt_atu(tender), bids.check_tender_bids(tender));
        });
        it("awards in tender", () => {
            tender.awards = [];
            assert.isTrue(bids.check_tender_bids(tender));
        });
    });

    describe("check_lot_bids", () => {
        it("no awards", () => {
            assert.strictEqual(bids.check_bids_from_bt_atu(tender, lot), bids.check_lot_bids(tender, lot));
        });

        it("awards", () => {
            tender.awards = [{
                lotID: "not_lot_id"
            }];
            assert.strictEqual(bids.check_bids_from_bt_atu(tender, lot), bids.check_lot_bids(tender, lot));
            tender.awards[0].lotID = lot.id;
            assert.isTrue(bids.check_lot_bids(tender, lot));
        });
    });

    describe("check_award_and_qualification", () => {
        it("no lot", () => {
            assert.strictEqual(bids.check_award_for_bid(tender, bid), bids.check_award_and_qualification(tender, bid));
            tender.awards[0].bidID = bid.id;
            assert.strictEqual(bids.check_award_for_bid(tender, bid), bids.check_award_and_qualification(tender, bid));
            tender.awards[0].status = "active";
            assert.strictEqual(bids.check_award_for_bid(tender, bid), bids.check_award_and_qualification(tender, bid));
        });

        it("lot", () => {
            assert.strictEqual(bids.check_award_for_bid(tender, bid, lot), bids.check_award_and_qualification(tender, bid, lot));
        });
    });
});
