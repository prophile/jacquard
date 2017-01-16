#!/bin/bash
set -e
fpm -s python \
    -t deb \
    --name jacquard \
    --python-bin /usr/bin/python3 \
    --python-package-name-prefix python3 \
    --python-install-lib /usr/lib/python3/dist-packages \
    -a all \
    -m "Alistair Lynn <alistair@thread.com>" \
    --deb-compression xz \
    --deb-suggests python3-etcd \
    --deb-suggests python3-sqlalchemy \
    --deb-suggests python3-psycopg2 \
    --deb-suggests gunicorn3 \
    -d python3 \
    -d python3-pkg-resources \
    -d python3-redis \
    -d python3-werkzeug \
    -d python3-dateutil \
    -d python3-yaml \
    --no-auto-depends \
    --force \
    jacquard-split

