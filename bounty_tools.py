#!/usr/bin/env python

import argparse
import configparser
from recon import reconng, crt_ssl
from enrichment import shodan
from connectivity import do_wrapper
from reporting import console


if __name__ == "__main__":
    # List of plugins to use
    plugin_list = [reconng, do_wrapper, console, shodan, crt_ssl]

    parser = argparse.ArgumentParser(description="Command line tool for bounty management.")
    parser.add_argument("--config", help="Config file to use rather than the default")
    parser.add_argument("--debug", help="Debug printing mode", action="store_true")

    # Get args from other plugins
    for plugin in plugin_list:
        plugin.add_args(parser)

    opts = parser.parse_args()

    # Read from the config file
    config = configparser.RawConfigParser()
    if opts.config is None:
        config.read("config.conf")
    else:
        config.read(opts.config)

    # Run the plugins plugins
    for plugin in plugin_list:
        plugin.parse_args(opts, config)
