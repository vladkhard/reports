"use strict";

let tenders = require("../../design/lib/tenders");
let bids = require("../../design/lib/bids");
let assert = require("../../../node_modules/chai").assert;

let tender = {
    procurementMethodType: "competitiveDialogueUA"
};
let lot = {
    id: "lot_id"
};
let bid = {
    id: "bid_id"
}

describe("competitiveDialogueUA", () => {
    describe("check_lot", () => {
        it("should return count_lot_qualifications((tender.qualifications || []), lot.id) > 2", () => {
            if ("qualifications" in tender) {
                delete tender.qualifications;
            }
            assert.strictEqual(tenders.count_lot_qualifications((tender.qualifications || []), lot.id) > 2, tenders.check_lot(lot, tender));
            tender.qualifications = [{
                lotID: lot.id
            }];
            assert.strictEqual(tenders.count_lot_qualifications((tender.qualifications || []), lot.id) > 2, tenders.check_lot(lot, tender));
            tender.qualifications.push(tender.qualifications[0], tender.qualifications[0]);
            assert.strictEqual(tenders.count_lot_qualifications((tender.qualifications || []), lot.id) > 2, tenders.check_lot(lot, tender));
        });
    });

    describe("check_tender", () => {
        it("should return (tender.qualifiactions || []).length > 2", () => {
            tender.qualifications = [];
            assert.isFalse(tenders.check_tender(tender));
            tender.qualifications = [null, null, null];
            assert.isTrue(tenders.check_tender(tender));
        })
    });

    describe("get_bids", () => {
        it("should return get_eu_tender_bids(tender)", () => {
            tender.qualifications = [];
            tender.bids = [];
            assert.deepEqual(bids.get_eu_tender_bids(tender), bids.get_bids(tender));
            tender.qualifications.push({
                bidID: "not_bid_id"
            });
            tender.bids.push({
                id: bid.id
            });
            assert.deepEqual(bids.get_eu_tender_bids(tender), bids.get_bids(tender));
            tender.qualifications[0].bidID = bid.id;
            assert.deepEqual(bids.get_eu_tender_bids(tender), bids.get_bids(tender));
        });
    });

    describe("check_bids_from_bt_atu", () => {
        it("should always return false", () => {
            assert.isFalse(bids.check_bids_from_bt_atu(tender));
            assert.isFalse(bids.check_bids_from_bt_atu(tender, lot));
        });
    });

    describe("check_tender_bids", () => {
        it("should return (tender.qualifications || []).length >= 2", () => {
            tender.qualifications = [];
            assert.isFalse(bids.check_tender_bids(tender));
            tender.qualifications = [null];
            assert.isFalse(bids.check_tender_bids(tender));
            tender.qualifications.push(null, null);
            assert.isTrue(bids.check_tender_bids(tender));
        });
    });


    describe("check_lot_bids", () => {
        it("should return count_lot_qualifications(tender.qualifications, lot) >= 2", () => {
            lot.status = "cancelled";
            tender.qualifications = [];
            assert.strictEqual(bids.count_lot_qualifications(tender.qualifications, lot) >= 2, bids.check_lot_bids(tender, lot));
            tender.qualifications = [
                {
                    lotID: lot.id,
                    status: "active"
                },
                {
                    lotID: "not_lot_id",
                    status: "active"
                },
                {
                    lotID: lot.id,
                    status: ""
                }
            ];
            assert.strictEqual(bids.count_lot_qualifications(tender.qualifications, lot) >= 2, bids.check_lot_bids(tender, lot));
            tender.qualifications.push(tender.qualifications[0], tender.qualifications[0]);
            assert.strictEqual(bids.count_lot_qualifications(tender.qualifications, lot) >= 2, bids.check_lot_bids(tender, lot));
            lot.status = "active";
            assert.strictEqual(bids.count_lot_qualifications(tender.qualifications, lot) >= 2, bids.check_lot_bids(tender, lot));
            tender.qualifications.push(tender.qualifications[0]);
            assert.strictEqual(bids.count_lot_qualifications(tender.qualifications, lot) >= 2, bids.check_lot_bids(tender, lot));
        });
    });

    describe("check_award_and_qualification", () => {
        it("should return check_qualification_for_EU_bid", () => {
            lot.status = "unsuccessful";
            tender.qualifications = [{
                bidID: bid.id,
                lotID: lot.id,
                status: "active"
            }];
            assert.strictEqual(bids.check_qualification_for_EU_bid(tender, bid, lot), bids.check_award_and_qualification(tender, bid, lot));
        });
    });
});
