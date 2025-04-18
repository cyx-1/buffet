from typing import TypedDict, List


class AssetData(TypedDict):
    id: str
    description: str
    timeseries: List[float]
    total: float


class ContentMetadata(TypedDict):
    name: str
    datatype: str
    time: List[str]


class Content(TypedDict):
    metadata: ContentMetadata
    data: List[AssetData]
