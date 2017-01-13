#!/bin/bash
set -e
fpm -s python \
    -t deb \
    --python-bin /usr/bin/python3 \
    --python-package-name-prefix python3 \
    -a all \
    -m "Alistair Lynn <alistair@thread.com>" \
    --deb-compression xz \
    --deb-suggests python3-etcd \
    --deb-suggests python3-sqlalchemy \
    --deb-suggests python3-psycopg2 \
    --deb-suggests gunicorn3 \
    -d python3 \
    -d python3-pkg-resources \
    --force \
    jacquard-split

