import os

import dj_database_url
from fabric.api import *

# names
env.default_db_name = "quotes"
env.project_name = "pq"
env.settings_module = os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pq.settings')

# one db configuration everywhere from DATABASE_URL
env.db = dj_database_url.config(default='postgres://localhost/%s' % env.default_db_name)

# paths
env.base = os.path.realpath(os.path.dirname(__file__)) # where this fabfile lives
env.project_root = os.path.join(env.base, env.project_name) # settings dir
env.ve = os.path.dirname(env.base) # one above base

# executables
env.python = os.path.join(env.ve, 'bin', 'python')
env.manage = "%(python)s %(base)s/manage.py" % env

env.exclude_requirements = set([
    'wsgiref', 'readline', 'ipython',
    'git-remote-helpers',
])


def rm_pyc():
    "Clear all .pyc files that might be lingering"
    local("find . -name '*.pyc' -print0|xargs -0 rm", capture=False)

 
def freeze():
    """
    pip freeze > requirements.txt, excluding virtualenv clutter
    """
    reqs = local('pip freeze', capture=True).split('\n')
    reqs = [r for r in reqs if r.split('==')[0] not in env.exclude_requirements]
    reqs = '\n'.join(reqs)
 
    with open('requirements.txt', 'wb') as f:
        f.write(reqs)
 
    print reqs


# Database management
# todo: add other db params from DATABASE_URL

def drop_database():
    "Drop database. Don't do this by accident."
    with settings(warn_only=True):
        local('dropdb %(NAME)s' % env.db)


def create_database():
    "Create our local database."
    local('createdb %(NAME)s' % env.db)
    local('psql -c "CREATE EXTENSION IF NOT EXISTS hstore" -d %(NAME)s' % env.db)


def reset():
    "Drop and recreate the local database."
    rm_pyc()
    drop_database()
    create_database()
    migrate()


def migrate():
    "Run manage.py syncdb and manage.py migrate"
    manage('syncdb --noinput')
    manage('migrate')


def manage(cmd):
    """
    Run a Django management command in this VE.
    Useful in other fab commands.
    """
    local('%s %s' % (env.manage, cmd))


def load_congress():
    """
    Load current members of Congress
    """
    from pq.apps.people import load
    
    load.congress()


def load_tumblr():
    """
    Load quotes from Tumblr.
    """
    from pq.apps.quotes.load import tumblr_ingest

    tumblr_ingest()

