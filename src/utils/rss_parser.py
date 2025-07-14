from datetime import datetime
from xml.etree.ElementTree import Element
from email.utils import parsedate_to_datetime
from pydantic import BaseModel


class RssItem(BaseModel):
    title: str
    link: str
    description: str | None = None
    pub_date: datetime
    source: str


class RssChannel(BaseModel):
    title: str
    link: str
    items: list[RssItem] = []


def parse_rss_feed(root: Element) -> RssChannel:
    channel = root.find("channel")
    if channel is None:
        raise ValueError("No channel tag found in RSS feed")
    parsed_channel = RssChannel(
        title=channel.findtext("title", ""),
        link=channel.findtext("link", ""),
    )
    domain = parsed_channel.link.split("//")[-1].split("/")[0]
    for item in channel.findall("item"):
        title = item.findtext("title", "")
        pubDate = item.findtext("pubDate")
        if not pubDate:
            continue
        parsed_item = RssItem(
            title=title,
            link=item.findtext("link", ""),
            description=item.findtext("description"),
            pub_date=parsedate_to_datetime(pubDate),
            source=item.findtext("source", domain),
        )
        parsed_channel.items.append(parsed_item)
    return parsed_channel
