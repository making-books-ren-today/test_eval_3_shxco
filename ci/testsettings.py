# This file is exec'd from settings.py, so it has access to and can
# modify all the variables in settings.py.

# If this file is changed in development, the development server will
# have to be manually restarted because changes will not be noticed
# immediately.

DEBUG = False

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        # Django needs to make databases in the test mysql server
        'NAME': 'travismep',
        'USER': 'root',
        'PASSWORD': '',
        'HOST': '127.0.0.1',
        'OPTIONS': {
            # In each case, we want strict mode on to catch truncation issues
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            # Load the socket info from .my.cnf in the travis user
            'read_default_file': '~travis/.my.cnf'
        },
        'PORT': '',
        'TEST': {
                # We also want the test databse to for utf8 and the general
                # collation to keep case sensitive unicode searches working
                # as we would expect on production
                'CHARSET': 'utf8',
                'COLLATION': 'utf8_general_ci',
        },
    },
}


SOLR_CONNECTIONS = {
    'default': {
        'URL': 'http://localhost:8983/solr/',
        'COLLECTION': 's-and-co',
        'CONFIGSET': 'sandco',
        'TEST': {
            # aggressive commitWithin for test only
            'COMMITWITHIN': 750,
        }
    }
}


# required by mezzanine for unit tests
ALLOWED_HOSTS = ['*']

# secret key added as a travis build step
