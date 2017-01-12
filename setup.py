from setuptools import setup, find_packages

with open('README.rst', 'r', encoding='utf-8') as f:
    long_description = f.read()


setup(
    name='jacquard',
    version='0.1.1',
    url='https://github.com/prophile/jacquard',
    description="Split testing server",
    long_description=long_description,

    author="Alistair Lynn",
    author_email="alistair@alynn.co.uk",

    license='MIT',

    packages=find_packages(),

    classifiers=(
        'Development Status :: 2 - Pre-Alpha',
        'Environment :: Console',
        'License :: Open Source :: MIT',
        'Natural Language :: English',
        'Operating System :: POSIX',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Office/Business',
    ),

    install_requires=(
        'redis',
        'werkzeug',
    ),

    setup_requires=(
        'pytest-runner',
    ),

    tests_require=(
        'pytest',
    ),

    entry_points={
        'console_scripts': (
            'jacquard = jacquard.cli:main',
        ),
        'jacquard.storage_engines': (
            'dummy = jacquard.storage.dummy:DummyStore',
            'redis = jacquard.storage.redis:RedisStore',
            'file = jacquard.storage.file:FileStore',
        ),
        'jacquard.commands': (
            'storage-dump = jacquard.storage.commands:StorageDump',
            'storage-flush = jacquard.storage.commands:StorageFlush',
            'storage-import = jacquard.storage.commands:StorageImport',
            'set-default = jacquard.users.commands:SetDefault',
            'override = jacquard.users.commands:Override',
            'show = jacquard.users.commands:Show',
            'runserver = jacquard.service.commands:RunServer',
            'launch = jacquard.experiments.commands:Launch',
            'conclude = jacquard.experiments.commands:Conclude',
            'load-experiment = jacquard.experiments.commands:Load',
        ),
    },
)
