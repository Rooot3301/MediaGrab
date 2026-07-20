class MediaGrabError(Exception):
    """Base class for errors safe to present to the user."""


class InvalidUrlError(MediaGrabError): pass
class UnsupportedUrlError(MediaGrabError): pass
class BinaryNotFoundError(MediaGrabError): pass
class BinaryExecutionError(MediaGrabError): pass
class MetadataExtractionError(MediaGrabError): pass
class DownloadError(MediaGrabError): pass
class InvalidDestinationError(MediaGrabError): pass
class InsufficientDiskSpaceError(MediaGrabError): pass
class SettingsError(MediaGrabError): pass

