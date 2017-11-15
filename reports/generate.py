import argparse
import os
import csv
import sys
import itertools
import subprocess as sb
from datetime import datetime
from logging.config import fileConfig
from ConfigParser import ConfigParser

from reports.utilities.invoices import InvoicesUtility
from reports.utilities.refunds import RefundsUtility
from reports.utilities.bids import BidsUtility, HEADERS
from reports.utilities.tenders import TendersUtility
from reports.helpers import parse_period_string
from reports.log import getLogger
from reports.utilities.send import Porter
from reports.utilities.zip import compress


SCRIPTS = [BidsUtility, InvoicesUtility, TendersUtility, RefundsUtility]
YES = ['y', 'yes', 'true', 't']
NO = ['n', 'no', 'false', 'f']
DEFAULT_KINDS = ['general', 'special', 'defense', 'other', '_kind']
DEFAULT_INCLUDE = "bids,invoices,tenders,refunds"
CONFIG = ConfigParser()

parser = argparse.ArgumentParser(description="Openprocurement Billing")
parser.add_argument('-c', '--config', required=True)
parser.add_argument('--brokers', dest='brokers', action="store")
parser.add_argument('--period', dest='period', action='store')
parser.add_argument('--notify', action='store', default='no')
parser.add_argument('--timestamp', action='store')
parser.add_argument('--include', action='store', default=DEFAULT_INCLUDE)
parser.add_argument('--notify-brokers', action="append")
parser.add_argument('--timezone', default='Europe/Kiev')
ARGS = parser.parse_args()

INCLUDE = [op.strip() for op in ARGS.include.split(",")]
TIMESTAMP = ARGS.timestamp or datetime.now().strftime("%Y-%m-%d/%H-%M-%S-%f")
CONFIG.read(ARGS.config)
fileConfig(ARGS.config)

LOGGER = getLogger('BILLING')
PORTER = Porter(ARGS.config, TIMESTAMP, ARGS.notify_brokers)


def upload_and_notify(files):
    ctx = PORTER.upload_files(files)
    if ARGS.notify:
        PORTER.postman.send_emails(ctx)
    return ctx


def send_emails_from_existing_files():
    ctx = PORTER.create_emails_context_from_existing_prefix()
    if ARGS.notify:
        PORTER.postman.send_emails(ctx)
    return [entry['broker'] for entry in ctx]


def generate_for_broker(broker, period, timezone='Europe/Kiev'):
    utilities = map(lambda u: u(broker, period, ARGS.config, timezone),
                    SCRIPTS)
    for ut in utilities:
        if isinstance(ut, (TendersUtility, RefundsUtility)):
            ut.kinds = DEFAULT_KINDS
        ut.run()


def construct_filenames_of_generation(type, broker, period):
    start, end = period
    return "{}@{}--{}-{}.csv".format(broker, start, end, type)


def create_all_bids_csv(brokers, period):
    path = CONFIG.get('out', 'out_dir')
    files = [
        construct_filenames_of_generation('bids', broker, period)
        for broker in brokers
        if broker != 'all'
    ]
    all_file = "all@{0}--{1}-bids.csv".format(*period)
    with open(os.path.join(path, all_file), 'w') as out_stream:
        results_file = csv.writer(out_stream)
        results_file.writerow(HEADERS)
        for header, iterator in zip(
                (['after_2017-01-01'], ['after 2017-08-16']),
                (itertools.takewhile, itertools.dropwhile)
                ):
            results_file.writerow(header)
            for file in files:
                with open(os.path.join(path, file)) as broker_file:
                    reader = csv.reader(broker_file)
                    next(reader)
                    for line in iterator(
                            lambda line: line != ['after 2017-08-16'],
                            reader
                            ):
                        if line and line != header:
                            results_file.writerow(line)


def get_password_for_broker(broker):
    cmd = 'pass {}'.format(
        os.path.join(
            CONFIG.get('brokers_keys', 'path'),
            broker
            )
        )
    try:
        password = sb.check_output(cmd, shell=True)
        LOGGER.info("Got password for broker {}".format(broker))
        return password
    except Exception as e:
        LOGGER.fatal(
            "Command {} falied with error {}".format(cmd, e)
            )
        raise e


def zip_for_broker(
        broker,
        period,
        include=INCLUDE,
        ):
    start, end = period
    files = [
        construct_filenames_of_generation(type, broker, period)
        for type in include
    ]
    result_zip_name = "{}@{}--{}-{}.zip".format(
        broker, start, end, "-".join(include)
    )
    try:
        return compress(
            files,
            CONFIG.get('out', 'out_dir'),
            result_zip_name,
            get_password_for_broker(broker)
        )
    except (OSError, IOError) as e:
        LOGGER.fatal(
                "Falied to create archive {} for broker {}. Error: {}".format(
                    result_zip_name, broker, e
                    )
                )
        return None


def zip_all_tenders(brokers, period):
    start, end = period
    try:
        return compress(
            [
                "{}@{}--{}-{}.csv".format(broker, start, end, type)
                for type in ['tenders', 'refunds']
                for broker in brokers
                if brokers != 'all'
            ],
            CONFIG.get('out', 'out_dir'),
            "all@{}--{}-tenders.zip".format(start, end),
            None
        )
    except (OSError, IOError) as e:
        LOGGER.fatal("Error: {}".format(e))
        return None


def zip_all_bids(brokers, period):
    start, end = period
    files = ["all@{}--{}-bids.csv".format(start, end)]
    files.extend([
        "{}@{}--{}-invoices.csv".format(broker, start, end)
        for broker in brokers
        if broker != 'all'
    ])
    try:
        name = "all@{}--{}-bids.zip".format(start, end)
        return compress(
            files,
            CONFIG.get('out', 'out_dir'),
            name,
            get_password_for_broker('all')
        )
    except (OSError, IOError) as e:
        LOGGER.fatal(
            "Falied to create archive {} for broker {}. Error: {}".format(
                name, broker, e
                )
            )
        return None


def clean_up(files):
    for file in files:
        try:
            os.remove(file)
        except (OSError, IOError) as e:
            LOGGER.fatal("Error {} while removing file {}".format(e, file))


def run():
    period = parse_period_string(ARGS.period)
    if ARGS.timestamp:
        sent = send_emails_from_existing_files()
        if all(sent):
            LOGGER.warning(
                "Sent emails to {} from existing prefix {}".format(
                    sent, TIMESTAMP
                    )
                )
            sys.exit(0)
    if ARGS.brokers:
        brokers = [
            b.strip() for b in ARGS.brokers.split(',')
            if b.strip() != 'all'
        ]
    else:
        brokers = [
            item[0].strip() for item in CONFIG.items('brokers_emails')
            if item[0].strip() != 'all'
        ]
    LOGGER.warning("Started generation for {} between {} and {}".format(
        brokers, period[0], period[1])
        )
    LOGGER.warning("Archive content: {}".format(INCLUDE))
    LOGGER.warning("Timestamp: {}".format(TIMESTAMP))

    for broker in brokers:
        generate_for_broker(broker, period, ARGS.config)
        zip_file_path = zip_for_broker(broker, period)
        sent = upload_and_notify([zip_file_path])
    create_all_bids_csv(brokers, period)

    results = upload_and_notify([
        zip_all_tenders(brokers, period),
        zip_all_bids(brokers, period)
        ])
    if results:
        clean_up()
