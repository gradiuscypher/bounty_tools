def add_args(parser):
    parser.add_argument("--reconng", help="recon-ng flag", action="store_true")
    parser.add_argument("--test", help="recon-ng test")


def parse_args(args):
    if args.test is not None:
        test_fun(args.test)


def test_fun(test1):
    print(test1)
