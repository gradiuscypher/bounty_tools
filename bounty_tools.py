#!/usr/bin/env python

import argparse
import configparser
import recon.reconng
import enrichment.shodan
import connectivity.digitalocean
import reporting.console


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Command line tool for bounty management.")
    parser.add_argument("--config", help="Config file to use rather than the default")

    # Get args from other plugins
    recon.reconng.add_args(parser)

    opts = parser.parse_args()

    # Read from the config file
    config = configparser.RawConfigParser()
    if opts.config is None:
        config.read("config.conf")
    else:
        config.read(opts.config)

    if opts.reconng:
        recon.reconng.parse_args(opts)

