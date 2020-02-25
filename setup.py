import setuptools


setuptools.setup(
    name='parse_slips',
    version='0.1',
    py_modules=[
        'slip',
        'db',
        'config',
    ],
    install_requires=[
        'python-dotenv',
        'loguru',
        'sqlalchemy',
    ],
    author='Max Sukhanov',
    author_email='mksuhanov@gmail.com',
    description='',
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: Windows",
    ],
    entry_points={'console_scripts': ['parse_slips=run_parser:cli']}
)
