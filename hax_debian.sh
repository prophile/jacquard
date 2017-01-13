#!/bin/bash
set -e
fpm -s python \
    -t deb \
    --python-bin python3 \
    --python-package-name-prefix python3 \
    -a all \
    -m "Alistair Lynn <alistair@thread.com>" \
    --deb-compression xz \
    --deb-suggests python3-etcd \
    --deb-suggests python3-sqlalchemy \
    --deb-suggests python3-psycopg2 \
    -d python3 \
    --force \
    jacquard-split

