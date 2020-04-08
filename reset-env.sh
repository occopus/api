#!/bin/bash

PDIR=env/occo

echo "Reseting '$PDIR'"

rm -rf "$PDIR"

virtualenv -p python3 "$PDIR"
source "$PDIR"/bin/activate
pip install -r requirements_test.txt --trusted-host pip.lpds.sztaki.hu

#cat /etc/grid-security/certificates/*.pem >> $(python -m requests.certs)

set +ex
echo "It's dangerous to go alone. Take these:"
echo "source '$PDIR/bin/activate'"
echo "nosetests"
