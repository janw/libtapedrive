import logging

logger = logging.getLogger(__name__)


class Podcast:
    title = ""
    subtitle = ""
    feed_url = ""
    fetched = ""
    author = ""
    language = ""
    url = ""
    itunes_type = ""
    itunes_explicit = False
    generator = ""
    summary = ""
    episodes = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __str__(self):
        return self.title

    def __repr__(self):
        return f'<Podcast(title="{self.title}" episodes={len(self)})>'

    def __len__(self):
        return len(self.episodes)

    def __iter__(self):
        return iter(self.episodes)

    @classmethod
    def from_feed(cls, feed_url, pages=True):
        pass


class PodcastList(list):
    @classmethod
    def from_opml(cls, opml_file):
        pass
