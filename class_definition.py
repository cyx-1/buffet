from typing import TypedDict, List


class AssetData(TypedDict):
    id: str
    description: str
    timeseries: List[float]


class ContentMetadata(TypedDict):
    time: List[str]


class Content(TypedDict):
    metadata: ContentMetadata
    data: List[AssetData]
