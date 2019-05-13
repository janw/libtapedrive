COVER_IMAGE_SIZE = (1000, 1000)

# Mappings of usable segment => field name
AVAILABLE_PODCAST_SEGMENTS = {
    "podcast_slug": "slug",
    "podcast_type": "itunes_type",
    "podcast_title": "title",
    "podcast_subtitle": "subtitle",
    "podcast_author": "author",
    "podcast_language": "language",
    "podcast_explicit": "itunes_explicit",
    "podcast_updated": "updated",
}

AVAILABLE_EPISODE_SEGMENTS = {
    "episode_slug": "slug",
    "episode_id": "id",
    "episode_date": "published",
    "episode_number": "itunes_episode",
    "episode_type": "itunes_episodetype",
    "episode_title": "title",
}

UNIQUE_EPISODE_SEGMENTS = [
    "episode_slug",
    "episode_id",
    "episode_date",
    "episode_number",
    "episode_title",
]

ALL_VALID_SEGMENTS = {**AVAILABLE_EPISODE_SEGMENTS, **AVAILABLE_PODCAST_SEGMENTS}
