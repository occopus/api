#!/bin/bash

PDIR=env/occo

echo "Reseting '$PDIR'"

rm -rf "$PDIR"

virtualenv -p python3 "$PDIR"
source "$PDIR"/bin/activate
pip install -r requirements_test.txt --find-links https://pip3.lpds.sztaki.hu/packages --no-index

#cat /etc/grid-security/certificates/*.pem >> $(python -m requests.certs)

set +ex
echo "It's dangerous to go alone. Take these:"
echo "source '$PDIR/bin/activate'"
