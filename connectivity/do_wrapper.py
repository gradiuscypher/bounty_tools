import digitalocean


def add_args(parser):
    parser.add_argument("--dowrapper", help="The Digital Ocean plugin", action="store_true")
    parser.add_argument("--createvm", help="Create a Digital Ocean VM to execute on", action="store_true")


def parse_args(args):
    # If we were passed a --createvm argument
    if args.createvm is not None:
        create_vm()


def create_vm():
    # Create a VM and return a droplet object.
    return "CREATING VM"
