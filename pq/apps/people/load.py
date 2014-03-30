"""
Various loader scripts for people.
"""
import logging

import requests
import yaml

from .models import Person

GENDER_MAP = {
    'f': 'female',
    'female': 'female',
    'fem': 'female',

    'm': 'male',
    'male': 'male',
}

log = logging.getLogger(__name__)


def congress(public=True):
    """
    Load current members of Congress using theunitedstates.io/congress-legislators

    Full repo here: https://github.com/unitedstates/congress-legislators

    Current members are here (raw version): 
        https://raw.githubusercontent.com/unitedstates/congress-legislators/master/legislators-current.yaml

    Everything is in yaml.

    Uniqueness is based on Person.links['bioguide']
    This only applies to current and former members of congress.
    """
    url = "https://raw.githubusercontent.com/unitedstates/congress-legislators/master/legislators-current.yaml"
    req = requests.get(url)

    members = yaml.load(req.content)

    for member in members:

        # mise en place
        name = dict((k, v) for k, v in member['name'].items() if k in Person.NAME_FIELDS)
        term = member['terms'][-1] # most recent term
        ids = member['id']
        
        # get or create a person, based on name fields
        try:
            person = Person.objects.get(links__contains={'bioguide': ids['bioguide']})
            created = False
        except Person.DoesNotExist:
            params = name.copy()
            params['links'] = ids
            person = Person.objects.create(**params)
            created = True

        log_created(person, created)

        # update attributes
        person.public = public
        person.nickname = member['name'].get('nickname')
        person.display = member['name'].get('official_full')
        person.gender = GENDER_MAP[member['bio']['gender'].lower()]
        person.party = term['party'].lower()

        person.save()


def log_created(obj, created):
    """
    Logs object creation.
    """
    if created:
        log.debug('%s created: %s', obj.__class__.__name__, obj)

    return obj, created
