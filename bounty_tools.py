#!/usr/bin/env python

import argparse
import configparser
from recon import reconng
from enrichment import shodan
from connectivity import do_wrapper
from reporting import console


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Command line tool for bounty management.")
    parser.add_argument("--config", help="Config file to use rather than the default")

    # Get args from other plugins
    reconng.add_args(parser)
    do_wrapper.add_args(parser)

    opts = parser.parse_args()

    # Read from the config file
    config = configparser.RawConfigParser()
    if opts.config is None:
        config.read("config.conf")
    else:
        config.read(opts.config)

    reconng.parse_args(opts, config)
    do_wrapper.parse_args(opts, config)

