"""User roles — the conceptual identities the domain reasons about.

There is no authentication and no persisted users in this PoC. The
enum exists so the domain (specifically the article lifecycle) can
express WHICH role is allowed to perform WHICH transition. In a real
system this enum would be paired with auth middleware that injects
the acting user's role into every request.
"""

from enum import StrEnum


class UserRole(StrEnum):
    USER = "user"
    SUPERVISOR = "supervisor"
