#!/usr/bin/env python


import argparse
import configparser
import time
import digitalocean
import paramiko
import sqlite3
import db.database
from db.database import db_session
from db.models import Host, Althosts


def setup_vm(manager, config, verbose):
    droplet = digitalocean.Droplet(token=manager.token, name="recon-droplet", region="nyc1", image="ubuntu-16-04-x64",
                                   size_slug="512mb", ssh_keys=manager.get_all_sshkeys(), backups=False)
    print("Creating the droplet...")
    droplet.create()

    print("Waiting for the droplet to be active...")
    # Wait for the DO droplet to become active
    while droplet.status != "active":
        for i in range(30):
            # Overwrites the previous line with the next line, removing the dependency of progressbar2
            print("Sleeping for {} seconds to wait for the droplet to become active.".format(30-i), end="\r")
            time.sleep(1)
        droplet.load()

    # Show progress
    print()
    droplet.load()
    print("Droplet has been created with the address {}".format(droplet.ip_address))

    # Setup the SSH connection
    print()
    for i in range(30):
        print("Sleeping for {} seconds to wait for SSH to be ready...".format(30-i), end="\r")
        time.sleep(1)
    print("SSH should now be ready...")
    droplet.load()
    ssh_key_filename = config.get("DigitalOcean", "ssh_key_filename")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    print("Connecting to the droplet...")
    ssh.connect(droplet.ip_address, username="root", key_filename=ssh_key_filename)

    # Configure the VM with the setup script
    print()
    setup_script = config.get("DigitalOcean", "setup_script")
    print("Setting up the droplet with the configuration script...")
    _, stdout, stderr = ssh.exec_command(
        "wget -O - {} | bash".format(setup_script))

    # Print the output of configuration
    for line in iter(lambda: stdout.readline(2048), ""):
        print(line)
    print("Droplet Created.")

    print(" ID | IP Addr | Name | Tags")
    print("{0.id} | {0.ip_address} | {0.name} | {0.tags}".format(droplet))
    return droplet


def run_recon(manager, droplet, config, workspace, domain_list):
    # Setup SSH
    ssh_key_filename = config.get("DigitalOcean", "ssh_key_filename")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    print("Connecting to the droplet...")
    ssh.connect(droplet.ip_address, username="root", key_filename=ssh_key_filename)

    # Do all the stuff with recon-ng
    recon_modules = [
        "recon/domains-hosts/google_site_web",
        "recon/domains-hosts/brute_hosts",
        "recon/domains-hosts/bing_domain_web",
        "recon/domains-hosts/hackertarget",
        "recon/domains-hosts/ssl_san",
        "recon/domains-hosts/threatcrowd",
        "recon/hosts-hosts/resolve",
    ]

    # Add domains to workspace
    for domain in domain_list:
        print("Adding domain: {}".format(domain))
        _, stdout, stderr = ssh.exec_command('./recon-ng/recon-cli -w {} -C "add domains {}"'.format(workspace, domain))
        # Print the output of execution
        for line in iter(lambda: stdout.readline(2048), ""):
            print(line)
        print()

    # Execute recon-ng modules
    for module in recon_modules:
        print("Executing recon-ng module: {}".format(module))
        _, stdout, stderr = ssh.exec_command('./recon-ng/recon-cli -w {} -m "{}" -x'.format(workspace, module))
        # Print the output of execution
        for line in iter(lambda: stdout.readline(2048), ""):
            print(line)
        print()

    # Remove hosts from recon-ng db where there is no IP
    print("Removing hosts without IP addresses from the DB...")
    _, stdout, stderr = ssh.exec_command(
        './recon-ng/recon-cli -w {} -C "query delete from hosts where ip_address is null"'.format(workspace))
    # Print the output of execution
    for line in iter(lambda: stdout.readline(2048), ""):
        print(line)
    print()


