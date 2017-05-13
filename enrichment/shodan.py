import shodan
import time
import traceback
from database import elastic_bounty_tools


def add_args(parser):
    parser.add_argument("--shodanports", help="Enriches data with Shodan port information", action="store_true")


def parse_args(args, config):
    if args.shodanports and args.workspace is not None:
        shodan_ports(args, config)


def shodan_ports(args, config):
    host_with_port = 0
    no_port_info = 0
    dupe_port = 0

    # Setup API
    shodan_api_key = config.get("Shodan", "api_key")
    api = shodan.Shodan(shodan_api_key)

    # Get list of IPs from Elasticsearch
    ip_bucket = elastic_bounty_tools.get_unique_ips(args.workspace)
    remaining = len(ip_bucket)

    # Get info for each IP from Shodan
    for ip in ip_bucket:
        try:
            # Check if IP starts with 10.
            # TODO: Use the IP Library to check for RFC1918
            if not ip['key'].startswith("10."):
                shodan_host = api.host(ip['key'])
                for port in shodan_host['ports']:
                    result = elastic_bounty_tools.add_port(ip['key'], port, "shodan", args.workspace)

                    if result:
                        host_with_port += 1
                    else:
                        dupe_port += 1

        except shodan.APIError:
            no_port_info += 1
            time.sleep(.1)

        except KeyboardInterrupt:
            raise

        except:
            print(traceback.format_exc())

        remaining -= 1
        print("Remaining: {}  New: {}  Duplicates: {}  No Info: {}".format(remaining, host_with_port, dupe_port, no_port_info), end="\r")
    print("Remaining: {}  New: {}  Duplicates: {}  No Info: {}".format(remaining, host_with_port, dupe_port, no_port_info))
