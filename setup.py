from setuptools import setup

install_requires = [
    'couchdb',
    'dateparser',
    'pbkdf2',
    'requests',
    'requests_cache',
    'pytz',
    'iso8601',
    'pyminizip',
    'arrow',
    'boto3',
    'Jinja2',
    'systemd-python',
    'PyYaml',
    'ExtendedJournalHandler==1.0.0'
]

test_requires = install_requires + [
    'mock',
]

setup(
    name='reports',
    version='0.0.1',
    packages=[
        'reports',
    ],
    author='Quintagroup, Ltd.',
    author_email='info@quintagroup.com',
    license='Apache License 2.0',
    url='https://github.com/openprocurement/reports',
    entry_points={
        'console_scripts': [
            'bids = reports.utilities.bids:run',
            'tenders = reports.utilities.tenders:run',
            'refunds = reports.utilities.refunds:run',
            'invoices = reports.utilities.invoices:run',
            'init = reports.db_init:run',
            'zip = reports.utilities.zip:run',
            'send = reports.utilities.send:run',
        ]
    },
    include_package_data=True,
    zip_safe=False,
    install_requires=install_requires,
    tests_require=test_requires,
    test_suite='reports.tests.main.suite',
    extras_require={'test': test_requires},
)
