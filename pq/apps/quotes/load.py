"""
Loader scripts for quotes, including Tumblr import.
"""
import datetime
import logging
import os

from calais import Calais
from pytumblr import TumblrRestClient

from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.timezone import utc

from pq.apps.people.models import Person
from .models import Topic, Quote

CALAIS_API_KEY = settings.CALAIS_API_KEY
TUMBLR_API_KEY = settings.TUMBLR_API_KEY
TUMBLR_BLOG = settings.TUMBLR_BLOG

calais = Calais(CALAIS_API_KEY)
tumblr = TumblrRestClient(TUMBLR_API_KEY)

log = logging.getLogger(__name__)

def tumblr_ingest(blog=TUMBLR_BLOG, **kwargs):
    """
    Load quotes from tumblr blog. See fields available here:
        https://www.tumblr.com/docs/en/api/v2#quote-posts

    Context is in post['source'], which gets passed to get_speaker.
    
    """
    kwargs.setdefault('limit', 50)
    quotes = tumblr.posts(blog, type='quote', **kwargs)
    default_user = get_default_user()

    for post in quotes['posts']:
        defaults = {
            'datetime': datetime.datetime.utcfromtimestamp(post['timestamp']).replace(tzinfo=utc),
            'added_by': default_user,
            'context': post['source'],
            'source_url': post['source_url'],
            'source_title': post['source_title'],
        }

        speaker = get_speaker(post)
        if speaker:
            speaker, created = Person.objects.get_or_create(name=speaker)
            log_created(speaker, created)

        defaults['speaker'] = speaker

        # uniqueness based on text
        # todo find a better way
        quote, created = Quote.objects.get_or_create(
            text=post['text'].strip(), defaults=defaults)

        log_created(quote, created)


def get_default_user():
    User = get_user_model()
    return User.objects.get(username=settings.DEFAULT_USER)


def get_speaker(quote):
    """
    Get the most relevant person from a Calais response
    """
    resp = calais.analyze(quote['source'])
    people = [e for e in resp.entities if e['_type'] == 'Person']
    
    if people:
        people.sort(key=lambda p: p['relevance'], reverse=True)
        return people[0]['name']


def log_created(obj, created):
    """
    Logs object creation.
    """
    if created:
        log.debug('%s created: %s', obj.__class__.__name__, obj)

    return obj, created