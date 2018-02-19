# Leverages the recon-ng RPC interface, as I don't want to import the recon-ng libraries here,
# and this makes it more portable.

import jsonrpclib
import traceback
from flask import Blueprint, request, jsonify

reconng = Blueprint('callback', __name__)


# Run a recon-ng module provided in the json POST
@reconng.route('/run', methods=['POST'])
def run():

    # Setup the jsonrpclib for the recon-ng RPC server, stop the API if it cannot connect to the RPC server.
    try:
        client = jsonrpclib.Server('http://localhost:4141')
        sid = client.init()

        # Get the configuration from JSON POST
        content = request.get_json()
        target_module = content['module']
        target_domain = content['domain']
        print(target_domain, target_module)

        # Set the target domain
        client.add('domains', target_domain, sid)
        print(client.show('domains', sid))
        client.use(target_module, sid)

        # Execute the requested module and return the results
        results = client.run(sid)

        return jsonify(results)

    except:
        return traceback.format_exc(), 500
