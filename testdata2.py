from typing import TypedDict, List


class AssetData(TypedDict):
    id: str
    description: str
    timeseries: List[float]


class ContentMetadata(TypedDict):
    years: List[str]


class Content(TypedDict):
    metadata: ContentMetadata
    data: List[AssetData]


content: Content = {
    "metadata": {
        "years": [
            "2024"
        ]
    },
    "data": [
        {
            "id": "AAPL",
            "description": "Apple Inc.",
            "timeseries": [
                167.21
            ]
        }
    ]
}
