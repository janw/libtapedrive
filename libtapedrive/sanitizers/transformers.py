from warnings import warn

from libtapedrive.sanitizers.filters import shownotes_image_cleaner


def markdownify(content):
    try:
        from markdown import markdown

        return markdown(content)
    except ImportError:
        warn("Cannot convert to markdown. Install libtapedrive's 'markdown' extra.")


def replace_shownotes_images(content, allowed_domains=False):
    if len(allowed_domains) == 1 and allowed_domains[0] == "*":
        return content
    else:
        return shownotes_image_cleaner.clean(content, allowed_domains=allowed_domains)
