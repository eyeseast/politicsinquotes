"""
Various loader scripts for people.
"""
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

def congress(public=True):
    """
    Load current members of Congress using theunitedstates.io/congress-legislators

    Full repo here: https://github.com/unitedstates/congress-legislators

    Current members are here (raw version): 
        https://raw.githubusercontent.com/unitedstates/congress-legislators/master/legislators-current.yaml

    Everything is in yaml.

    Uniqueness is based on name fields, for now. Bioguide is a better ID, 
    but it's only for past and present members of Congress.
    """
    url = "https://raw.githubusercontent.com/unitedstates/congress-legislators/master/legislators-current.yaml"
    req = requests.get(url)

    members = yaml.load(req.content)

    for member in members:

        # mise en place
        name = dict((k, v) for k, v in member['name'].items() if k in Person.NAME_FIELDS)
        term = member['terms'][-1] # most recent term
        
        # get or create a person, based on name fields
        person, created = Person.objects.get_or_create(**name)

        # update attributes
        person.public = public
        person.nickname = member['name'].get('nickname')
        person.display = member['name'].get('official_full')
        person.gender = GENDER_MAP[member['bio']['gender'].lower()]
        person.party = term['party'].lower()

        person.save()

        print person.name
