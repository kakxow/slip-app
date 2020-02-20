Hello!

It's slip-app - application to parse all your slips, add them to database and provide web view and API to gather info about operations or find particular operation.

How to setup:
To install and run locally: clone this repo, install required packages ```pipenv install```, set evironment variables, run the app ```pipenv run flask run```. Optionally you can use venv and pip - requirements.txt is present in the repo.
Dockerfile included to run with gunicorn in container.
Procfile included for deploy on heroku.


Environment variables to be set for successful deployment:
FLASK_APP - set to slip_app.py
SECRET_KEY - obviously
DATABASE_URL - set path for your database, defaults to example_db in db module.
DB_PASSWORD - set to restrict changes in database via API.

Optional/development:
FLASK_ENV - default for production, you can set 'development' when needed.
FLASK_DEBUG - default is 0, set 1 when choose for development env.
SQLALCHEMY_TRACK_MODIFICATIONS - set to 1 if you want to track modifications for some reason, default is 0.
JSON_AS_ASCII - default is 0, set to 1 if you plan to use other crawler.

Variables for emailing support:
Mailing won't be available if any of these variables is not set.
MAIL_SERVER
MAIL_PORT
MAIL_USE_TLS
MAIL_USERNAME
MAIL_PASSWORD


Misc:
POPPLER_PATH - set if you don't want to use poppler utils, provided with the package.
SLIP_DIR - set paths to slips, default is \\Msk-vm-slip\SLIP.
PAGE_SIZE - default is 20, for table pagination.
