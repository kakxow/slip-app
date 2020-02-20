#!/bin/sh
exec venv/bin/gunicorn -b :5000 --access-logfile - --error-logfile - slip_app:app
