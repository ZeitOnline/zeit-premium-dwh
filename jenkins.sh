#!/bin/sh -xe

. /opt/credentials/govc/credentials.env.sh
vagrant up --provider vsphere --provision

trap "vagrant destroy --force" EXIT

vagrant ssh -c "cd /vagrant && sudo python3 setup.py sdist" -- -q

vagrant ssh-config > ${WORKSPACE}/vagrant.ssh-config
scp -F ${WORKSPACE}/vagrant.ssh-config default:/vagrant/dist/\*.tar.gz ${WORKSPACE}/

devpi use https://devpi.zeit.de/premium-dwh/default
devpi login premium-dwh --password 'premium-dwh'
devpi upload *.tar.gz
