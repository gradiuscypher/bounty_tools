#!/usr/bin/env python
# Command line tool for elastibounty
# TODO: Logging to file + elasticsearch
import argparse
import subprocess
import traceback


def export_to_sheets():
    pass


def import_from_masscan():
    pass


def import_from_nmap():
    pass


def import_from_reconng(workspace, remote=None):
    # copy file from local or SCP from remote host
    # iterate through all tables of DB and extract all useful information to proper workspace indexes
    print("Importing from recon-ng")
    if remote is not None:
        try:
            print("Remote importing from", remote)
            source_file = "~/.recon-ng/workspaces/{}".format(workspace)
        except:
            print("An error occured while trying to SCP the file from the remote system")
            traceback.print_exc()


def import_from_shodan():
    # TODO: Import from a new shodan scan or from a shodan report
    pass


def scp_files(host, source, destination):
    # TODO: use for scp'ing files when importing from a remote location
    # NOTE: Not 100% sure if this is needed, attempting to use something like paramiko instead would be smart
    pass


def setup_elastalert():
    # TODO: Use for easy configuraiton of elastalert, filling in JSON template with provided information
    pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Command line interface for ElastiBounty tools.")
    parser.add_argument('-i', help="Import data from sources: reconng, etc", dest='import_from')
    parser.add_argument('-w', help="Workspace name. Must match workspace name from other tools, if applicable.",
                        dest='workspace')
    parser.add_argument('--remote',
                        help="Import data from a remote location. REMOTE location is a host configured in ssh config")
    opts = parser.parse_args()

    if opts.import_from == "reconng":
        if opts.remote is not None:
            import_from_reconng(opts.workspace, opts.remote)
        else:
            import_from_reconng(opts.workspace)
