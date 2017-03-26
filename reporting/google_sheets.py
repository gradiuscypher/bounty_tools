from database.database import db_session
from database.models import Host, Althosts


def add_args(parser):
    parser.add_argument("--sheets", help="Recon report to Google Sheets", action="store_true")


def parse_args(args, config):
    if args.sheets and args.workspace is not None:
        pass
