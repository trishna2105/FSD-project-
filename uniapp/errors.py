class DataFormatError(ValueError):
    """Stored or serialized data does not match the model schema."""


class ValidationError(ValueError):
    """User input is invalid; field and reason can be used by CLI or GUI."""

    def __init__(self, field: str, reason: str) -> None:
        self.field = field
        self.reason = reason
        super().__init__(f"{field}: {reason}")


class StorageError(OSError):
    """The student data file could not be created, read or written."""


class DuplicateStudentError(ValueError):
    """A student ID or normalized email is already registered."""


class StudentNotFoundError(LookupError):
    """An update targeted a student ID that is not stored."""


class AuthenticationError(ValueError):
    """The supplied credentials do not match a registered student."""


class IDGenerationError(RuntimeError):
    """No unused student ID was found within the retry limit."""
