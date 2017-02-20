from database.database import db_session
from database.models import Host, Althosts


def add_args(parser):
    parser.add_argument("--console", help="Recon report to console", action="store_true")


def parse_args(args, config):
    if args.console:
        console()


def console():
    session = db_session()
    qr = session.query(Host).all()

    for host in qr:
        port_list = [x.number for x in host.ports]
        print("{} | {} | {} | {} | {}".format(host.workspace, host.source, host.ip_address, host.host, port_list))

        althosts = session.query(Althosts).filter(Althosts.host_id == host.id)
        for althost in althosts:
            print("    {} | {}".format(althost.source, althost.hostname))
        print()
