import argparse
import os
import csv
from datetime import datetime
from ConfigParser import ConfigParser
from reports.utilities.invoices import run as run_invoices
from reports.utilities.refunds import run as run_refunds
from reports.utilities.bids import run as run_bids
from reports.utilities.tenders import run as run_tenders
from reports.utilities.send import run as run_send
from reports.utilities.zip import run as run_zip

PATH = os.path.join(os.getcwd(), 'var/reports')


def get_argument_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-c',
        '--config',
        dest='config',
        required=True
    )
    parser.add_argument(
        '-b',
        '--brokers',
        dest='brokers',
        nargs='+'
    )
    parser.add_argument(
        '-p',
        '--period',
        dest='period',
        nargs='+'
    )
    parser.add_argument(
        '-n',
        '--notify',
    )
    parser.add_argument(
        '--notify-brokers',
        dest='notify_brokers',
        nargs='+'
    )
    parser.add_argument(
        '-t',
        '--timezone',
        dest='timezone',
        default='Europe/Kiev',
        help='Timezone. Default "Europe/Kiev"'
    )
    return parser


def generate_for_broker(*args):
    run_bids(*args)
    run_invoices(*args)
    run_tenders(*args)
    run_refunds(*args)


def get_period():
    now = datetime.now()
    start = "{}-{}-{}".format(now.year, now.month - 1, 01)
    end = "{}-{}-{}".format(now.year, now.month, 01)
    return [start, end]


def get_all_bids_tenders():
    header_added = False
    to_skip = [['before_2017'], ['after_2017-01-01'], ['after_2017-08-16']]
    all_tenders = []
    all_bids = []
    tenders_files = [file for file in os.listdir(PATH) if all(['tenders' in file, 'zip' not in file, 'all' not in file])]
    bids_files = [file for file in os.listdir(PATH) if all(['bids' in file, 'zip' not in file, 'all' not in file])]
    for file in tenders_files:
        with open(os.path.join(PATH, file), 'r') as file:
            tenders = list(csv.reader(file))
        if not header_added:
            all_tenders.extend(tenders)
            header_added = True
        else:
            all_tenders.extend(tenders[1:])
    header_added = False
    for file in bids_files:
        with open(os.path.join(PATH, file), 'r') as file:
            bids = list(csv.reader(file))
        if not header_added:
            all_bids.extend(bids)
            header_added = True
        else:
            all_bids.extend(bids[1:])
    with open(os.path.join(PATH, str("all" + "@" + bids_files[0].split('@')[1])), "w") as file:
        file = csv.writer(file)
        for bid in all_bids:
            if bid in to_skip:
                continue
            file.writerow(bid)
    with open(os.path.join(PATH, str("all" + "@" + tenders_files[0].split('@')[1])), "w") as file:
        file = csv.writer(file)
        for tender in all_tenders:
            if tender in to_skip:
                continue
            file.writerow(tender)


def get_files_for_sending(broker):
    if broker == 'all':
        return [os.path.join(PATH, file) for file in os.listdir(PATH) if 'all' in file]
    else:
        return [os.path.join(PATH, file) for file in os.listdir(PATH) if broker in file]


def get_files_for_zip(broker):
    return [os.path.join(PATH, file) for file in os.listdir(PATH) if all([broker in file, 'zip' not in file])]


def get_files_for_all_zip():
    bids_invoices_files = []
    tenders_refunds_files = []
    for file in os.listdir(PATH):
        if all(["all" in file, "bids" in file, 'zip' not in file]) or all(["invoices" in file, 'zip' not in file]):
            bids_invoices_files.append(os.path.join(PATH, file))
        elif all(["all" in file, "tenders" in file, 'zip' not in file]) or all(["refunds" in file, 'zip' not in file]):
            tenders_refunds_files.append(os.path.join(PATH, file))
    return bids_invoices_files, tenders_refunds_files


def clean_up():
    for file in os.listdir(PATH):
        if not "zip" in file:
            os.remove(os.path.join(PATH, file))


def run():
    parser = get_argument_parser()
    args = parser.parse_args()
    config = ConfigParser()
    config.read(args.config)
    period = args.period if args.period else get_period()
    is_all = False
    print "Generation period:{} to {}".format(period[0], period[1])
    brokers = args.brokers if args.brokers else config.get("generate", "brokers").split(' ')
    if "all" in brokers:
        is_all = True
        brokers.remove("all")
    for broker in brokers:
        print "Generating for {}".format(broker)
        generate_for_broker(broker, period, args.config, args.timezone)
        run_zip(get_files_for_zip(broker), args.config)
    if is_all:
        get_all_bids_tenders()
        for i, op in enumerate(['bids', 'tenders']):
            run_zip(get_files_for_all_zip()[i], args.config, "all@{}--{}-{}.zip".format(period[0], period[1], op))
    clean_up()
    if args.notify:
        if args.notify_brokers:
            for broker in args.notify_brokers:
                run_send(broker, args.config, get_files_for_sending(broker), True)
        else:
            for broker in brokers:
                run_send(broker, args.config, get_files_for_sending(broker), True)
