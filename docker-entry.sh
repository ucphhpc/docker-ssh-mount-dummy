#!/bin/bash

# Generate a new set of host SSH keys for the OpenSSH server
echo "Reconfiguring OpenSSH Server"
/usr/sbin/dpkg-reconfigure openssh-server

echo "Running the OpenSSH Server"
# Launch the main.py script that starts the OpenSSH server daemon
python3 main.py