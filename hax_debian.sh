#!/bin/bash
set -e
export JACQUARD_DEBIAN_HACK=1
fpm -s python \
    -t deb \
    --name jacquard \
    --python-bin /usr/bin/python3 \
    --python-package-name-prefix python3 \
    --python-install-lib /usr/lib/python3/dist-packages \
    -a all \
    -m "Alistair Lynn <alistair@thread.com>" \
    --deb-compression xz \
    --deb-suggests python3-psycopg2 \
    -d "python3 (>= 3.5)" \
    -d python3-pkg-resources \
    -d python3-redis \
    -d python3-werkzeug \
    -d python3-dateutil \
    -d python3-sqlalchemy \
    -d python3-yaml \
    -d python3-waitress \
    --config-files /etc/jacquard \
    --deb-systemd jacquard.service \
    --after-install deb-jacquard-install.sh \
    --no-auto-depends \
    --force \
    .

