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







