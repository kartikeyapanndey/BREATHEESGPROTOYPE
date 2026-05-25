#!/usr/bin/env bash
# exit on error
set -o errexit

cd frontend
npm install
npm run build
cd ..

cd breathe_backend
pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate
