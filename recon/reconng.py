import paramiko
import configparser
from connectivity import do_wrapper


def add_args(parser):
    parser.add_argument("--runrecon", help="Execute recon-ng tasks", action="store_true")
    parser.add_argument("--droplet", help="Digital Ocean droplet ID for execution", action="store_true")
    parser.add_argument("--domains", help="List of domains to target", nargs='+')
    parser.add_argument("--workspace", help="Name of the workspace")


def parse_args(args, config):
    # If we were passed a --droplet argument
    if args.runrecon and args.createvm and (args.workspace is not None) and (args.domains is not None) and (args.droplet is not None):
        pass

    # If we were passed a --createvm argument
    elif args.runrecon and args.createvm and (args.workspace is not None) and (args.domains is not None):
        droplet = do_wrapper.create_vm()
        workspace = args.workspace
        domains = args.domains
        run_recon(droplet, config, workspace, domains)


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
