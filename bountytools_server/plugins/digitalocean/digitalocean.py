"""
API endpoints created for controlling DigitalOcean tasks
"""
import digitalocean
from flask import Blueprint, request

# DO Library docs: https://github.com/koalalorenzo/python-digitalocean

doconnector = Blueprint('doconnector', __name__)


@doconnector.route('/droplets/list', methods=['GET'])
def droplets_list():
    """
    List the DO droplets available that are tagged with the correct client tag
    :return:
    """


@doconnector.route('/droplets/create', methods=['POST'])
def droplets_create():
    """
    Create a DO droplet and install the required bounty client software and tools
    :return:
    """


@doconnector.route('/droplets/destroy/<droplet_id>', methods=['POST'])
def droplets_destroy(droplet_id):
    """
    Destroy the target droplet ID
    :return:
    """
