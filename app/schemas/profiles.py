"""Pydantic schemas for stock profiles API."""

from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, field_validator

OwnershipType = Literal["GOVT_CONTROLLED", "JOINT_VENTURE", "PRIVATE", "PSU"]


class StockProfileResponse(BaseModel):
    """Full stock profile as returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    stock_name: str
    associated_brands: Optional[List[str]]
    business_group: Optional[str]
    information: Optional[str]
    risk_level: Optional[str]
    location: Optional[List[str]]
    ownership_type: Optional[str]
    keynotes: Optional[List[str]]
    clients: Optional[List[str]]


class StockProfilePatchRequest(BaseModel):
    """Partial update payload — all fields optional."""

    associated_brands: Optional[List[str]] = None
    business_group: Optional[str] = None
    information: Optional[str] = None
    risk_level: Optional[str] = None
    location: Optional[List[str]] = None
    ownership_type: Optional[OwnershipType] = None
    keynotes: Optional[List[str]] = None
    clients: Optional[List[str]] = None

    @field_validator("business_group", "information", "risk_level", mode="before")
    @classmethod
    def strip_strings(cls, v: Optional[str]) -> Optional[str]:
        return v.strip() if isinstance(v, str) else v

    @field_validator("associated_brands", "location", "keynotes", "clients", mode="before")
    @classmethod
    def strip_array_items(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v is None:
            return v
        return [item.strip() for item in v if isinstance(item, str)]
