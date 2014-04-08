import requests
from django.core.files.base import ContentFile
from django.db import models
from django.utils.text import slugify

from django_hstore import hstore
from model_utils import Choices
from model_utils.models import TimeStampedModel
from nameparser import HumanName
from sorl.thumbnail import ImageField, get_thumbnail

from .managers import PersonManager
from .parties import PARTIES


class PhotoBase(models.Model):
    """
    Fields and methods related to photo management,
    separated for clarity, and in case it needs 
    further separation later.

    This will probably move to its own module later.
    """

    CROP_HORZ_CHOICES = Choices(
        ('0%', "Left"),
        ('25%', "Left-center"),
        ('50%', "Center"),
        ('75%', "Right-center"),
        ('100%', "Right"),
    )
    
    CROP_VERT_CHOICES = Choices(
        ('0%', "Top"),
        ('25%', "Top-center"),
        ('50%', "Center"),
        ('75%', "Bottom-center"),
        ('100%', "Bottom"),
    )

    image = ImageField(upload_to='photos/%Y/%m',
        blank=True, null=True)

    crop_horz = models.CharField("Crop Horizontal", max_length=10, 
        choices=CROP_HORZ_CHOICES, default='50%')

    crop_vert = models.CharField("Crop Vertical", max_length=10, 
        choices=CROP_VERT_CHOICES, default='50%')

    class Meta:
        abstract = True

    def thumbnail(self):
        return self.resize('75x75').url
    
    @property
    def crop(self):
        return u"%s %s" % (self.crop_horz, self.crop_vert)
    
    def resize(self, size, **options):
        options.setdefault('crop', self.crop)
        return get_thumbnail(self.image, size, **options)

    def admin_thumbnail(self):
        img = self.resize('75x75')
        return u'<img src="{0}" height="75" width="75">'.format(img.url)
    admin_thumbnail.allow_tags = True


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
        return self.get_display_name()

    # name parsing
    def _get_name(self):
        "Join name parts into one string"
        parts = self.get_name_list()
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
            parts = self.get_name_dict()
            return self.display.format(**parts)

        return self.name

    def get_name_dict(self):
        """
        Get name fields only, as a dict (includes nickname)
        """
        return dict((f, getattr(self, f)) for f in self.NAME_FIELDS + ('nickname',))

    def get_name_list(self):
        """
        Get name fields only, as a list (excludes nickname)
        """
        return [getattr(self, f) for f in self.NAME_FIELDS]

    def get_thumbnail(self):
        pass

    def admin_thumbnail(self):
        pass

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

    def get_photo_from_usio(self, replace=False):
        """
        Ingest a photo from theunitedstates.io.
        Requires a bioguide ID stored in links.

        By default, this will not overwrite an 
        already-attached photo. Pass replace=True
        to replace an existing photo.
        """
        bioguide = self.links.get('bioguide')
        if not bioguide:
            return

        # bail out here if we have a photo and aren't replacing
        if hasattr(self, 'photo') and not replace:
            return self.photo

        url = "https://raw.githubusercontent.com/unitedstates/images/" \
              "gh-pages/congress/original/{0}.jpg".format(bioguide)

        name = "{0}.jpg".format(bioguide)

        img = requests.get(url)
        file = ContentFile(img.content)

        photo = Photo(person=self)
        photo.image.save(name, file, save=True)

        return photo


class Photo(PhotoBase, models.Model):
    """
    Profile photo for a person, based on PhotoBase
    """
    person = models.OneToOneField(Person, related_name='photo')

    def __unicode__(self):
        return self.image.name

