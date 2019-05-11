import os
import logging
from urllib.error import HTTPError, URLError

import requests
import feedparser
from tqdm import tqdm

from libtapedrive import __version__, __source__

USER_AGENT = f"Libtapedrive/{__version__} (+{__source__})"
HEADERS = {"User-Agent": USER_AGENT}

session = requests.Session()
session.headers.update(HEADERS)

logger = logging.getLogger(__name__)


class FeedResponse:
    feed_object = None
    url = ""
    next_page = None
    last_page = None

    def __init__(self, feed_object, url, next_page, last_page):
        self.feed_object = feed_object
        self.url = url
        self.next_page = next_page
        self.last_page = last_page


def fetch_feed(feed_url):
    try:
        response = session.get(feed_url, allow_redirects=True)
    except requests.exceptions.ConnectionError:
        logger.error("Connection error", exc_info=True)
        return None

    # Catch improper response
    if response.status_code >= 400:
        logger.error("HTTP error %d: %s" % (response.status_code, response.reason))
        return None

    # Try parsing the feed
    feedobj = feedparser.parse(response.content)
    if (
        feedobj["bozo"] == 1
        and type(feedobj["bozo_exception"]) is not feedparser.CharacterEncodingOverride
    ):
        logger.error("Feed is malformatted")
        return None

    if "feed" not in feedobj:
        logger.error("Feed is incomplete")
        return None

    links = feedobj["feed"].get("links", [])
    next_page = next((item for item in links if item["rel"] == "next"), {}).get("href")
    last_page = next((item for item in links if item["rel"] == "last"), {}).get("href")

    if next_page:
        logger.info("Feed has next page")

    return FeedResponse(feedobj, response.url, next_page, last_page)


def download_file(link, filename, progress=False, chunk_size=8192, overwrite=False):
    if os.path.isfile(filename) and not overwrite:
        logger.error("File at %s already exists" % filename)
        return

    # Create the subdir, if it does not exist
    directory = os.path.dirname(filename)
    if directory:
        os.makedirs(directory, exist_ok=True)

    try:
        with session.get(link, stream=True, allow_redirects=True) as response:
            response.raise_for_status()
            logger.debug("Resolved link:", response.url)

            # Check for proper content length, with resolved link
            total_size = int(response.headers.get("content-length", "0"))
            if total_size == 0:
                logger.error("Received content-length is 0")
                return
            if progress:
                pbar = tqdm(total=total_size, desc=filename, unit="B", unit_scale=True)

            with open(filename, mode="wb") as outfile:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:  # filter out keep-alive new chunks
                        outfile.write(chunk)
                        if progress:
                            pbar.update(len(chunk))

        return total_size

    except (HTTPError, URLError) as error:
        logger.error("Download failed. Query returned '%s'" % error)
        return
    except KeyboardInterrupt:
        logger.error("Unexpected interruption. Deleting unfinished file")
        os.remove(filename)
        return
