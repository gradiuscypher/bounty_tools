#!/usr/bin/env python

from flask import Flask
from plugins.digitalocean.digitalocean import digitalocean

# Create the Flask app
app = Flask(__name__)

# Register Blueprint views
# DigitalOcean Plugin for connectivity management
app.register_blueprint(digitalocean, url_prefix='/digitalocean')

# Start the API
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
