"""Reddit JSON adapter for the inbound source contract."""

from collections.abc import AsyncIterator
from datetime import datetime, timezone
from typing import Any

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


class RedditArticleSource(ExternalArticleSource):
    kind: ExternalSource = ExternalSource.REDDIT
    user_url_template: str = "https://www.reddit.com/user/{account}.json"
    user_agent: str = (
        "rest-ddd-fastapi-blog/0.3 (https://github.com/parfeniukink)"
    )
    request_timeout_seconds: float = 10.0

    async def fetch(self, account: str) -> AsyncIterator[ArticleDraft]:
        url = self.user_url_template.format(account=account)

        try:
            async with httpx.AsyncClient(
                timeout=self.request_timeout_seconds,
                headers={"User-Agent": self.user_agent},
            ) as client:
                response = await client.get(url)
                response.raise_for_status()
                payload: Any = response.json()
        except httpx.HTTPError as exc:
            raise ExternalSourceUnreachable(f"reddit: {exc}") from exc
        except ValueError as exc:
            raise ExternalSourceFormatChanged(f"reddit: {exc}") from exc

        try:
            children: list[dict[str, Any]] = payload["data"]["children"]
        except (KeyError, TypeError) as exc:
            raise ExternalSourceFormatChanged(f"reddit: {exc}") from exc

        for child in children:
            if child.get("kind") != "t3":
                continue  # comments — skip; only submissions become articles
            yield self._to_draft(child.get("data", {}))

    def _to_draft(self, data: dict[str, Any]) -> ArticleDraft:
        title: str = (data.get("title") or "").strip()
        permalink: str = data.get("permalink") or ""
        post_id: str = (data.get("id") or "").strip()
        selftext: str = (data.get("selftext") or "").strip()
        created_utc: float = float(data.get("created_utc") or 0)

        if not title or not permalink or not post_id:
            raise ExternalSourceFormatChanged(
                "reddit: post missing title, permalink, or id"
            )

        return ArticleDraft(
            title=title,
            slug=self._slug_from_post(permalink=permalink, post_id=post_id),
            summary=(selftext[:500] or title),
            body=selftext or title,
            published_on=datetime.fromtimestamp(
                created_utc, tz=timezone.utc,
            ).date(),
        )

    def _slug_from_post(self, *, permalink: str, post_id: str) -> str:
        title_slug = permalink.rstrip("/").rsplit("/", 1)[-1]
        return f"{title_slug}-{post_id}"
