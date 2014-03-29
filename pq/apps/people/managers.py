from django.db.models.query import QuerySet
from django_hstore.query import HStoreQuerySet
from model_utils.managers import PassThroughManager
from nameparser import HumanName


class PersonQuerySet(HStoreQuerySet):

    def public(self):
        return self.filter(public=True)

    def filter(self, *args, **kwargs):
        """
        Override default filter method to parse out `name` argument
        into consituent fields. Also works for `get` and `get_or_create`.
        """
        from .models import Person
        if "name" in kwargs:
            name = kwargs.pop('name')
            name = HumanName(name)
            for field in Person.NAME_FIELDS:
                kwargs[field] = getattr(name, field)

        return super(PersonQuerySet, self).filter(*args, **kwargs)


PersonManager = PassThroughManager.for_queryset_class(PersonQuerySet)