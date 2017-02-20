import digitalocean
import time
import paramiko


def add_args(parser):
    parser.add_argument("--createvm", help="Create a Digital Ocean VM to execute on", action="store_true")
    parser.add_argument("--listdroplets", help="List available DO Droplets", action="store_true")


def parse_args(args, config):
    if args.listdroplets:
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

    # Configure the VM with the setup script
    print()
    setup_script = config.get("DigitalOcean", "setup_script")
    print("Setting up the droplet with the configuration script...")
    _, stdout, stderr = ssh.exec_command(
        "wget -O - {} | bash".format(setup_script))

    # Print the output of configuration
    for line in iter(lambda: stdout.readline(2048), ""):
        print(line)
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
