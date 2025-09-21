import asyncio
import logging
from datetime import datetime, timezone
from xml.etree import ElementTree as ET
from xml.etree.ElementTree import Element

import httpx
from pydantic import Field

from utils.network import get
from utils.rss_parser import RssChannel, RssItem, parse_rss_feed

from .base import BaseFragment, FragmentType

logger = logging.getLogger(__name__)

FEED_EXPIRY_SECONDS = 60 * 60  # 1 hour


class RssFeedError(Exception):
    """Base class for RSS feed-related errors."""

    pass


class RssFeedParseError(RssFeedError):
    """Exception raised when parsing the RSS feed fails."""

    pass


class ListRssFeedError(RssFeedError):
    """Exception raised when listing RSS feed stories fails."""

    pass


class RSSFeed(BaseFragment):
    """RSS Fragment class."""

    type: FragmentType = Field(default=FragmentType.RSS_FEED, frozen=True)
    urls: list[str]
    n_items: int = Field(
        default=10,
        description="Number of items to fetch from the aggregated RSS feeds.",
    )
    feed: list[RssItem] | None = Field(default=None)
    feed_last_generated: datetime | None = Field(default=None)

    def serialise(self) -> dict[str, str | FragmentType | list[str]]:
        """Serialise the RSS fragment to a dictionary."""
        return {
            "type": self.type.value,
            "id": str(self.id),
            "urls": self.urls,
        }

    async def load_aggregated_feed(self) -> None:
        if self.feed_last_generated is not None:
            delta = datetime.now(tz=timezone.utc) - self.feed_last_generated
            if delta.total_seconds() < FEED_EXPIRY_SECONDS:
                return  # don't regen if less than an hour old
        jobs = [self._load_feed_xml(url) for url in self.urls]
        xml_roots = await asyncio.gather(*jobs)
        items: list[RssItem] = []
        for root in xml_roots:
            try:
                channel = self._get_channel(root)
            except ValueError as e:
                raise RssFeedParseError(str(e)) from e
            items.extend(channel.items)
        self.feed = sorted(
            items, key=lambda item: item.pub_date, reverse=True
        )[: self.n_items]

    async def _load_feed_xml(self, url: str) -> Element:
        """Fetch the RSS feed and return the text."""
        try:
            response = await get(url)
        except httpx.HTTPStatusError as e:
            logger.exception(e)
            raise ListRssFeedError(
                f"Failed to fetch RSS feed from {self.urls}: {e.response.status_code}"  # noqa: E501
            ) from e
        return ET.fromstring(response.text)

    def _get_channel(self, root: Element, n_items: int = 10) -> RssChannel:
        channel = parse_rss_feed(root)
        if len(channel.items) > n_items:
            channel.items = channel.items[:n_items]
        return channel
