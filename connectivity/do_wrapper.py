import digitalocean


def add_args(parser):
    parser.add_argument("--createvm", help="Create a Digital Ocean VM to execute on", action="store_true")
    parser.add_argument("--listdroplets", help="List available DO Droplets", action="store_true")


def parse_args(args, config):
    if args.createvm:
        create_vm()

    elif args.listdroplets:
        list_droplets(config)


def create_vm():
    # Create a VM and return a droplet object.
    return "CREATING VM"


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
