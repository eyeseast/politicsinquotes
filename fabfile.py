import os

from fabric.api import *

# names
env.db_name = "quotes"
env.project_name = "pq"

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


def drop_database():
    "Drop database. Don't do this by accident."
    with settings(warn_only=True):
        local('dropdb %(db_name)s' % env)


def create_database():
    "Create our local database."
    #local('createdb -T template_postgis %(db_name)s' % env)
    local('createdb %(db_name)s' % env)
    local('psql -c "CREATE EXTENSION hstore" -d %(db_name)s' % env)

