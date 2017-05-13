#!/usr/bin/env python

import argparse
import configparser
import logging.config
from recon import reconng, crt_ssl
from enrichment import shodan, censys
from connectivity import do_wrapper
from database import elastic_bounty_tools
from automation import automation

# Configure Logging
logging.config.fileConfig('logging.conf', disable_existing_loggers=False)
logger = logging.getLogger('bounty_tools')
logging.getLogger("elasticsearch").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("digitalocean").setLevel(logging.WARNING)
logging.getLogger("paramiko").setLevel(logging.WARNING)


if __name__ == "__main__":
    # List of plugins to use
    plugin_list = [reconng, do_wrapper, shodan, crt_ssl, elastic_bounty_tools, automation, censys]

    parser = argparse.ArgumentParser(description="Command line tool for bounty management.")
    parser.add_argument("--config", help="Config file to use rather than the default")
    parser.add_argument("--bulkenrich", help="Run enrichment tasks on all workspaces", action="store_true")
    parser.add_argument("--debug", help="Debug printing mode", action="store_true")
    parser.add_argument("--droplet", help="Digital Ocean droplet ID for execution")
    parser.add_argument("--workspace", help="Name of the workspace")

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
