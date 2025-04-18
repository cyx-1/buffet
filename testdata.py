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


content: Content = {
    "metadata": {"time": ["2020", "2021", "2022", "2023", "2024"]},
    "data": [
        {"id": "BTC", "description": "Bitcoin", "timeseries": [305.1, 59.8, -64.2, 155.3, 121.0]},
        {"id": "IWF", "description": "US Growth", "timeseries": [38.2, 27.6, -29.1, 42.7, 33.1]},
        {"id": "GLD", "description": "Gold", "timeseries": [24.8, -3.6, -0.3, 15.1, 26.7]},
        {"id": "QQQ", "description": "US Nasdaq 100", "timeseries": [48.6, 27.2, -32.6, 54.8, 25.6]},
        {"id": "SPY", "description": "US Large Caps", "timeseries": [18.4, 28.7, -18.1, 26.2, 24.9]},
        {"id": "IWD", "description": "US Value", "timeseries": [2.8, 24.9, -7.5, 11.5, 14.2]},
        {"id": "MDY", "description": "US Mid Caps", "timeseries": [13.7, 24.6, -13.1, 8.9, 13.6]},
        {"id": "IWM", "description": "US Small Caps", "timeseries": [20.0, 14.8, -20.4, 16.8, 11.4]},
        {"id": "CWB", "description": "Convertible Bonds", "timeseries": [23.7, 8.2, -15.2, 12.4, 10.1]},
        {"id": "HYG", "description": "High Yield Bonds", "timeseries": [5.2, 4.3, -11.2, 9.1, 8.0]},
        {"id": "PFF", "description": "Preferred Stocks", "timeseries": [6.1, 6.4, -17.3, 5.8, 7.2]},
    ],
}
