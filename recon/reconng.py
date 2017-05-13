import jsonrpclib
import logging.config
import database.elastic_bounty_tools
from connectivity import do_wrapper

# Setup logging
logging.config.fileConfig('logging.conf')
logger = logging.getLogger('reconng')


def add_args(parser):
    parser.add_argument("--reconng", help="Execute recon-ng tasks", action="store_true")
    parser.add_argument("--domains", help="List of domains to target", nargs='+')


def parse_args(args, config):
    droplet = None
    # If we're passed reconng
    if args.reconng:
        # Make sure we're given a workspace
        if args.workspace is not None and (args.droplet is not None or args.bulkrecon):
            # If we're using bulkrecon
            if args.bulkrecon:
                droplet = args.droplet
            # If we were passed a --droplet argument
            elif args.droplet is not None and not args.bulkrecon:
                droplet = do_wrapper.get_droplet(args.droplet, config)

            if droplet is not None:
                if args.domains is not None:
                    # droplet = do_wrapper.get_droplet(args.droplet, config)
                    run_recon(droplet, config, args.workspace, args.domains)

        # If we were passed reconng, but didn't get all the requirements
        else:
            print("Required arguments not passed. Need either --createvm or --droplet to execute, along with "
                  "--workspace and --domains")


def run_recon(droplet, config, workspace, domain_list):
    # Recon modules to use
    recon_modules = [
        "recon/domains-hosts/google_site_web",
        "recon/domains-hosts/brute_hosts",
        "recon/domains-hosts/bing_domain_web",
        "recon/domains-hosts/hackertarget",
        "recon/domains-hosts/ssl_san",
        "recon/domains-hosts/threatcrowd",
        "recon/hosts-hosts/resolve",
    ]

    # Build recon-ng JSONRPC object
    client = jsonrpclib.Server("http://{}:4141".format(droplet.ip_address))
    session_id = client.init()

    # Create the workspace
    client.workspace(workspace, session_id)

    # Add the domains
    for domain in domain_list:
        client.add("domains", domain, session_id)

    # Run the recon modules
    for recon_module in recon_modules:
        client.use(recon_module, session_id)
        client.run(session_id)

    # Collect the results and save them to Elastic
    results = client.show("hosts", session_id)

    for host in results:
        database.elastic_bounty_tools.add_host(host[2], host[1], host[7], workspace)
