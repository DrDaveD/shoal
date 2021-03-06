#!/usr/bin/env bash

#
# This script installs shoal onto SL6 and configures
# it to connect to the production shoal instance used
# by the ATLAS Cloud group.
#
# Author Ian Gable <igable@uvic.ca>
#

curl http://shoal.heprc.uvic.ca/repo/shoal-sl6x.repo -o /etc/yum.repos.d/shoal.repo

# importing RPM signing key for Shoal RPMs
rpm --import http://hepnetcanada.ca/pubkeys/igable.asc

echo -e "\nAttempting install of EPEL repository\n"
echo "The following could fail without a problem on the SLC varient and if you"
echo "have EPEL installed already\n"

yum install -y yum-conf-epel

# install the agent
yum install -y shoal-agent

echo "Setting the config to point to shoal.heprc.uvic.ca"
sed -i 's/localhost/shoal.heprc.uvic.ca/g' /etc/shoal/shoal_agent.conf

echo -e "\n\nTo start shoal agent execute:"
echo -e "  service shoal-agent start\n"
