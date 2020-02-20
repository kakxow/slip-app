import setuptools


config = {
    'name': 'pos_slips',
    'version': '0.1a',
    'packages': [
        'flask_app',
        'slip'
    ],
    'scripts': [
        'run_run.py',
        'PIKTA_pos.py',
    ],
    'install_requires': [
        'flask',
        'wtforms',
        'sqlalchemy',
        'flask-sqlalchemy',
        'flask-wtf',
        'loguru',
        'python-dotenv',
    ],
    'author': 'Max Sukhanov',
    'author_email': 'kakxow@gmail.com',
    'description': 'Web-view, BD and parser for Svyaznoy POS-terminal slips',
    'url': 'https://github.com/kakxow/slip_DB',
    'classifiers': [
        "Programming Language :: Python :: 3",
        "Operating System :: Windows",
    ],
}

setuptools.setup(**config)
