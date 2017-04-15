import elasticsearch
import traceback
import paramiko
import sqlite3
import configparser
from datetime import datetime
from connectivity import do_wrapper


# Grab config for ES host
config = configparser.RawConfigParser()
config.read("config.conf")
elastic_host = config.get("Elastic", "host")

elastic = elasticsearch.Elasticsearch([elastic_host])


def add_args(parser):
    parser.add_argument("--elastic", help="All importing should use Elasticsearch", action="store_true")
    parser.add_argument("--esimport", help="Import the workspace into Elasticsearch", action="store_true")


def parse_args(args, config):
    if args.esimport:
        if args.workspace is not None:
            reconng_import(args, config)


def add_host(ip_address, hostname, source, workspace, time_range="7d"):
    # Check if the host/ip combination is already in Elasticsearch
    es_query = {
        "query": {
            "bool": {
                "must": [
                    {"range": {"timestamp": {"gte": "now-{}".format(time_range), "lte": "now"}}},
                    {"term": {"ip_address": ip_address}},
                    {"term": {"hostname": hostname}},
                ],
            }
        }
    }
    result = elastic.search(index="bug_bounty", doc_type="host", body=es_query)

    if result['hits']['total'] <= 0:
        body = {"ip_address": ip_address, "hostname": hostname, "source": source, "workspace": workspace,
                "timestamp": datetime.utcnow()}
        elastic.index(index="bug_bounty", doc_type="host", body=body)

        return True
    return False


def add_port(ip_address, port, source, workspace, time_range="7d"):
    # Check if the port/ip combination is already in Elasticsearch
    es_query = {
        "query": {
            "bool": {
                "must": [
                    {"range": {"timestamp": {"gte": "now-{}".format(time_range), "lte": "now"}}},
                    {"term": {"ip_address": ip_address}},
                    {"term": {"port": port}},
                ],
            }
        }
    }
    result = elastic.search(index="bug_bounty", doc_type="port", body=es_query)

    if result['hits']['total'] <= 0:
        body = {"ip_address": ip_address, "port": port, "source": source, "workspace": workspace,
                "timestamp": datetime.utcnow()}
        elastic.index(index="bug_bounty", doc_type="port", body=body)

        return True
    return False


def get_hosts(workspace, time_range="7d"):
    # Query for first set of hosts
    es_query = {
        "from": 0, "size": 100,
        "query": {
            "bool": {
                "must": [
                    {"range": {"timestamp": {"gte": "now-{}".format(time_range), "lte": "now"}}},
                    {"term": {"workspace": workspace}},
                ],
            }
        }
    }
    result = elastic.search(index="bug_bounty", doc_type="host", body=es_query, scroll="2m")
    sid = result['_scroll_id']
    scroll_size = result['hits']['total']

    # Scroll the results
    while scroll_size > 0:
        result = elastic.scroll(scroll_id=sid, scroll="2m")
        sid = result['_scroll_id']
        scroll_size = len(result['hits']['hits'])
        print(result['hits']['hits'][0]['_source']['ip_address'])


def get_unique_ips(workspace, time_range="7d"):
    # Query for first set of hosts
    es_query = {
        "from": 0, "size": 100,
        "query": {
            "bool": {
                "must": [
                    {"range": {"timestamp": {"gte": "now-{}".format(time_range), "lte": "now"}}},
                    {"term": {"workspace": workspace}},
                ],
            }
        }
    }
    result = elastic.search(index="bug_bounty", doc_type="host", body=es_query)
    total_results = result['hits']['total']

    # Query for aggregation results
    es_query = {
        "from": 0, "size": 10,
        "aggs": {
            "ip_addresses": {
                "terms": {"field": "ip_address", "size": total_results+10}
            }
        },
        "query": {
            "bool": {
                "must": [
                    {"range": {"timestamp": {"gte": "now-{}".format(time_range), "lte": "now"}}},
                    {"term": {"workspace": workspace}},
                ],
            }
        }
    }
    result = elastic.search(index="bug_bounty", doc_type="host", body=es_query)
    return result['aggregations']['ip_addresses']['buckets']


def reconng_import(args, config):
    workspace = args.workspace

    # If we're given --droplet, collect the DB remotely
    # Otherwise assume the file is already local
    if args.droplet is not None:
        droplet = do_wrapper.get_droplet(args.droplet, config)

        # Setup SSH
        ssh_key_filename = config.get("DigitalOcean", "ssh_key_filename")
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        print("Connecting to the droplet...")
        ssh.connect(droplet.ip_address, username="root", key_filename=ssh_key_filename)

        # Collect recon-ng db file
        print("Downloading recon-ng db for {}".format(workspace))
        sftp = ssh.open_sftp()
        sftp.chdir("/root/.recon-ng/workspaces/{}".format(workspace))
        sftp.get("data.db", "{}.db".format(workspace))

    # Build the DB and create session object and connect to downloaded db
    conn = sqlite3.connect('{}.db'.format(workspace))
    cursor = conn.cursor()

    # Iterate through recon-ng db and add host data to recon.db
    print("Pulling data from recon-ng db to local db...")
    new_hosts = 0
    duplicate_hosts = 0

    query = "select * from hosts group by ip_address, host"
    total_host_count = cursor.execute("select count(host) from hosts").fetchone()[0]
    print("{} total hosts in db...".format(total_host_count))
    for row in cursor.execute(query):
        hostname = str(row[0])
        ip_address = str(row[1])
        source = str(row[6])
        add_success = add_host(ip_address, hostname, source, workspace)

        if add_success:
            new_hosts += 1
        else:
            duplicate_hosts += 1

        print("{} new hosts, {} duplicate hosts".format(new_hosts, duplicate_hosts), end="\r")
    print("{} new hosts, {} duplicate hosts".format(new_hosts, duplicate_hosts))


def create_index():
    try:
        host_mapping = {
            "host": {
                "properties": {
                    "ip_address": {"type": "ip"},
                    "source": {"type": "string", "index": "not_analyzed"},
                    "workspace": {"type": "string", "index": "not_analyzed"},
                    "hostname": {"type": "string", "index": "not_analyzed"},
                    "timestamp": {"type": "date"},
                }
            }
        }

        port_mapping = {
            "port": {
                "properties": {
                    "ip_address": {"type": "ip"},
                    "source": {"type": "string", "index": "not_analyzed"},
                    "workspace": {"type": "string", "index": "not_analyzed"},
                    "port": {"type": "integer"},
                    "timestamp": {"type": "date"},
                }
            }
        }

        shodan_metadata_mapping = {
            "shodan_metadata": {
                "properties": {
                    "ip_address": {"type": "ip"},
                    "source": {"type": "string", "index": "not_analyzed"},
                    "workspace": {"type": "string", "index": "not_analyzed"},
                    "hostname": {"type": "string", "index": "not_analyzed"},
                    "timestamp": {"type": "date"},
                }
            }
        }

        elastic.indices.create("bug_bounty")
        elastic.indices.put_mapping(index="bug_bounty", doc_type="host", body=host_mapping)
        elastic.indices.put_mapping(index="bug_bounty", doc_type="port", body=port_mapping)
        elastic.indices.put_mapping(index="bug_bounty", doc_type="shodan_metadata", body=shodan_metadata_mapping)

    except:
        traceback.print_exc()
