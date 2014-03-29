import requests
import yaml

from django.test import TestCase

from .models import Person

PEOPLE = [
	'Barack Obama', 'Joe Biden', 'Mitch McConnell',
	'Hillary Clinton', 'John Boehner', 'Paul Ryan'
]

class PeopleTest(TestCase):
	"""
	Test that people are created correctly.
	"""
	def setUp(self):
		for name in PEOPLE:
			Person.objects.create(name=name)

	def test_total_created(self):
		"""
		Ensure that we're creating all the people we should.
		"""
		people = Person.objects.all()
		self.assertEqual(people.count(), len(PEOPLE))

	def test_get_people(self):
		"""
		Ensure that we can get people by name.
		"""
		for name in PEOPLE:
			p = Person.objects.get(name=name)
			self.assertEqual(p.name, name)

	def test_display_name(self):
		"""
		Ensure names are displayed correctly.
		"""
		mitch = Person.objects.get(name='Mitch McConnell')
		mitch.display = "Sen. {first} {last}"

		self.assertEqual('Sen. Mitch McConnell', mitch.get_display_name())


class PeopleLoadingTest(TestCase):
	"""
	Tests for people loaders
	"""
	
	def test_load_congress(self):
		"""
		Ensure that we're loading congress correctly
		"""
		from pq.apps.people import load

		url = "https://raw.githubusercontent.com/unitedstates/congress-legislators/master/legislators-current.yaml"
		req = requests.get(url)

		members = yaml.load(req.content)

		# do the actual loading
		load.congress()

		self.assertEqual(len(members), Person.objects.count())



