class BaseStorageError(Exception):
    pass


class FileTooBigError(BaseStorageError):
    pass


class DataTypeError(BaseStorageError):
    pass
