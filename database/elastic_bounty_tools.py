import elasticsearch
import traceback
import configparser
from datetime import datetime


# Grab config for ES host
config = configparser.RawConfigParser()
config.read("config.conf")
elastic_host = config.get("Elastic", "host")

elastic = elasticsearch.Elasticsearch([elastic_host])


def add_args(parser):
    parser.add_argument("--elastic", help="All importing should use Elasticsearch", action="store_true")


def parse_args(args, config):
    pass


def add_host(ip_address, hostname, source, workspace, time_range="7d"):
    if (ip_address is not None) and (hostname is not None):
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
            elastic.indices.refresh(index="bug_bounty")
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
        elastic.indices.refresh(index="bug_bounty")
        return True
    return False


def add_field_to_ip(workspace, ip_address, field_name, field_value, time_range="7d"):
    # ref: https://www.elastic.co/guide/en/elasticsearch/reference/current/docs-update.html
    # ref: https://www.elastic.co/guide/en/elasticsearch/reference/current/docs-update-by-query.html - version conflict
    upquery = {
        'conflicts': 'proceed',
        'query': {
            'bool': {
                'must': [
                    {'range': {'timestamp': {'gte': 'now-{}'.format(time_range), 'lte': 'now'}}},
                    {'term': {'workspace': workspace}},
                    {'term': {'ip_address': ip_address}}
                ]}
        },
        'script': {
            'inline': 'ctx._source.{} = "{}"'.format(field_name, field_value),
            'lang': 'painless'
        }
    }
    elastic.update_by_query(index="bug_bounty", doc_type="host", body=upquery)


def remove_field_from_ip(workspace, ip_address, field_name, time_range="7d"):
    # ref: https://www.elastic.co/guide/en/elasticsearch/reference/current/docs-update.html
    upquery = {
        'conflicts': 'proceed',
        'query': {
            'bool': {
                'must': [
                    {'range': {'timestamp': {'gte': 'now-{}'.format(time_range), 'lte': 'now'}}},
                    {'term': {'workspace': workspace}},
                    {'term': {'ip_address': ip_address}}
                ]}
        },
        'script': {
            'inline': 'ctx._source.remove("{}")'.format(field_name),
            'lang': 'painless'
        }
    }
    elastic.update_by_query(index="bug_bounty", doc_type="host", body=upquery)


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
    if workspace == "":
        es_query = {
            "from": 0, "size": 10000,
            "query": {
                "bool": {
                    "must": [
                        {"range": {"timestamp": {"gte": "now-{}".format(time_range), "lte": "now"}}},
                    ],
                }
            }
        }
    else:
        es_query = {
            "from": 0, "size": 10000,
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
    if workspace == "":
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
                    ],
                }
            }
        }
        result = elastic.search(index="bug_bounty", doc_type="host", body=es_query)
        return result['aggregations']['ip_addresses']['buckets']
    else:
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
