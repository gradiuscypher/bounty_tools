import time
import censys.ipv4
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
    # TODO: Catch 404, better progress tracking
    ip_list = elastic_bounty_tools.get_unique_ips(args.workspace)

    for ip in ip_list:
        enrich_info = ip_info(config, ip['key'])
        asn_owner = enrich_info['autonomous_system']['name']
        protocols = enrich_info['protocols']
        elastic_bounty_tools.add_field_to_ip(args.workspace, ip['key'], "asn_owner", asn_owner)
        elastic_bounty_tools.add_field_to_ip(args.workspace, ip['key'], "protocols", protocols)
        print(asn_owner, protocols, ip)
