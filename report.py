#!/usr/bin/env python

import argparse
import configparser
from db.database import db_session
from db.models import Host, Althosts


def console_report():
    session = db_session()
    qr = session.query(Host).all()

    for host in qr:
        port_list = [x.number for x in host.ports]
        print("{} | {} | {} | {} | {}".format(host.workspace, host.source, host.ip_address, host.host, port_list))

        althosts = session.query(Althosts).filter(Althosts.host_id == host.id)
        for althost in althosts:
            print("    {} | {}".format(althost.source, althost.hostname))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Command line tool for reporting.")
    parser.add_argument("--config", help="Config file to use rather than the default")
    parser.add_argument("--console", help="Print report to console.", action="store_true")
    opts = parser.parse_args()

    # Read from the config file
    config = configparser.RawConfigParser()
    if opts.config is None:
        config.read("config.conf")
    else:
        config.read(opts.config)

    if opts.console:
        console_report()
