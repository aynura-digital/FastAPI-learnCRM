"""Reusable Pydantic field validators and annotated types."""

import re
from typing import Annotated

from pydantic import AfterValidator

_PHONE_RE = re.compile(r"^\+?\d{7,15}$")


def _validate_phone(value: str | None) -> str | None:
    if value is None:
        return value
    if not _PHONE_RE.match(value):
        raise ValueError("Phone must be 7–15 digits, optionally prefixed with +")
    return value


PhoneNumber = Annotated[str | None, AfterValidator(_validate_phone)]
