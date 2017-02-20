import shodan
import time
import traceback
from database.database import db_session
from database.models import Host, Port


def add_args(parser):
    parser.add_argument("--shodanports", help="Enriches data with Shodan port information", action="store_true")


def parse_args(args, config):
    if args.shodanports and args.workspace is not None:
        shodan_ports(args, config)


def shodan_ports(args, config):
    # Setup the db session
    session = db_session()
    # Setup API
    shodan_api_key = config.get("Shodan", "api_key")
    api = shodan.Shodan(shodan_api_key)

    target_host_query = session.query(Host).filter(Host.workspace == args.workspace).all()
    remaining = len(target_host_query)
    host_with_port = 0
    no_port_info = 0
    dupe_port = 0

    for target_host in target_host_query:
        try:
            # Get phyiscal location, ASN, ports, etc
            shodan_host = api.host(target_host.ip_address)

            port_list = [x.number for x in target_host.ports]
            # Add ports to host
            for port in shodan_host['ports']:
                if port in port_list:
                    dupe_port += 1
                else:
                    host_with_port += 1
                    p = Port(number=port, host=target_host)
                    session.add(p)
                    session.commit()

            # Sleep to try and ratelimit
            time.sleep(.1)

        except shodan.APIError:
            # print("API Error, sleeping .5 second")
            # print(traceback.format_exc())
            no_port_info += 1
            time.sleep(.1)
        except:
            print(traceback.format_exc())

        remaining -= 1
        print("Remaining: {}  New: {}  Duplicates: {}  No Info: {}".format(remaining, host_with_port, dupe_port, no_port_info), end="\r")
    print("Remaining: {}  New: {}  Duplicates: {}  No Info: {}".format(remaining, host_with_port, dupe_port, no_port_info))
