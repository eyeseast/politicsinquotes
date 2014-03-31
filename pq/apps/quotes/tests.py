from django.contrib.auth import get_user_model
from django.test import TestCase

from .models import Topic, Quote, Storyline, StorylineQuote
from .load import TUMBLR_BLOG, tumblr, tumblr_ingest

User = get_user_model()

class QuoteLoadingTest(TestCase):
    """
    Tests for loading quotes from external sources
    """
    
    def setUp(self):
        # create a default user
        User.objects.create_user('guynoir', 'guy@example.com')

    def test_tumblr_ingest(self):
        "Ensure tumblr ingest works"

        # get posts to test against
        quotes = tumblr.posts(TUMBLR_BLOG, type='quote', limit=10)

        # do the actual ingest
        tumblr_ingest(TUMBLR_BLOG, limit=10)

        self.assertEqual(len(quotes['posts']), Quote.objects.count())
