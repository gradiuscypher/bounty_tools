#!/usr/bin/env python

from flask import Flask
from plugins.reconng.reconng import reconng

# Create the Flask app
app = Flask(__name__)

# Register Blueprint views

# recon-ng API, leverages recon-ng's RPC server
app.register_blueprint(reconng, url_prefix='/reconng')

# Start the API
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
