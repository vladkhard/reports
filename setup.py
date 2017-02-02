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
    'Jinja2'
]

test_requires = install_requires + [
    'mock',
    'pytest',
    'pytest-cov',
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
            'bids = reports.scripts.bids:run',
            'tenders = reports.scripts.tenders:run',
            'refunds = reports.scripts.refunds:run',
            'invoices = reports.scripts.invoices:run',
            'zip = reports.scripts.zip:run',
            'send = reports.scripts.send:run',
            'init = reports.db_init:run',
        ]
    },
    include_package_data=True,
    zip_safe=False,
    install_requires=install_requires,
    tests_require=test_requires,
    test_suite='reports.tests.main.suite',
    extras_require={'test': test_requires},
)
