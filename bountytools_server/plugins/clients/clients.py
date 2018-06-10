"""
Used to manage bountytools clients
"""

from flask import Blueprint, request

# DO Library docs: https://github.com/koalalorenzo/python-digitalocean

clients = Blueprint('clients', __name__)


@clients.route('/list', methods=['GET'])
def clients_list():
    """
    List available bountytools clients
    :return:
    """


@clients.route('/ping', methods=['POST'])
def clients_ping():
    """
    Ping bountytools clients to test connectivity
    :return:
    """


@clients.route('/register', methods=['POST'])
def clients_register():
    """
    Register a new client to be available
    :return:
    """


@clients.route('/destroy/<client_id>', methods=['POST'])
def clients_destroy(client_id):
    """
    Destroy a client and remove it from availability
    :return:
    """
