from enum import Enum


class PermissionsEvents(str, Enum):
    EDITORS_ADDED = "editors_added"
    EDITORS_REMOVED = "editors_removed"
    READERS_ADDED = "readers_added"
    READERS_REMOVED = "readers_removed"
    MADE_PUBLIC = "made_public"
    MADE_PRIVATE = "made_private"
    MEMORY_REMOVED = "memory_removed"
    MEMORY_CREATED = "memory_created"
