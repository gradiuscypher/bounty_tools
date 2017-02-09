#!/usr/bin/env python

import argparse
import time
import configparser
import shodan
import traceback
from db.models import Host, Port, Shodan
from db.database import db_session


def shodan_enrichment(target_host, config):
    # Setup the db session
    session = db_session()

    try:
        # Get phyiscal location, ASN, ports, etc
        shodan_api_key = config.get("Shodan", "api_key")
        api = shodan.Shodan(shodan_api_key)
        shodan_host = api.host(target_host.ip_address)

        port_list = [x.number for x in target_host.ports]
        # Add ports to host
        for port in shodan_host['ports']:
            if port in port_list:
                print("This port already exists.")
            else:
                print("Adding port to host.")
                p = Port(number=port, host=target_host)
                session.add(p)
                session.commit()

        # Add other Shodan info

        # Sleep to try and ratelimit
        time.sleep(.5)

    except shodan.APIError:
        print("API Error, sleeping 1 second")
        print(traceback.format_exc())
        time.sleep(1)
    except:
        print(traceback.format_exc())


def masscan_enrichment():
    pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Command line tool to include more info in the bounty DB.")
    parser.add_argument("--config", help="Config file to use rather than the default")
    parser.add_argument("--shodan", help="Iterate through the host DB and add information from Shodan", action="store_true")
    parser.add_argument("--workspace", help="Target workspace")
    opts = parser.parse_args()

    # Setup the db session
    session = db_session()

    # Read from the config file
    config = configparser.RawConfigParser()
    if opts.config is None:
        config.read("config.conf")
    else:
        config.read(opts.config)

    if opts.shodan and opts.workspace is not None:
        for host in session.query(Host).filter(Host.workspace == opts.workspace).all():
            shodan_enrichment(host, config)
