from django.contrib import admin

from .models import Person

class PersonAdmin(admin.ModelAdmin):
	"Admin for people. Deliberately basic."

	#prepopulated_fields = {'slug': Person.NAME_FIELDS}


admin.site.register(Person, PersonAdmin)