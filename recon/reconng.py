import paramiko
import sqlite3
import logging.config
import database.elastic_bounty_tools
from connectivity import do_wrapper
from database.bounty_tools_db import BountyToolsDb

# Setup logging
logging.config.fileConfig('logging.conf')
logger = logging.getLogger('reconng')


def add_args(parser):
    parser.add_argument("--reconng", help="Execute recon-ng tasks", action="store_true")
    parser.add_argument("--reconimport", help="Import recon results to DB", action="store_true")
    parser.add_argument("--dbimport", help="Import recon to local DB", action="store_true")
    parser.add_argument("--autocleanup", help="Cleanup and remove the VM when completed", action="store_true")
    parser.add_argument("--domains", help="List of domains to target", nargs='+')


def parse_args(args, config):

    # If we're passed reconng
    if args.reconng:
        # Make sure we're given a workspace
        if args.workspace is not None:
            workspace = args.workspace
            droplet = None

            # If we were passed a --droplet argument
            if args.droplet is not None:
                droplet = do_wrapper.get_droplet(args.droplet, config)
            # If we were passed a --createvm argument
            elif args.createvm:
                droplet = do_wrapper.create_vm(config)

            if droplet is not None:
                if args.reconimport:
                    if args.dbimport:
                        import_to_db(droplet, config, args.workspace)
                    elif args.elastic:
                        database.elastic_bounty_tools.reconng_import(args, config)

                elif args.domains is not None:
                    droplet = do_wrapper.get_droplet(args.droplet, config)
                    run_recon(droplet, config, args.workspace, args.domains)

                    if args.autocleanup:
                        # Localize the data
                        import_to_db(droplet, config, workspace)

                        # Destroy the droplet
                        print("Destroying the recon droplet...")
                        droplet.destroy()
                        print("Destroyed.")

        # If we were passed reconng, but didn't get all the requirements
        else:
            print("Required arguments not passed. Need either --createvm or --droplet to execute, along with "
                  "--workspace and --domains")


def import_to_db(droplet, config, workspace):
    # Setup SSH
    ssh_key_filename = config.get("DigitalOcean", "ssh_key_filename")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    print("Connecting to the droplet...")
    ssh.connect(droplet.ip_address, username="root", key_filename=ssh_key_filename)

    # Collect recon-ng db file
    print("Downloading recon-ng db...")
    sftp = ssh.open_sftp()
    sftp.chdir("/root/.recon-ng/workspaces/{}".format(workspace))
    sftp.get("data.db", "{}.db".format(workspace))

    # Build the DB and create session object and connect to downloaded db
    conn = sqlite3.connect('{}.db'.format(workspace))
    cursor = conn.cursor()

    # Iterate through recon-ng db and add host data to recon.db
    print("Pulling data from recon-ng db to local db...")
    bounty_db = BountyToolsDb()
    new_hosts = 0
    duplicate_hosts = 0

    for row in cursor.execute("select * from hosts"):
        hostname = row[0]
        ip_address = row[1]
        source = row[6]

        added_host = bounty_db.add_host(ip_address, hostname, source, workspace)

        if added_host:
            new_hosts += 1
        else:
            duplicate_hosts += 1

        print("{} new hosts, {} duplicate hosts".format(new_hosts, duplicate_hosts), end="\r")
    print("{} new hosts, {} duplicate hosts".format(new_hosts, duplicate_hosts))


def run_recon(droplet, config, workspace, domain_list):

    # Setup SSH
    ssh_key_filename = config.get("DigitalOcean", "ssh_key_filename")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    print("Connecting to the droplet...")
    ssh.connect(droplet.ip_address, username="root", key_filename=ssh_key_filename)

    # Do all the stuff with recon-ng
    recon_modules = [
        "recon/domains-hosts/google_site_web",
        "recon/domains-hosts/brute_hosts",
        "recon/domains-hosts/bing_domain_web",
        "recon/domains-hosts/hackertarget",
        "recon/domains-hosts/ssl_san",
        "recon/domains-hosts/threatcrowd",
        "recon/hosts-hosts/resolve",
    ]

    # Add domains to workspace
    for domain in domain_list:
        print("Adding domain: {}".format(domain))
        _, stdout, stderr = ssh.exec_command('./recon-ng/recon-cli -w {} -C "add domains {}"'.format(workspace, domain))
        # Print the output of execution
        for line in iter(lambda: stdout.readline(2048), ""):
            print(line)
        print()

    # Execute recon-ng modules
    for module in recon_modules:
        print("Executing recon-ng module: {}".format(module))
        _, stdout, stderr = ssh.exec_command('./recon-ng/recon-cli -w {} -m "{}" -x'.format(workspace, module))
        # Print the output of execution
        for line in iter(lambda: stdout.readline(2048), ""):
            print(line)
        print()

    # Remove hosts from recon-ng db where there is no IP
    print("Removing hosts without IP addresses from the DB...")
    _, stdout, stderr = ssh.exec_command(
        './recon-ng/recon-cli -w {} -C "query delete from hosts where ip_address is null"'.format(workspace))
    # Print the output of execution
    for line in iter(lambda: stdout.readline(2048), ""):
        print(line)
    print()
