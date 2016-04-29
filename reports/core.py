import couchdb
import couchdb.design
import os.path
import csv
import os
import os.path
import sys
from config import Config, create_db_url
from design import bids_owner_date, tenders_owner_date

from argparse import ArgumentParser
from dateparser import parse
from couchdb.http import ResourceNotFound
from couchdb.design import ViewDefinition


views = [bids_owner_date, tenders_owner_date]



OWNERS = {
    "smarttender": "it.ua",
    "dzo": "netcast.com.ua",
    "privatmarket": "privatmarket.ua",
    "prom": "prom.ua",
    "etender": "e-tender.biz",
    "publicbid": "public-bid.com.ua",
    "newtend": "newtend.com",
}



class ReportUtility():

    def __init__(self, operation, rev=False):
        self.rev = rev
        self.headers = None
        self.operation = operation

    def init_from_args(self, owner, period, config=None):
        self.owner = owner
        self.config = Config(config)
        self.start_date = ''
        self.end_date = ''

        if period:
            if len(period) == 1:
                self.start_date = parse(period[0]).isoformat()
            if len(period) == 2:
                self.start_date = parse(period[0]).isoformat()
                self.end_date = parse(period[1]).isoformat()
        self.get_db_connection()
        self.thresholds = self.config.get_thresholds()
        self.payments = self.config.get_payments(self.rev)

    def get_db_connection(self):
        host = self.config.get_option('db', 'host')
        port = self.config.get_option('db', 'port')
        user_name = self.config.get_option('user', 'username')
        user_password = self.config.get_option('user', 'password')

        db_name = self.config.get_option('db', 'name')
        couch_url = create_db_url(host, port, user_name, user_password, db_name)

        self.db = couchdb.Database(couch_url)

        a_name = self.config.get_option('admin', 'username')
        a_password = self.config.get_option('admin', 'password')


	self.adb = couchdb.Database(create_db_url(host, port, a_name, a_password, db_name))








    def row(self):
        raise NotImplemented

    def rows(self):
        raise NotImplemented


    def get_payment(self, value):
        index = 0
        for th in self.thresholds:
            if value <= th:
                return self.payments[index]
            index += 1
        return self.payments[-1]

    def _sync_views(self):
	
        ViewDefinition.sync_many(self.adb, views)
        
        

    def get_response(self):
        self._sync_views()

	if not self.view:
	    raise NotImplemented

        if not self.start_date and  not self.end_date:
            self.response = self.db.iterview(self.view, 1000, startkey=(self.owner, ""), endkey=(self.owner, "9999-12-30T00:00:00.000000+03:00")) 
        elif self.start_date and not self.end_date:
            self.response = self.db.iterview(self.view, 1000, startkey=(self.owner, self.start_date), endkey=(self.owner, "9999-12-30T00:00:00.000000+03:00"))
        else:
            self.response = self.db.iterview(self.view, 1000, startkey=(self.owner, self.start_date), endkey=(self.owner, self.end_date))
            

    def out_name(self):
        name = self.owner + "@" + self.start_date + "--" \
               + self.end_date +"-"+ self.operation+ ".csv"

        self.put_path = os.path.join(self.config.get_out_path(), name)

    def write_csv(self):
        if not self.headers:
            raise ValueError
        with open(self.put_path, 'w') as out_file:
            writer = csv.writer(out_file)
            writer.writerow(self.headers)
            for row in self.rows():
                writer.writerow(row)

    def run(self):
        self.get_response()
        self.out_name()
        self.write_csv()






def thresholds_headers(thresholds):
    prev_threshold = None
    result = []
    threshold = []
    for t in thresholds:
        threshold.append(str(t/1000))
    for t in threshold:
        if not prev_threshold:
            result.append("<= " + t)
        else:
            result.append(">" + prev_threshold + "<=" + t)
        prev_threshold = t
    result.append(">" + threshold[-1])
    return result

def parse_args():
    parser = ArgumentParser()
    parser.add_argument('-o', '--owner', dest='owner',  required=True)
    parser.add_argument('-c', '--config', dest='config', required=False, default='~/.config/reports/reports.ini')
    parser.add_argument('-p', '--period', nargs='+', dest='period', default=[])
    args = parser.parse_args()
    return args.owner.strip(), args.period, args.config
   
