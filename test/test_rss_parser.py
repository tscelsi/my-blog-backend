from xml.etree import ElementTree as ET

import pytest

from utils.rss_parser import parse_rss_feed


def test_parse_rss_feed_when_no_channel_tag(rss_content: str):
    root = ET.fromstring(rss_content)
    ch = root.find("channel")
    assert ch is not None
    root.remove(ch)
    with pytest.raises(ValueError, match="No channel tag found in RSS feed"):
        parse_rss_feed(root)


def test_parse_rss_feed(rss_content: str):
    root = ET.fromstring(rss_content)
    channel = parse_rss_feed(root)
    assert channel.title == "Democracy Now!"


def test_parse_rss_feed_items(rss_content: str):
    root = ET.fromstring(rss_content)
    channel = parse_rss_feed(root)
    first_item = channel.items[0]
    assert (
        first_item.title
        == "ICE Rounds Up 300 California Farmworkers, One Dies: Eyewitness and Oxnard Mayor Respond"  # noqa: E501
    )
    assert (
        first_item.link == "http://www.democracynow.org/2025/7/14/los_angeles"
    )
    assert first_item.description is not None
    assert first_item.pub_date is not None
