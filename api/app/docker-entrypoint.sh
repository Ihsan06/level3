#!/bin/sh

set -e

# Migrate and upgrade the database during container start
flask db migrate
flask db upgrade

# Docker-entrypoint for starting the application
gunicorn -c gunicorn.config.py wsgi:app