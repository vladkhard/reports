from reports.modules import AWSClient
from reports.vault import Vault
from reports.report import ReportConfig
from reports.helpers import (
    get_send_args_parser
)


def run():
    parser = get_send_args_parser()
    args = parser.parse_args()
    config = ReportConfig.from_namespace(args)
    client = AWSClient(config)
    if args.brokers:
        client.brokers = args.brokers
    if args.exists:
        client.send_from_timestamp(args.timestamp)
    else:
        client.send_files(args.files, args.timestamp)
    for broker in client.links:
        if (not client.brokers) or (client.brokers and broker['broker'] in client.brokers):
            print "Url for {} ==> {}\n".format(broker['broker'], broker['link'])
    if args.test:
        client.send_emails(email)
    else:
        if args.notify:
            client.send_emails()

