class DataFormatError(ValueError):
    """Stored or serialized data does not match the model schema."""


class ValidationError(ValueError):
    """User input is invalid; field and reason can be used by CLI or GUI."""

    def __init__(self, field: str, reason: str) -> None:
        self.field = field
        self.reason = reason
        super().__init__(f"{field}: {reason}")
