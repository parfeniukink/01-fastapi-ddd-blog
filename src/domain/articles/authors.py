"""Authors registry — who is allowed to publish.

A real system would have its own aggregate. For the PoC, an
in-process dict is enough to make `AuthorityCheck` feel like a
real domain rule.
"""

from enum import StrEnum


class AuthorRole(StrEnum):
    CONTRIBUTOR = "contributor"
    EDITOR = "editor"
    ADMIN = "admin"


AUTHORS: dict[str, AuthorRole] = {
    "jane.doe": AuthorRole.CONTRIBUTOR,
    "john.smith": AuthorRole.EDITOR,
    "blog.admin": AuthorRole.ADMIN,
}


def is_authorized_to_publish(author: str) -> bool:
    return author in AUTHORS
