import os

from fabric.api import *

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
