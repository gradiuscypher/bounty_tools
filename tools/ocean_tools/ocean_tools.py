#!/usr/bin/env python

import digitalocean
import configparser
import argparse


def print_all_droplets():
    droplets = manager.get_all_droplets()

    print("Droplets Running:\n")
    for droplet in droplets:
        print("{0.name} {0.ip_address} {0.tags}".format(droplet))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Command line tool for managing digital ocean droplets.")
    parser.add_argument("-l", "--list", help="List all running droplets", action="store_true")
    parser.add_argument("--config", help="Config file to use rather than the default")
    opts = parser.parse_args()

    # Read from the config file
    config = configparser.RawConfigParser()
    if opts.config is None:
        config.read("config.conf")
    else:
        config.read(opts.config)

    # build the digital ocean manager object
    manager = digitalocean.Manager(token=config.get("DigitalOcean", "api_key"))

    if opts.list:
        print_all_droplets()

