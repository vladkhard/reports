import couchdb.design
import os
basepath = os.path.dirname(__file__)


with open(os.path.join(basepath, 'design/bids.js')) as bids_file:
    bids = bids_file.read()

with open(os.path.join(basepath, 'design/tenders.js')) as tenders_file:
    tenders = tenders_file.read()

with open(os.path.join(basepath, 'design/lib/jsonpatch.js')) as jsonp:
    jsonpatch = jsonp.read()

with open(os.path.join(basepath, 'design/lib/tenders.js')) as tl:
    tenders_lib = tl.read()

with open(os.path.join(basepath, 'design/lib/bids.js')) as bl:
    bids_lib = bl.read()

bids_owner_date = couchdb.design.ViewDefinition(
    'report', 'bids_owner_date', bids
)
tenders_owner_date = couchdb.design.ViewDefinition(
    'report', 'tenders_owner_date', tenders
)
