import json
import digitalocean
import logging.config
from recon import reconng
from connectivity import do_wrapper
from database import elastic_bounty_tools

# Configure Logging
logging.config.fileConfig('logging.conf', disable_existing_loggers=False)
logger = logging.getLogger('bounty_tools')


def add_args(parser):
    parser.add_argument("--bulkrecon", help="Run recon on a bulk set of hosts in a JSON file", action="store_true")
    parser.add_argument("--hostjson", help="JSON file containing list of workspaces and targets")
    parser.add_argument("--distribute", help="Number of scanners to distribute scans across")


def parse_args(args, config):
    if args.bulkrecon and args.hostjson is not None:
        with open(args.hostjson) as json_data:
            json_hosts = json.load(json_data)
        bulk_recon(args, config, json_hosts)


def bulk_recon(args, config, json_hosts):
    # build the digital ocean manager object
    manager = digitalocean.Manager(token=config.get("DigitalOcean", "api_key"))

    if args.distribute is not None:
        # Get enough droplets so that we can distribute between scanners, do this in multiprocess
        droplets = manager.get_all_droplets()
        required_droplets = int(args.distribute)

        if len(droplets) < required_droplets:
            more_droplets = required_droplets - len(droplets)
            logger.debug("Creating {} more droplets".format(more_droplets))

            for x in range(0, more_droplets):
                do_wrapper.create_vm(config)
                logger.debug("Making a droplet...")

        # Distribute scans and launch, then collect results and run enrichment, do this in multiprocess

    else:
        if args.droplet is None:
            args.droplet = do_wrapper.create_vm(config)

        for target in json_hosts:
            args.workspace = target
            args.domains = json_hosts[target]
            reconng.parse_args(args, config)
            elastic_bounty_tools.parse_args(args, config)
