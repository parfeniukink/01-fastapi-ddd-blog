"""Medium RSS adapter for the inbound source contract."""

from collections.abc import AsyncIterator
from datetime import date
from email.utils import parsedate_to_datetime
from xml.etree import ElementTree as ET

import httpx

from src.domain.articles import (
    ArticleDraft,
    ExternalArticleSource,
    ExternalSource,
)
from src.domain.errors import (
    ExternalSourceFormatChanged,
    ExternalSourceUnreachable,
)


class MediumArticleSource(ExternalArticleSource):
    kind: ExternalSource = ExternalSource.MEDIUM
    feed_url_template: str = "https://medium.com/feed/@{account}"
    request_timeout_seconds: float = 10.0

    async def fetch(self, account: str) -> AsyncIterator[ArticleDraft]:
        url = self.feed_url_template.format(account=account)

        try:
            async with httpx.AsyncClient(
                timeout=self.request_timeout_seconds,
            ) as client:
                response = await client.get(url)
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise ExternalSourceUnreachable(f"medium: {exc}") from exc

        try:
            root = ET.fromstring(response.text)
        except ET.ParseError as exc:
            raise ExternalSourceFormatChanged(f"medium: {exc}") from exc

        channel = root.find("channel")
        if channel is None:
            raise ExternalSourceFormatChanged("medium: feed missing <channel>")

        for item in channel.findall("item"):
            yield self._to_draft(item)

    def _to_draft(self, item: ET.Element) -> ArticleDraft:
        title: str = (item.findtext("title") or "").strip()
        link: str = (item.findtext("link") or "").strip()
        description: str = (item.findtext("description") or "").strip()
        pub_date_text: str | None = item.findtext("pubDate")

        if not title or not link:
            raise ExternalSourceFormatChanged(
                "medium: <item> missing title or link"
            )

        return ArticleDraft(
            title=title,
            slug=self._slug_from_url(link),
            summary=(description[:500] or title),
            body=description or title,
            published_on=self._parse_date(pub_date_text),
        )

    def _slug_from_url(self, url: str) -> str:
        return url.rstrip("/").rsplit("/", 1)[-1].split("?")[0]

    def _parse_date(self, text: str | None) -> date:
        if not text:
            return date.today()
        try:
            return parsedate_to_datetime(text).date()
        except (TypeError, ValueError):
            return date.today()
