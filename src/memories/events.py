from enum import Enum


class StorageEvents(str, Enum):
    FILESYS_SAVE_ERROR = "filesys_save_error"
    FILESYS_SAVE_SUCCESS = "filesys_save_success"
    FILESYS_DELETE_ERROR = "filesys_delete_error"
    FILESYS_DELETE_SUCCESS = "filesys_delete_success"
