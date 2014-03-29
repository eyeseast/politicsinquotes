import datetime
from django.conf import settings
from django.db import models
from django.utils.text import slugify

from model_utils import Choices
from model_utils.models import TimeStampedModel

from pq.apps.people.models import Person

class Topic(TimeStampedModel):
    """
    A topic, tied to quotes and storylines
    """
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ('name',)

    def __unicode__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self.slugify()
        super(Topic, self).save(*args, **kwargs)

    def slugify(self):
        return slugify(self.name)


class Quote(TimeStampedModel):
    """
    A quote, said by a person, from a source URL

    Quotes can be sorted chronologically, and organized
    by topic and speaker.

    Every quote must have a source URL. Nothing should appear
    here first.
    """
    added_by = models.ForeignKey(settings.AUTH_USER_MODEL, 
        related_name='quotes')

    speaker = models.ForeignKey(Person, related_name='quotes')
    datetime = models.DateTimeField()

    text = models.TextField(
        help_text="The quote itself, with no attribution or surrounding quote marks.")

    source_url = models.URLField()
    source_title = models.CharField(max_length=500, blank=True)

    # topics
    topics = models.ManyToManyField(Topic, related_name='quotes',
        blank=True, null=True)

    class Meta:
        # reverse chron
        get_latest_by = "datetime"
        ordering = ('-datetime',)

    def __unicode__(self):
        return u"{0}: {1}".format(self.speaker.name, self.text)


class Storyline(TimeStampedModel):
    """
    A storyline is our core editorial model. 
    
    It frames and (minimally) explains a story, which is illustrated
    through quotes.

    The point is to show: Here's what people in power are saying about this thing.

    A user can create a storyline and add quotes, with ordering 
    (defaults to reverse chron).

    A storyline can be saved in draft, shared privately (like private gists)
    or made public.
    """
    STATUS = Choices(
        ('draft', 'Draft'), # not visibile
        ('published', 'Published'), # visible, public
        ('private', 'Private') # visible only with a link
    )

    author = models.ForeignKey(settings.AUTH_USER_MODEL, 
        related_name='storylines')

    title = models.CharField(max_length=500)
    slug = models.SlugField(db_index=True)
    datetime = models.DateTimeField(default=datetime.datetime.now)

    text = models.TextField(blank=True)

    quotes = models.ManyToManyField(Quote,
        related_name='storylines',
        through='StorylineQuote',
        blank=True, null=True) # so we can save before adding quotes

    # topics, should be union of quote topics
    # can we do this without creating another table?
    topics = models.ManyToManyField(Topic, related_name='storylines',
        blank=True, null=True)

    # todo photos

    class Meta:
        # reverse chron by default
        get_latest_by = "datetime"
        ordering = ('-datetime',)

    def __unicode__(self):
        return self.title

    def save(self, *args, **kwargs):
        "Make a slug before saving"
        if not self.slug:
            self.slug = slugify(self.title)
        super(Storyline, self).save(*args, **kwargs)


class StorylineQuote(models.Model):
    """
    A through-model connecting quotes to storylines, allowing ordering
    """
    quote = models.ForeignKey(Quote)
    storyline = models.ForeignKey(Storyline)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ('order', 'quote')

    