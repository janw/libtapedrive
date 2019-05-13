import os
import logging
from io import BytesIO
from urllib.parse import urlparse, urlunparse
from urllib.error import HTTPError, URLError

import requests
import feedparser
import enlighten
from PIL import Image

from libtapedrive import __version__, __source__, defaults

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

    directory = os.path.dirname(filename)
    if directory and directory != ".":
        os.makedirs(directory, exist_ok=True)

    try:
        return _download_file(link, filename, chunk_size, progress)
    except (HTTPError, URLError):
        logger.error("Download failed.", exc_info=True)
    except KeyboardInterrupt:
        logger.error("Unexpected interruption. Deleting unfinished file")
        os.remove(filename)

    return 0


def _download_file(link, filename, chunk_size, progress):
    with session.get(link, stream=True, allow_redirects=True) as resp, open(
        filename, "wb"
    ) as out:
        resp.raise_for_status()
        if resp.url != link:
            logger.info(f"Original link: {link}")
            logger.info(f"Resolved link: {resp.url}")

        total_size = int(resp.headers.get("content-length", "0"))
        pbar = enlighten.Counter(
            total=total_size, desc=filename, enabled=progress, unit="B", min_delta=0.5
        )

        for chunk in resp.iter_content(chunk_size=chunk_size):
            out.write(chunk)
            pbar.update(len(chunk))
    return total_size


def download_cover(img_url, file):
    logger.info("Downloading cover")

    # Remove query params from URL (could be size-restricting, example: NPR's Invisibilia)
    # Of course that does not work on for example private feeds that use query params for
    # authentication (example: Do By Friday Aftershow delivered via Patreon using
    # token-time&token-hash)
    url = urlparse(img_url)
    logger.debug("Query params (removed on first try): %s", url.query)
    url = url._replace(query="")
    unqueried_img_url = urlunparse(url)
    response = requests.get(unqueried_img_url, headers=HEADERS, allow_redirects=True)
    if response.status_code >= 400:
        logger.info("Failed without query string, trying again.")
        # If that fails, try again with the original URL. After that fail softly
        response = requests.get(img_url, headers=HEADERS, allow_redirects=True)
        if response.status_code >= 400:
            return
        else:
            logger.info("Success.")

    name = url.path.split("/")[-1]
    name, ext = os.path.splitext(name)
    target_img_size = defaults.COVER_IMAGE_SIZE
    finput = BytesIO(response.content)
    img = Image.open(finput)
    logger.debug("Original image size is %dx%d." % img.size)

    # Return early and untouched if the image is smaller than desired
    if img.size[0] < target_img_size[0] or img.size[1] < target_img_size[1]:
        logger.info("Image size is smaller than desired. Ain't (re)touching that.")
        finput.seek(0)
        file.write(finput.read())
        file.seek(0)
        return name + ext

    # Resize the image (from https://djangosnippets.org/snippets/10597/)
    img.thumbnail(target_img_size)

    if ext.lower() != "png":

        # If the downloaded image has an alpha-channel: fill background
        if img.mode in ("RGBA", "LA"):
            logger.debug(
                "Non-PNG image with alpha-channel will be placed on white background"
            )
            fill_color = (255, 255, 255, 255)
            background = Image.new(img.mode[:-1], img.size, fill_color)
            background.paste(img, img.split()[-1])
            img = background

        if img.mode != "RGB":
            img = img.convert("RGB")

        # After modifications, save it to the output
        img.save(file, format="JPEG", quality=95)
        name += "jpg"
    else:
        img.save(file, format="PNG", transparency=False)
        name += "png"

    file.seek(0)
    return name
