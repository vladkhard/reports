"use strict";

let tenders = require("../../design/lib/tenders");
let bids = require("../../design/lib/bids");
let assert = require("../../../src/node_modules/chai").assert;

let tender = {
    procurementMethodType: "competitiveDialogueUA.stage2"
};
let lot = {
    id: "lot_id"
};
let bid = {
    id: "bid_id"
}

describe("competitiveDialogueUA.stage2", () => {
    describe("check_lot", () => {
        it("should return count_lot_bids(lot, filter_bids(tender.bids || []) > 1", () => {
            assert.strictEqual(tenders.count_lot_bids(lot, tenders.filter_bids(tender.bids || [])) > 1, tenders.check_lot(tender, lot));

            tender.bids = [
                {
                    date: "2017-11-20T00:00:00Z",
                    lotValues: [{
                        relatedLot: lot.id
                    }]
                },
                {
                    date: "2017-11-20T00:00:00Z",
                    lotValues: [{
                        relatedLot: "not_lot_id"
                    }]      
                }
            ];

            assert.strictEqual(tenders.count_lot_bids(lot, tenders.filter_bids(tender.bids || [])) > 1, tenders.check_lot(tender, lot));

            tender.bids.push({
                date: "2017-11-20T00:00:00Z",
                lotValues: [{
                    relatedLot: lot.id
                }]
            });

            assert.strictEqual(tenders.count_lot_bids(lot, tenders.filter_bids(tender.bids || [])) > 1, tenders.check_lot(tender, lot));
        });
    });

    describe("check_tender", () => {
        it("should return tender.numberOfBids > 1", () => {
            tender.numberOfBids = 0;
            assert.strictEqual(tender.numberOfBids > 1, tenders.check_tender(tender));
            tender.numberOfBids = 1;
            assert.strictEqual(tender.numberOfBids > 1, tenders.check_tender(tender));
            tender.numberOfBids = 2;
            assert.strictEqual(tender.numberOfBids > 1, tenders.check_tender(tender));
        });
    });

    describe("get_bids", () => {
        it("should return filter_bids(tender.bids).", () => {
            tender.bids = [
                {
                    date: "2016-11-13T00:00:00Z",
                    status: "active",
                },
                {
                    date: "2016-11-13T00:00:00Z",
                    status: "invalid.pre-qualification",
                },
                {
                    date: "2017-11-13T00:00:00Z",
                    status: "cancelled",
                },
                {
                    date: "2017-11-13T00:00:00Z",
                    status: "active",
                },
                {
                    date: "2017-11-13T00:00:00Z",
                    status: "invalid.pre-qualification",
                }
            ];
            assert.deepEqual(bids.get_bids(tender), bids.filter_bids(tender.bids));
        });
    });

    describe("check_bids_from_bt_atu", () => {
        it("should always return false", () => {
            assert.isFalse(bids.check_bids_from_bt_atu(tender));
            assert.isFalse(bids.check_bids_from_bt_atu(tender, lot));
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
