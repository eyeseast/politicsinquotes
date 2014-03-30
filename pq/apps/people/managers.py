from django.db.models.query import QuerySet
from django_hstore.hstore import HStoreManager
from django_hstore.query import HStoreQuerySet
from model_utils.managers import create_pass_through_manager_for_queryset_class
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
                if getattr(name, field):
                    kwargs[field] = getattr(name, field)

        return super(PersonQuerySet, self).filter(*args, **kwargs)


PersonManager = create_pass_through_manager_for_queryset_class(HStoreManager, PersonQuerySet)