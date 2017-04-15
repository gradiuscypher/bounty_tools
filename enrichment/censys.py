import time
import traceback
import censys.ipv4
from censys.base import CensysNotFoundException, CensysRateLimitExceededException
from database import elastic_bounty_tools


def add_args(parser):
    parser.add_argument("--censys", help="Enables Censys enrichment.", action="store_true")


def parse_args(args, config):
    if args.censys and args.workspace is not None:
        if args.elastic:
            enrich_elastic(args, config)


def ip_info(config, ip_address):
    api_id = config.get("Censys", "api_id")
    api_secret = config.get("Censys", "api_secret")
    censys_ip = censys.ipv4.CensysIPv4(api_id=api_id, api_secret=api_secret)
    return censys_ip.view(ip_address)


def enrich_elastic(args, config):
    ip_list = elastic_bounty_tools.get_unique_ips(args.workspace)
    total_ips = len(ip_list)
    completed = 0
    no_result = 0

    for ip in ip_list:
        print("{} Remaining | {} Completed | {} No Results".format(total_ips, completed, no_result), end="\r")

        try:
            enrich_info = ip_info(config, ip['key'])
            asn_owner = enrich_info['autonomous_system']['name']
            protocols = enrich_info['protocols']
            elastic_bounty_tools.add_field_to_ip(args.workspace, ip['key'], "asn_owner", asn_owner)
            elastic_bounty_tools.add_field_to_ip(args.workspace, ip['key'], "protocols", protocols)
            total_ips -= 1
            completed += 1

        except KeyboardInterrupt:
            raise

        except CensysRateLimitExceededException:
            # TODO: Need to wait for more API calls
            print("YOU STILL NEED TO IMPLEMENT API WAITING")
            print(traceback.format_exc())
            raise

        except CensysNotFoundException:
            no_result += 1

        except:
            print(traceback.format_exc())

    print("{} Remaining | {} Completed | {} No Results".format(total_ips, completed, no_result))
