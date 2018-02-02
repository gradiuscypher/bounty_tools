import digitalocean
from flask import Blueprint, request

# DO Library docs: https://github.com/koalalorenzo/python-digitalocean

doconnector = Blueprint('callback', __name__)
