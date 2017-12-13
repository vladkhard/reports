"use strict";

let tenders = require("../../design/lib/tenders");
let assert = require("../../../src/node_modules/chai").assert;

describe("tenders view tests", () => {
    describe("find_first_revision_date", () => {
        let doc = {};

        it("no revisions - should return empty string.", () => {
            doc.revisions = undefined;
            assert.strictEqual(tenders.find_first_revision_date(doc), "");
        });

        it("revisions are empty array - should return empty string.", () => {
            doc.revisions = [];
            assert.strictEqual(tenders.find_first_revision_date(doc), "");
        });

        it("first revision has no date - should return empty string.", () => {
            doc.revisions = [{}];
            assert.strictEqual(tenders.find_first_revision_date(doc), "");    
        });

        it("everything is ok - should return date.", () => {
            let date = "2016-04-01T00:00:00+03:00";
            doc.revisions = [{date: date}];
            assert.strictEqual(tenders.find_first_revision_date(doc), date);
        });
    });

    describe("count_lot_bids", () => {
        let lot, bids;

        it("bids are undefined - should return 0.", () => {
            assert.strictEqual(tenders.count_lot_bids(lot, bids), 0);
        });

        bids = [];

        it("bids are empty array - should return 0.", () => {
            assert.strictEqual(tenders.count_lot_bids(lot, bids), 0);
        })

        lot = {
            id: "lot_id"
        }

        it("no related lots - should return 0.", () => {
            bids.push({
                lotValues: [{
                    relatedLot: "not_lot_id"
                }]
            });
            assert.strictEqual(tenders.count_lot_bids(lot, bids), 0);
        });

        it("one related lot - should return 1", () => {
            bids.push({
                lotValues: [{
                    relatedLot: lot.id
                }]
            });
            assert.strictEqual(tenders.count_lot_bids(lot, bids), 1);
        });

        it("two related lots - should return 2", () => {
            bids[0].lotValues.push({
                relatedLot: lot.id
            });
            assert.strictEqual(tenders.count_lot_bids(lot, bids), 2);
        });
    });

    describe("filter_bids", () => {
        let bids = [];

        it("bids are empty array - should return empty array.", () => {
            assert.deepEqual(bids, tenders.filter_bids(bids));
        });

        it("bid status is not active - should return empty array.", () => {
            bids.push({
                date: "2017-11-02T00:00:00Z",
                status: ""
            });
        
            assert.deepEqual([], tenders.filter_bids(bids));
        });

        it("bid date is earlier then minimal date - should return empty array.", () => {
            // min_date is 2016-04-01T00:00:00+03:00
            bids.push({
                date: "2015-11-02T00:00:00Z",
                status: "active"
            });
            assert.deepEqual([], tenders.filter_bids(bids));
        })

        it("bid date is later then minimal date and status is active - should return array containing this bid.", () => {
            bids.push({
                date: "2017-11-02T00:00:00Z",
                status: "active"
            });    
            assert.deepEqual([bids[2]], tenders.filter_bids(bids));
        });

    });

    describe("count_lot_qualifications", () => {
        let qualifications;
        let lot_id = "lot_id";

        it("qualifications are undefined - should return 0.", () => {
            assert.strictEqual(tenders.count_lot_qualifications(qualifications, lot_id), 0);
        });

        it("qualifications are empty array - should return 0.", () => {
            qualifications = [];
            assert.strictEqual(tenders.count_lot_qualifications(qualifications, lot_id), 0);
        });

        it("lots ids are not related - should return 0.", () => {
            qualifications.push({
                lotID: "not_lot_id"
            });
            assert.strictEqual(tenders.count_lot_qualifications(qualifications, lot_id), 0);
        });

        it("qualification is related to lot - should return 1.", () => {
            qualifications.push({
                lotID: lot_id
            });
            assert.strictEqual(tenders.count_lot_qualifications(qualifications, lot_id), 1);
        })
    });

    describe("max_date", () => {
        let obj = {};
        
        it("no dates in object - should return invalid Date.", () => {
            assert.isNaN(tenders.max_date(obj).getTime());
        });

        it("obj date is valid - should return date.", () => {
            obj.date = "2017-11-02T00:00:00Z";
            assert.deepEqual(tenders.max_date(obj), new Date(obj.date));
        });

        it("obj date and obj documents are valid - should return max date.", () => {
            obj.documents = [{
                datePublished: "2017-11-03T00:00:00Z"
            }];
            let max_date = Math.max.apply(null, [new Date(obj.date), new Date(obj.documents[0].datePublished)]);
            assert.strictEqual(tenders.max_date(obj).getTime(), max_date);
        });
    });

    describe("find_complaint_date", () => {
        let complaints = [];

        it("complaints are empty array - should return invalid Date.", () => {
            assert.isNaN(tenders.find_complaint_date(complaints).getTime());
        });

        it("complaint type is not claim and dateDecision is undefined - should return invalid Date.", () => {
            complaints.push({});
            assert.isNaN(tenders.find_complaint_date(complaints).getTime());
        });

        it("complaint type is not claim and dateDecision is valid - should return dateDecision.", () => {
            complaints[0].dateDecision = "2017-11-02T00:00:00Z";
            assert.deepEqual(tenders.find_complaint_date(complaints), new Date(complaints[0].dateDecision));
        });

        it("comlaint type is claim and dateAnswered is undefined - should return invalid Date.", () => {
            complaints[0].type = "claim";
            assert.isNaN(tenders.find_complaint_date(complaints).getTime());
        });

        it("complaint type is claim and dateAnswered is valid - should return dateAnswered", () => {
            complaints[0].dateAnswered = "2017-11-02T00:00:00Z";
            assert.deepEqual(tenders.find_complaint_date(complaints), new Date(complaints[0].dateAnswered));
        });

        it("two dates are valid - should return later of them.", () => {
            complaints = [
                {
                    type: "claim",
                    dateAnswered: "2017-11-02T00:00:00Z"
                },
                {
                    type: "claim",
                    dateAnswered: "2017-11-03T00:00:00Z"
                }
            ];
            let max_date = Math.max.apply(null, [new Date(complaints[0].dateAnswered), new Date(complaints[1].dateAnswered)]);
            assert.deepEqual(tenders.find_complaint_date(complaints).getTime(), max_date);
        });
    });

    describe("find_cancellation_max_date", () => {
        let cancellations;
        it("cancellations are undefined - should return null.", () => {
            assert.isNull(tenders.find_cancellation_max_date(cancellations)); 
        });

        it("cancellations are empty array - should return null.", () => {
            cancellations = [];
            assert.isNull(tenders.find_cancellation_max_date(cancellations));
        });

        it("one valid cancellation - should return cancellation date.", () => {
            cancellations = [{
                date: "2017-11-02T00:00:00+03:00"
            }];
            assert.deepEqual(new Date(cancellations[0].date), tenders.find_cancellation_max_date(cancellations));
        });

        it("cancellations have two dates - should return earlier of them.", () => {
            cancellations.push({
                date: "2017-11-03T00:00:00+03:00"
            });
            assert.deepEqual(new Date(cancellations[0].date), tenders.find_cancellation_max_date(cancellations));
        });
    });

    describe("find_awards_max_date", () => {
        let awards;
        it("awards are undefined - should return null.", () => {
            assert.isNull(tenders.find_awards_max_date(awards));
        });

        it("awards are empty array - should return null.", () => {
            awards = [];
            assert.isNull(tenders.find_awards_max_date(awards));
        });

        it("award has no complaints - should return award.complaintPeriod.endDate.", () => {
            awards.push({
                complaintPeriod: {
                    endDate: "2017-11-02T00:00:00+03:00"
                }
            });
            assert.deepEqual(new Date(awards[0].complaintPeriod.endDate), tenders.find_awards_max_date(awards));
        });

        it("award has complaints but complaint date hasn't finded - should return award.complaintPeriod.endDate.", () => {
            awards[0].complaints = [];
            assert.deepEqual(new Date(awards[0].complaintPeriod.endDate), tenders.find_awards_max_date(awards));
        });

        it("award has complaints and complaint date is finded - should return later date.", () => {
            awards[0].complaints.push({
                type: "",
                dateDecision: "2017-11-03T00:00:00+03:00"
            });
            let max_date = Math.max.apply(null, [new Date(awards[0].complaintPeriod.endDate), new Date(awards[0].complaints[0].dateDecision)]);
            assert.deepEqual(max_date, tenders.find_awards_max_date(awards).getTime());
        });
    });

    describe("Handler", () => {
        let tender;
        let bids_disclojure_date;

        it("tender has no date and status is undefined - should return null.", () => {
            tender = {};
            assert.isNull(new tenders.Handler(tender).tender_date);
        });

        it("tender has date but status is undefined - should return null.", () => {
            tender.date = "2017-11-02T00:00:00+03:00";
            assert.isNull(new tenders.Handler(tender).tender_date);
        });

        it("tender has date and status is complete - should return tender date.", () => {
            tender.status = "complete";
            assert.deepEqual(new tenders.Handler(tender).tender_date, new Date(tender.date));
        });

        it("tender has date and status is unsuccessful - should return tender date.", () => {
            tender.status = "unsuccessful";
            assert.deepEqual(new tenders.Handler(tender).tender_date, new Date(tender.date));
        });


        it("tender has date and status is cancelled but date is earlier than bids disclojure date - should return null.", () => {
            tender.qualificationPeriod = {
                startDate: "2017-01-01T00:00:00Z"
            };
            bids_disclojure_date = tender.qualificationPeriod.startDate;
            tender.status = "cancelled";
            tender.date = bids_disclojure_date.substring(0, 3) + (bids_disclojure_date[3] - 1) + bids_disclojure_date.substring(4);
            assert.isNull(new tenders.Handler(tender).tender_date);
        });

        it("tender has date and status is cancelled and date is later than bids disclojure date - should return tender date.", () => {
            tender.status = "cancelled";
            tender.date = bids_disclojure_date.substring(0, 3) + (bids_disclojure_date[3] + 1) + bids_disclojure_date.substring(4);
            assert.deepEqual(new Date(tender.date), new tenders.Handler(tender).tender_date);
        });

        it("tender hasn't date and status is complete but tender hasn't contracts - should return invalid Date.", () => {
            delete tender.date;
            tender.status = "complete";
            assert.isNaN(new tenders.Handler(tender).tender_date.getTime());
        });

        it("tender hasn't date and status is complete and tender has contracts with valid date - should return the latest contracts date.", () => {
            tender.status = "complete";
            tender.contracts = [
                {
                    status: "active",
                    date: "2017-11-02T00:00:00Z"
                },
                {
                    status: "active",
                    date: "2017-11-03T00:00:00Z"
                }
            ];
            let max_date = Math.max.apply(null, tender.contracts.map((c) => { return new Date(c.date); }));

            assert.deepEqual(new tenders.Handler(tender).tender_date.getTime(), max_date);
        });

        it("tender hasn't date and status is unsuccessful but tender hasn't awards - should return null.", () => {
            tender.status = "unsuccessful";
            assert.isNull(new tenders.Handler(tender).tender_date);
        });

        it("tender hasn't date and status is unsuccessful, tender has awards field with valid date - should return the latest awards date.", () => {
            tender.awards = [{
                complaintPeriod: {
                    endDate: "2017-11-02T00:00:00Z"
                },
                complaintPeriod: {
                    endDate: "2017-11-03T00:00:00Z"
                }
            }];
            let max_date = Math.max.apply(null, tender.awards.map((c) => { return new Date (c.complaintPeriod.endDate); }));
            assert.deepEqual(new tenders.Handler(tender).tender_date.getTime(), max_date);
        });
        
        it("tender hasn't date and status is cancelled but tender cancellations is empty array - should return null.", () => {
            tender.status = "cancelled";
            tender.cancellations = [];
            assert.isNull(new tenders.Handler(tender).tender_date);
        });

        it("tender hasn't date and status is cancelled, tender has cancellations with valid date - should return the latest cancellations date.", () => {
            tender.status = "cancelled";
            tender.cancellations = [
                {
                    date: bids_disclojure_date.substring(0, 3) + (bids_disclojure_date[3] + 1) + bids_disclojure_date.substring(4),
                    status: "active",
                    cancellationOf: "tender"
                }
            ];
            assert.deepEqual(new Date(tender.cancellations[0].date), new tenders.Handler(tender).tender_date);
        });
    });

    describe("lotHandler", () => {
        let lot, tender, bids_disclojure_date;

        it("lot and tender statuses are undefined and lot has no date - should return null.", () => {
            lot = {};
            tender = {};
            assert.isNull(new tenders.lotHandler(lot, tender).lot_date);
        });
        
        it("lot has no status and lot date is undefined, lot has status cancelled and has valid date - should return tender date.", () => {
            lot.date = undefined;
            tender.status = "cancelled";
            tender.date = "2017-11-06T00:00:00+03:00";
            assert.deepEqual(new Date(tender.date), new tenders.lotHandler(lot, tender).lot_date);
        });
        
        it("lot status is complete and lot date is valid - should return lot date.", () => {
            lot.date = "2017-11-06T00:00:00+03:00";
            lot.status = "complete";
            assert.deepEqual(new Date(lot.date), new tenders.lotHandler(lot, tender).lot_date);
        });

        it("lot status is unsuccessful and lot date is valid - should return lot date.", () => {
            lot.status = "unsuccessful";
            assert.deepEqual(new Date(lot.date), new tenders.lotHandler(lot, tender).lot_date);
        });

        it("lot status is undefined and lot date is valid - should return lot date.", () => {
            lot.status = undefined;
            assert.deepEqual(new Date(lot.date), new tenders.lotHandler(lot, tender).lot_date);
        });

        it("lot status is cancelled and lot date is earlier then bids disclojure date - should return null.", () => {
            tender.qualificationPeriod = {
                startDate: "2017-01-01T00:00:00Z"
            };
            bids_disclojure_date = tender.qualificationPeriod.startDate;
            lot.status = "cancelled";
            lot.date = bids_disclojure_date.substring(0, 3) + (bids_disclojure_date[3] - 1) + bids_disclojure_date.substring(4);
            assert.isNull(new tenders.lotHandler(lot, tender).lot_date);
        });

        it("lot status is cancelled and lot date is later then bids disclojure date - should return lot date.", () => {
            lot.status = "cancelled"
            lot.date = bids_disclojure_date.substring(0, 3) + (bids_disclojure_date[3] + 1) + bids_disclojure_date.substring(4);
            assert.deepEqual(new Date(lot.date), new tenders.lotHandler(lot, tender).lot_date);
        });


        it("lot status is unsuccessful, lot has no date - should return the result of find_awards_max_date. (tender awards is fine)", () => {
            delete lot.date;
            lot.id = "lot_id";
        
            lot.status = "unsuccessful";
            tender.awards = [{
                complaintPeriod: {
                    endDate: "2017-11-09T00:00:00+03:00"
                },
                lotID: lot.id
            }];
            assert.deepEqual(tenders.find_awards_max_date(tender.awards), new tenders.lotHandler(lot, tender).lot_date);
        });

        it("lot status is cancelled, lot has no date - should return the result of find_cancellation_max_date. (tender cancellations is fine)", () => {
            lot.status = "cancelled";
            tender.cancellations = [{
                date: "2017-11-09T00:00:00+03:00",
                status: "active",
                cancellationOf: "lot",
                relatedLot: lot.id
            }];
            assert.deepEqual(tenders.find_cancellation_max_date(tender.cancellations), new tenders.lotHandler(lot, tender).lot_date);
        });

        it("lot status is complete, lot has no date - should return the result of max_date. (tender contracts is fine)", () => {
            lot.status = "complete";
            tender.awards[0].id = lot.id;
            tender.contracts = [{
                status: "active",
                date: "2017-11-09T00:00:00+03:00",
                awardID: lot.id
            }]; 
            assert.deepEqual(tenders.max_date(tender.contracts[0]), new tenders.lotHandler(lot, tender).lot_date);
        });

        it("lot status is udnefined, tender status is cancelled", () => {
            lot.status = undefined;
            tender.status = "cancelled";
            let Handler = new tenders.Handler(tender);
            if (Handler.tender_date !== null) {
                if (Handler.tender_date > Handler.bids_disclosure_standstill) {
                    it("Handler.tender_date is later then bids disclojure date - should return Handler.tender_date", () => {
                        assert.deepEqual(Handler.tender_date, new tenders.lotHandler(lot, tender).lot_date);
                    });
                } else {
                    it("Handler.tender_date is earlier then bids disclojure date - should return null.", () => {
                        assert.isNull(new tenders.lotHandler(lot, tender).lot_date);
                    });
                }
            } else {
                it("Handler.tender_date is null - should return null.", () => {
                    assert.isNull(new tenders.lotHandler(lot, tender).lot_date);
                });
            }
        });

        it("lot status and tender status is undefined - should return the result of max_date. (tender contracts is fine)", () => {
            tender.status = undefined;
            lot.status = undefined;
            assert.deepEqual(tenders.max_date(tender.contracts[0]), new tenders.lotHandler(lot, tender).lot_date);
        });
    });

    describe("get_contract_date", () => {
        let tender;

        it("tender has no 'contracts' field - should return empty string.", () => {
            tender = {};
            assert.strictEqual(tenders.get_contract_date(tender), "");
        });

        it("tender has no contracts in status 'active' - should return empty string.", () => {
            tender.contracts = [{
                status: undefined,
                date: "2017-11-09T00:00:00Z"
            }];
            assert.strictEqual(tenders.get_contract_date(tender), "");
        });

        it("tender has contract in status 'active' - should return contract.date", () => {
            tender.contracts[0].status = "active"; 
            assert.deepEqual(tender.contracts[0].date, tenders.get_contract_date(tender));
        });
    });

    describe("get_contract_date_for_lot", () => {
        let lot, tender;
        
        it("tender has no 'awards' field - should return false", () => {
            lot = {id: "lot_id"};
            tender = {
                contracts: [{
                    status: "active",
                    date: "2017-11-09T00:00:00Z",
                    awardID: "award_id"
                }]
            };

            assert.strictEqual(tenders.get_contract_date_for_lot(tender, lot), "");
        });

        it("tender has valid award - should return contract date.", () => {
            tender.awards = [{
                id: "award_id",
                lotID: "lot_id"
            }];

            assert.strictEqual(tender.contracts[0].date, tenders.get_contract_date_for_lot(tender, lot));
        });
    });

    describe("find_date_from_revisions", () => {
        let lot, tender;

        it("no awards and no revisions - should return undefined.", () => {
            lot = {
                id: "lot_id"
            }
        
            tender = {
                awards: [],
                revisions: []
            };
            
            assert.isUndefined(tenders.find_date_from_revisions(tender));
        });

        it("valid awards and no revisions - should return award date.", () => {
            tender.awards.push({
                status: "active",
                date: "2017-11-09T00:00:00Z"
            });

            assert.strictEqual(tender.awards[0].date, tenders.find_date_from_revisions(tender));
        });
        
        it("no valid awards and no revisions - should return undefined.", () => {
            tender.awards[0].lotID = "not_lot_id";
            assert.isUndefined(tenders.find_date_from_revisions(tender, lot));
        });
        
        it("valid awards and no revisions - should return award date.", () => {
            tender.awards[0].lotID = "lot_id";
            assert.strictEqual(tender.awards[0].date, tenders.find_date_from_revisions(tender, lot));
        });
        
        it("valid awards and revisions didn't changed awards - should return award date.", () => {
            tender.revisions = [{
                date: "2017-11-09T00:30:00Z",
                changes: [{
                    path: "/something",
                    op: "remove"
                }]
            },
            {
                date: "2017-11-09T01:00:00Z",
                changes: [{
                    path: "/numberOfBids",
                    op: "add",
                    value: 0
                }]
            }];

            assert.strictEqual(tender.awards[0].date, tenders.find_date_from_revisions(tender));
        });

        it("valid awards and revisions changed awards dates, but new date is later then actual - should return actual date.", () => {
            tender.revisions.push({
                date: "2017-11-10T00:00:00Z",
                changes: [{
                    path: "/awards/0/date",
                    op: "replace",
                    value: "2017-11-10T00:00:00Z"
                }]
            });

            assert.strictEqual(tender.awards[0].date, tenders.find_date_from_revisions(tender));
        });

        it("valid awards and revisions changed awards dates, and new date is earlier then actual - should return new date.", () => {
            tender.revisions[2].changes[0].value = "2017-11-08T00:00:00Z";
            assert.strictEqual(tender.revisions[2].changes[0].value, tenders.find_date_from_revisions(tender, lot));
        });

        it("valid awards and revisions changed awards dates, but 'lotID' doesn't match lot id - should return actual date.", () => {
            tender.revisions[2].changes.push({
                path: "/awards/0/lotID",
                op: "replace",
                value: "not_lot_id"
            });

            assert.strictEqual(tender.awards[0].date, tenders.find_date_from_revisions(tender, lot));
        });

        it("valid awards and revisions changed awards dates, 'lotID' matches lot id and new date is earlier then actual - should return new date.", () => {
            tender.revisions[2].changes[1].value = "lot_id";
            assert.strictEqual(tender.revisions[2].changes[0].value, tenders.find_date_from_revisions(tender, lot));
        });
    });

    describe("get_first_award_date", () => {
        let tender, lot;
        it("tender awards is empty array - should return null.", () => {
            tender = {
                awards: []
            };

            assert.isNull(tenders.get_first_award_date(tender));
        });

        it("tender awards are only unsuccessful or pending - should return null.", () => {
            tender.awards.push({
                status: "unsuccessful"
            },
            {
                status: "pending"
            });

            assert.isNull(tenders.get_first_award_date(tender));
        });

        it("tender has one complete award - should return this award date.", () => {
            tender.awards.push({
                status: "complete",
                date: "2017-11-10T00:00:00Z"
            });
            
            assert.strictEqual(tender.awards[2].date, tenders.get_first_award_date(tender));
        });

        it("tender has one cancelled and one active award - should return active award date.", () => {
            tender = {
                awards: [{
                    status: "cancelled",
                    date: "2017-11-09T00:00:00Z"
                },
                {
                    status: "active",
                    date: "2017-11-10T00:00:00Z"
                }],
                revisions: []
            };

            assert.strictEqual(tender.awards[1].date, tenders.get_first_award_date(tender));
        });

        it("tender awards 'lotID's don't match lot id - should return null.", () => {
            lot = {
                id: "lot_id"
            };
            tender.awards.forEach(function(award) {
                award.lotID = "not_lot_id";
            });

            assert.isNull(tenders.get_first_award_date(tender, lot));
        });

        it("tender has one cancelled and one active award, awards 'lotID's match lot id - should return active award date.", () => {
            tender.awards.forEach(function(award) {
                award.lotID = "lot_id";
            });

            assert.strictEqual(tender.awards[1].date, tenders.get_first_award_date(tender));
        });
    });
});
