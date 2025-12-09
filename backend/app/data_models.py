"""Typed schemas representing the raw and normalized customer records."""
from __future__ import annotations

from datetime import datetime
from typing import Optional, Literal

from pydantic import BaseModel, Field, validator, model_validator

from .config import settings

MarketingContact = Literal["cellular", "telephone", "unknown"]
BinaryResponse = Literal["yes", "no"]
Outcome = Literal["failure", "success", "other", "unknown"]
LoanOption = Literal["yes", "no", "unknown"]
EducationLevel = Literal["primary", "secondary", "tertiary", "unknown"]
MaritalStatus = Literal["married", "single", "divorced"]
JobCategory = Literal[
    "admin.", "blue-collar", "entrepreneur", "housemaid", "management",
    "retired", "self-employed", "services", "student", "technician",
    "unemployed", "unknown"
]
Month = Literal[
    "jan", "feb", "mar", "apr", "may", "jun", "jul",
    "aug", "sep", "oct", "nov", "dec"
]


class BankMarketingRawRecord(BaseModel):
    """Schema describing the incoming raw CSV record."""

    age: int = Field(ge=18, le=100)
    job: JobCategory
    marital: MaritalStatus
    education: EducationLevel
    default: BinaryResponse
    balance: float
    housing: BinaryResponse
    loan: BinaryResponse
    contact: MarketingContact
    day: int = Field(ge=1, le=31)
    month: Month
    duration: int = Field(ge=0)
    campaign: int = Field(ge=1)
    pdays: int = Field(ge=-1)
    previous: int = Field(ge=0)
    poutcome: Outcome
    y: BinaryResponse

    @validator("pdays", pre=True)
    def convert_pdays_to_int(cls, value):
        """Convert pdays to int, handling float values from CSV parsing."""
        if value is None:
            return -1
        if isinstance(value, float):
            # Handle NaN
            import math
            if math.isnan(value):
                return -1
            return int(round(value))
        return int(value)

    @validator("previous", pre=True)
    def convert_previous_to_int(cls, value):
        """Convert previous to int, handling float values from CSV parsing."""
        if value is None:
            return 0
        if isinstance(value, float):
            # Handle NaN
            import math
            if math.isnan(value):
                return 0
            return int(round(value))
        return int(value)

    @validator("campaign", pre=True)
    def convert_campaign_to_int(cls, value):
        """Convert campaign to int, handling float values from CSV parsing."""
        if value is None:
            return 1
        if isinstance(value, float):
            # Handle NaN
            import math
            if math.isnan(value):
                return 1
            return int(round(value))
        return int(value)

    @validator("age", pre=True)
    def convert_age_to_int(cls, value):
        """Convert age to int, handling float values from CSV parsing."""
        if value is None:
            return 18
        if isinstance(value, float):
            # Handle NaN
            import math
            if math.isnan(value):
                return 18
            return int(round(value))
        return int(value)

    @validator("day", pre=True)
    def convert_day_to_int(cls, value):
        """Convert day to int, handling float values from CSV parsing."""
        if value is None:
            return 1
        if isinstance(value, float):
            # Handle NaN
            import math
            if math.isnan(value):
                return 1
            return int(round(value))
        return int(value)

    @validator("duration", pre=True)
    def convert_duration_to_int(cls, value):
        """Convert duration to int, handling float values from CSV parsing."""
        if value is None:
            return 0
        if isinstance(value, float):
            # Handle NaN
            import math
            if math.isnan(value):
                return 0
            return int(round(value))
        return int(value)

    @validator("balance")
    def balance_reasonable(cls, value: float) -> float:
        if value < -10000 or value > 1000000:
            raise ValueError("Balance is outside plausible operational range")
        return value

    @validator("duration")
    def duration_limit(cls, value: int) -> int:
        if value > 3600:
            raise ValueError("Call duration exceeds one hour limit")
        return value

    @model_validator(mode="after")
    def check_campaign_previous(cls, values: "BankMarketingRawRecord") -> "BankMarketingRawRecord":
        if values.previous == 0 and values.pdays not in (-1, 999):
            raise ValueError("pdays must be -1 or 999 when previous is zero")
        return values


class BankMarketingRecord(BankMarketingRawRecord):
    """Schema once normalized and enriched during ingestion."""

    dataset_id: str
    ingestion_timestamp: datetime
    normalized_contact: MarketingContact
    is_contact_recent: bool
    balance_to_age_ratio: Optional[float]
    age_balance_interaction: float
    contact_frequency_score: float
    target: BinaryResponse = Field(alias=settings.TARGET_COLUMN)

    model_config = {
        "populate_by_name": True,
        "from_attributes": True,
    }









