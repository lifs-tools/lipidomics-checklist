# generated by datamodel-codegen:
#   filename:  schema.json
#   timestamp: 2024-08-27T15:39:30+00:00

from __future__ import annotations

from typing import List, Optional, Union

from pydantic import BaseModel, Field


class ChoiceItem(BaseModel):
    name: str
    label: str
    value: int
    description: Optional[str] = None


class ContentItem(BaseModel):
    label: Optional[str] = None
    name: str
    type: str
    required: Optional[int] = None
    value: Optional[Union[int, str]] = None
    description: Optional[str] = None
    validate_: Optional[str] = Field(None, alias='validate')
    choice: Optional[List[ChoiceItem]] = None
    view: Optional[str] = None
    condition: Optional[str] = None
    min: Optional[float] = None
    code: Optional[str] = None


class Page(BaseModel):
    title: str
    content: List[ContentItem]


class CheckList(BaseModel):
    pages: List[Page]
    current_page: int
    max_page: int
    creation_date: str
    version: str


class LipidClassChoiceItem(BaseModel):
    name: str
    label: str
    group: Optional[str] = None
    description: Optional[str] = None
    value: int


class LipidClassContentItem(BaseModel):
    label: Optional[str] = None
    name: str
    type: str
    required: Optional[int] = None
    choice: Optional[List[LipidClassChoiceItem]] = None
    description: Optional[str] = None
    value: Optional[str] = None
    condition: Optional[str] = None
    columns: Optional[str] = None


class LipidClassPage(BaseModel):
    title: str
    content: List[LipidClassContentItem]


class LipidClass(BaseModel):
    pages: List[LipidClassPage]
    current_page: int
    max_page: int
    creation_date: str
    version: str


class SampleChoiceItem(BaseModel):
    name: str
    label: str
    value: int
    condition: Optional[str] = None


class SampleContentItem(BaseModel):
    label: str
    name: str
    type: str
    required: int
    value: Optional[Union[int, str]] = None
    description: str
    choice: Optional[List[SampleChoiceItem]] = None
    condition: Optional[str] = None
    min: Optional[float] = None


class SamplePage(BaseModel):
    title: str
    content: List[SampleContentItem]


class Sample(BaseModel):
    pages: List[SamplePage]
    current_page: int
    max_page: int
    creation_date: str
    version: str


class LipidomicsChecklistJsonSchema10(BaseModel):
    CheckList: Optional[CheckList] = Field(
        None, description='The main checklist object'
    )
    LipidClass: Optional[LipidClass] = None
    Sample: Optional[Sample] = None
