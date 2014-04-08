from django.contrib import admin

from .models import Topic, Quote, Storyline, StorylineQuote

class TopicAdmin(admin.ModelAdmin):
	prepopulated_fields = {'slug': ('name',)}


class QuoteAdmin(admin.ModelAdmin):

	list_display = ('speaker', 'text', 'source_title', 'datetime', 'added_by')


admin.site.register(Quote, QuoteAdmin)
admin.site.register(Storyline)
