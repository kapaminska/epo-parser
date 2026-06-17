"""Single-file conversion result for orchestration and summary output."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from domain.model import ParseWarning

ConversionStatus = Literal["success", "failed"]


@dataclass(frozen=True, slots=True)
class ConversionResult:
    """Outcome of converting one XML source file to PDF."""

    source: Path
    pdf_path: Path | None
    status: ConversionStatus
    warnings: list[ParseWarning] = field(default_factory=list)
    error_message: str | None = None
    tracking_number: str | None = None
