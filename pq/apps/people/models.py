from django.db import models
from django.utils.text import slugify

from django_hstore import hstore
from model_utils import Choices
from model_utils.models import TimeStampedModel
from nameparser import HumanName

from .managers import PersonManager
from .parties import PARTIES


class Person(TimeStampedModel):
    """
    People in the news who get quoted saying things.
    """
    # static properties
    GENDERS = Choices(
        ('female', 'Female'),
        ('male', 'Male'),
    )

    PARTIES = Choices(*PARTIES)

    NAME_FIELDS = ('first', 'middle', 'last', 'suffix')

    public = models.BooleanField(default=False)

    # name
    first = models.CharField('First name', max_length=100)
    middle = models.CharField('Middle name', max_length=100, blank=True)
    last = models.CharField('Last name', max_length=100)
    suffix = models.CharField('Suffix', max_length=10, blank=True)
    nickname = models.CharField('Nickname', max_length=100, blank=True)

    slug = models.SlugField(unique=True)

    # nicities
    title = models.CharField(max_length=255, blank=True,
        help_text="How is this person commonly referred in the news. "
                  "Example: Former secratary of state.")

    display = models.CharField('Display', max_length=255, blank=True,
        help_text="How to display this person's name. "
                  "Can be a template, for example: "
                  "Sen. {first} {last}")

    # metadata
    gender = models.CharField(max_length=10, blank=True, choices=GENDERS)
    party = models.CharField(max_length=50, blank=True, choices=PARTIES)
    bio = models.TextField(blank=True)

    # links
    links = hstore.DictionaryField(blank=True, null=True,
        help_text="Links to external resources and IDs, ex: bioguide")

    # todo images

    objects = PersonManager()

    class Meta:
        ordering = ('last', 'first')
        verbose_name_plural = "people"

    def __unicode__(self):
        return self.name

    # name parsing
    def _get_name(self):
        "Join name parts into one string"
        parts = [getattr(self, f) for f in self.NAME_FIELDS]
        parts = filter(bool, parts)
        return u" ".join(parts)

    def _set_name(self, name):
        "Parse name parts from a name string"
        name = HumanName(name)
        self.first = name.first
        self.middle = name.middle
        self.last = name.last
        self.suffix = name.suffix

    name = property(_get_name, _set_name)

    def _clean_name_fields(self):
        "Strip whitespace from name fields + display + nickname"
        for part in self.NAME_FIELDS + ('display', 'nickname'):
            field = getattr(self, part) or u""
            setattr(self, part, field.strip())

    def get_display_name(self):
        """
        Either name or interpolated display. Allows nickname too.
        """
        if self.display:
            parts = dict((f, getattr(self, f)) for f in self.NAME_FIELDS + ('nickname',))
            return self.display.format(**parts)

        return self.name

    def save(self, *args, **kwargs):
        "Make sure we slugify before saving."
        self._clean_name_fields()
        if not self.slug:
            self.slug = self.slugify()
        super(Person, self).save(*args, **kwargs)

    def slugify(self, n=0):
        "Make a slug, ensuring no dupes."
        slug = slugify(self.name)
        if n:
            slug = "%s-%i" % (slug, n)
        try:
            Person.objects.get(slug__iexact=slug)
            return self.slugify(n + 1)
        except Person.DoesNotExist:
            return slug