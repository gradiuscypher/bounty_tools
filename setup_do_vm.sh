#!/bin/bash
# note: some of the libxml packages might be redundant, I need to figure out which ones are actually needed

# update packages and install new ones
apt-get update && apt-get upgrade -y
apt-get install nmap -y

# setup recon-ng
cd /root
apt-get install python-dev libxml2-dev libxslt1-dev zlib1g-dev build-essential autoconf libtool python-pip -y
git clone https://LaNMaSteR53@bitbucket.org/LaNMaSteR53/recon-ng.git
cd recon-ng
pip install -r REQUIREMENTS

# setup masscan
cd /root
apt-get install libpcap-dev -y
git clone https://github.com/robertdavidgraham/masscan
cd masscan
make
make install
