import json
from recon import reconng
from connectivity import do_wrapper
from database import elastic_bounty_tools


def add_args(parser):
    parser.add_argument("--bulkrecon", help="Run recon on a bulk set of hosts in a JSON file", action="store_true")
    parser.add_argument("--hostjson", help="JSON file containing list of workspaces and targets")


def parse_args(args, config):
    if args.bulkrecon and args.hostjson is not None:
        with open(args.hostjson) as json_data:
            json_hosts = json.load(json_data)
        bulk_recon(args, config, json_hosts)


def bulk_recon(args, config, json_hosts):
    if args.droplet is None:
        args.droplet = do_wrapper.create_vm(config)

    for target in json_hosts:
        args.workspace = target
        args.domains = json_hosts[target]
        reconng.parse_args(args, config)
        elastic_bounty_tools.parse_args(args, config)