def import_to_db(manager, droplet, config, workspace):
    # Setup SSH
    ssh_key_filename = config.get("DigitalOcean", "ssh_key_filename")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    print("Connecting to the droplet...")
    ssh.connect(droplet.ip_address, username="root", key_filename=ssh_key_filename)

    # Collect recon-ng db file
    print("Downloading recon-ng db...")
    sftp = ssh.open_sftp()
    sftp.chdir("/root/.recon-ng/workspaces/{}".format(workspace))
    sftp.get("data.db", "{}.db".format(workspace))

    # Build the DB and create session object and connect to downloaded db
    db.database.init_db()
    session = db_session()
    conn = sqlite3.connect('{}.db'.format(workspace))
    cursor = conn.cursor()

    # Iterate through recon-ng db and add host data to recon.db
    print("Pulling data from recon-ng db to local db...")
    for row in cursor.execute("select * from hosts"):
        # Check if IP address already exists
        qresult = session.query(Host).filter(Host.ip_address == row[1])
        if qresult.count() > 0:
            first_host = qresult.first()

            # Check to see if the first_host has althosts that match, to avoid dupes
            fh_alts = session.query(Althosts).filter(Althosts.host_id == first_host.id).filter(Althosts.hostname == row[0])

            if fh_alts.count() == 0:
                ah = Althosts(hostname=row[0], source=row[6], host=first_host)
                session.add(ah)
                session.commit()
            else:
                print("Duplicate AltHost: {}".format(row[0]))

        #If no other IP exists
        else:
            print("new host")
            h = Host(host=row[0], ip_address=row[1], source=row[6], workspace=workspace)
            session.add(h)
            session.commit()


def cleanup_droplet(droplet):
    print("Destroying the recon droplet...")
    droplet.destroy()
    print("Destroyed.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Command line tool for bounty management.")
    parser.add_argument("--config", help="Config file to use rather than the default")
    parser.add_argument("--setupvm", help="Setup recon VM", action="store_true")
    parser.add_argument("--droplets", help="List DO droplets and their IDs", action="store_true")
    parser.add_argument("--verbose", help="Verbose logging", action="store_true")
    parser.add_argument("--recon", help="Run recon tasks on supplied droplet ID", metavar="DROPLET_ID")
    parser.add_argument("--importdb", help="Import recon-ng DB from supplied droplet ID", metavar="DROPLET_ID")
    parser.add_argument("--fullrecon", help="Setup recon VM and run recon tasks", action="store_true")
    parser.add_argument("--domains", help="List of domains to target", nargs='+')
    parser.add_argument("--workspace", help="Name of the workspace")
    opts = parser.parse_args()

    # Read from the config file
    config = configparser.RawConfigParser()
    if opts.config is None:
        config.read("config.conf")
    else:
        config.read(opts.config)

    # build the digital ocean manager object
    manager = digitalocean.Manager(token=config.get("DigitalOcean", "api_key"))

    if opts.setupvm:
        setup_vm(manager, config, opts.verbose)

    elif opts.fullrecon and (opts.domains is not None) and (opts.workspace is not None):
        droplet = setup_vm(manager, config, opts.verbose)
        workspace = opts.workspace
        domains = opts.domains
        run_recon(manager, droplet, config, workspace, domains)
        import_to_db(manager, droplet, config, workspace)
        cleanup_droplet(droplet)

    elif opts.droplets:
        droplets = manager.get_all_droplets()

        print("Droplets Running:\n")
        print(" ID | IP Addr | Name | Tags")
        print("===========================")
        for droplet in droplets:
            print("{0.id} | {0.ip_address} | {0.name} | {0.tags}".format(droplet))
        print()

    elif opts.importdb and (opts.workspace is not None):
        droplet = manager.get_droplet(opts.importdb)
        import_to_db(manager, droplet, config, opts.workspace)

    elif opts.recon and (opts.domains is not None) and (opts.workspace is not None):
        droplet = manager.get_droplet(opts.recon)
        run_recon(manager, droplet, config, opts.workspace, opts.domains)
