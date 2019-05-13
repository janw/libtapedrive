from xml import etree


def parse_opml_file(filename):
    with open(filename) as file:
        tree = etree.fromstringlist(file)
    return [
        node.get("xmlUrl")
        for node in tree.findall("*/outline/[@type='rss']")
        if node.get("xmlUrl") is not None
    ]
