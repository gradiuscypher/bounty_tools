# Leverages the recon-ng RPC interface, as I don't want to import the recon-ng libraries here,
# and this makes it more portable.

import jsonrpclib
import traceback
from flask import Blueprint, request

reconng = Blueprint('callback', __name__)


# Setup the jsonrpclib for the recon-ng RPC server, stop the API if it cannot connect to the RPC server.
try:
    client = jsonrpclib.Server('http://localhost:4141')
    sid = client.init()

except:
    print(traceback.format_exc())
    print("The recon-ng RPC server was not started. Please start the RPC server before starting the BountyTools Client.")
    exit(1)


# Run a recon-ng module provided in the json POST
@reconng.route('/run', methods=['POST'])
def run():
    try:
        content = request.get_json()
        target_module = content['module']
        return 'Success.', 200
    except:
        print(traceback.format_exc())
        return 'Fail.', 500


# Returns the database with the recon-ng data
@reconng.route('/get_database', methods=['GET'])
def get_database():
    pass
