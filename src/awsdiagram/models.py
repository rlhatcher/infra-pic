"""Pydantic v2 models for the YAML DSL schema."""

from __future__ import annotations

import re

from pydantic import BaseModel, field_validator, model_validator


_TYPE_PATTERN = re.compile(r"^[a-z][a-z0-9]*\.[A-Z][A-Za-z0-9]*$")


class ServiceDef(BaseModel):
    """A single AWS service node."""

    type: str
    label: str

    @field_validator("type")
    @classmethod
    def validate_type_format(cls, v: str) -> str:
        if not _TYPE_PATTERN.match(v):
            raise ValueError(
                f"Invalid type format '{v}'. "
                "Expected 'category.ClassName' (e.g. 'compute.EC2')."
            )
        return v


class GroupDef(BaseModel):
    """A cluster group that can contain services and nested child groups."""

    name: str
    services: list[str] = []
    children: list[GroupDef] = []


class ConnectionDef(BaseModel):
    """A connection between services."""

    from_: str
    to: str | list[str]
    label: str | None = None

    @model_validator(mode="before")
    @classmethod
    def remap_from_key(cls, data: dict) -> dict:
        if isinstance(data, dict) and "from" in data:
            data["from_"] = data.pop("from")
        return data


class DiagramDef(BaseModel):
    """Top-level diagram definition."""

    name: str
    services: dict[str, ServiceDef]
    groups: list[GroupDef] = []
    connections: list[ConnectionDef] = []

    @field_validator("services")
    @classmethod
    def services_not_empty(cls, v: dict) -> dict:
        if not v:
            raise ValueError("At least one service must be defined")
        return v


class RootModel(BaseModel):
    """Root wrapper — expects a top-level 'diagram' key."""

    diagram: DiagramDef
