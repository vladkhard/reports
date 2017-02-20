from reports.helpers import (
    create_arguments
)

from reports.modules import Refunds
from reports.config import Config


def run():
    parser = create_arguments()
    args = parser.parse_args()
    config = Config.from_namespace(args)
    bids = Refunds(config)
    bids.run()


if __name__ == "__main__":
    run()
