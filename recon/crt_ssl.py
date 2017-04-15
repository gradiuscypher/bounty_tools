import requests
import traceback
from bs4 import BeautifulSoup
from dns.resolver import query
from dns.exception import DNSException
from database.bounty_tools_db import BountyToolsDb
from database import elastic_bounty_tools

bountydb = BountyToolsDb()


def add_args(parser):
    parser.add_argument("--crtssl", help="Search crt.sh for domains in your workspace", action="store_true")
    parser.add_argument("--remote", help="Execute this command on a remote droplet", action="store_true")


def parse_args(args, config):
    if args.crtssl and (args.workspace is not None) and (args.domains is not None):
        if args.elastic:
            new_hosts = 0
            for domain in args.domains:
                results = get_crt_results(args, domain)

                for result in results:
                    success = elastic_bounty_tools.add_host(result['ip_address'], result['hostname'], "crtssl", args.workspace)

                    if success:
                        new_hosts += 1
                        print("{} new hosts added.".format(new_hosts), end="\r")
            print("{} new hosts added.".format(new_hosts))

        else:
            for domain in args.domains:
                results = get_crt_results(args, domain)
                # TODO: Actually add this hosts to DB
                # addhost = bountydb.add_host(ip.address, hostname, "crtssl", args.workspace)


def get_crt_results(args, domain):
    results = []
    new_hosts = 0

    try:
        # Make a request to crt.sh to get the list
        result = requests.get("https://crt.sh/?q=%25.{}".format(domain))
        soup = BeautifulSoup(result.text, 'html.parser')
        rows = soup.find_all("tr")

        # Ignore the first two rows as they're headers
        for row in rows[3:len(rows)]:
            tds = row.find_all("td")
            hostname = tds[3].text

            if "*" not in hostname:
                try:
                    answer = query(hostname)
                    for ip in answer.rrset:
                        results.append({"ip_address": ip.address, "hostname": hostname})
                        new_hosts += 1
                        print("{} new hosts found.".format(new_hosts), end="\r")

                except DNSException as e:
                    if args.debug:
                        print(e)
    except:
        print(traceback.format_exc())

    print("{} new hosts found.".format(new_hosts))
    return results
