import digitalocean
import time
import paramiko
import json


def add_args(parser):
    parser.add_argument("--createvm", help="Create a Digital Ocean VM to execute on", action="store_true")
    parser.add_argument("--listdroplets", help="List available DO Droplets", action="store_true")
    parser.add_argument("--cleanupdroplets", help="Destroys all recon droplets", action="store_true")


def parse_args(args, config):
    if args.listdroplets:
        list_droplets(config)
    if args.createvm:
        droplet = create_vm(config)
    if args.cleanupdroplets:
        cleanup_droplets(config)


def cleanup_droplets(config):
    list_droplets(config)
    # build the digital ocean manager object
    manager = digitalocean.Manager(token=config.get("DigitalOcean", "api_key"))

    droplets = manager.get_all_droplets(tag_name="bounty")

    # Delete all droplets that match the tag
    for droplet in droplets:
        droplet.destroy()
    list_droplets(config)


def create_vm(config):
    # build the digital ocean manager object
    manager = digitalocean.Manager(token=config.get("DigitalOcean", "api_key"))

    # Create a VM and return a droplet object.
    droplet = digitalocean.Droplet(token=manager.token, name="recon-droplet", region="nyc1", image="ubuntu-16-04-x64",
                                   size_slug="512mb", ssh_keys=manager.get_all_sshkeys(), backups=False)
    print("Creating the droplet...")
    droplet.create()

    print("Waiting for the droplet to be active...")
    # Wait for the DO droplet to become active
    while droplet.status != "active":
        for i in range(30):
            # Overwrites the previous line with the next line, removing the dependency of progressbar2
            print("Sleeping for {} seconds to wait for the droplet to become active.".format(30-i), end="\r")
            time.sleep(1)
        droplet.load()

    # Show progress
    print()
    droplet.load()
    print("Droplet has been created with the address {}".format(droplet.ip_address))

    # Setup the SSH connection
    print()
    for i in range(30):
        print("Sleeping for {} seconds to wait for SSH to be ready...".format(30-i), end="\r")
        time.sleep(1)
    print("SSH should now be ready...")
    droplet.load()
    ssh_key_filename = config.get("DigitalOcean", "ssh_key_filename")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    print("Connecting to the droplet...")
    ssh.connect(droplet.ip_address, username="root", key_filename=ssh_key_filename)

    # wget the firewall config and swap in relevant IP addresses to allow connectivity to the droplet
    firewall_config = config.get("DigitalOcean", "firewall_config")
    source_ips = config.get("DigitalOcean", "source_ips")
    rpc_script = config.get("DigitalOcean", "rpc_script")
    rpc_service = config.get("DigitalOcean", "rpc_service")

    # build a comma separated list of ips to add to firewall config
    ip_str = ""
    for ip in json.loads(source_ips):
        if ip_str == "":
            ip_str += ip
        else:
            ip_str += "," + ip

    # grab the firewall config
    _, stdout, stderr = ssh.exec_command(
        "wget {}".format(firewall_config))

    # replace SOURCE_IPS in the config with ip_str
    _, stdout, stderr = ssh.exec_command(
        "sed -i 's/SOURCE_IPS/{}/g' iptables.rules".format(ip_str))

    # grab the rpc script
    _, stdout, stderr = ssh.exec_command(
        "wget {}".format(rpc_script))

    # grab the rpc service file
    _, stdout, stderr = ssh.exec_command(
        "wget {}".format(rpc_service))

    # Configure the VM with the setup script
    print()
    setup_script = config.get("DigitalOcean", "setup_script")
    print("Setting up the droplet with the configuration script...")
    _, stdout, stderr = ssh.exec_command(
        "wget -O - {} | bash".format(setup_script))

    # Print the output of configuration
    for line in iter(lambda: stdout.readline(2048), ""):
        print(line)

    tag = digitalocean.Tag(token=manager.token, name="bounty")
    tag.create()
    tag.add_droplets([str(droplet.id)])

    print("Droplet Created.")

    print(" ID | IP Addr | Name | Tags")
    print("{0.id} | {0.ip_address} | {0.name} | {0.tags}".format(droplet))
    return droplet


def get_droplet(droplet_id, config):
    manager = digitalocean.Manager(token=config.get("DigitalOcean", "api_key"))
    return manager.get_droplet(droplet_id)


def list_droplets(config):
    # build the digital ocean manager object
    manager = digitalocean.Manager(token=config.get("DigitalOcean", "api_key"))

    droplets = manager.get_all_droplets()

    print("Droplets Running:\n")
    print(" ID | IP Addr | Name | Tags")
    print("===========================")
    for droplet in droplets:
        print("{0.id} | {0.ip_address} | {0.name} | {0.tags}".format(droplet))
    print()
