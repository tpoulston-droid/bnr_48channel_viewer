"""
bnr_sdk/models.py
Data models representing optical snapshot and channel telemetry.
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class OpticalChannel:
    channel_index: int
    raw_ad_count: int
    board_group: str = "RED"
    track_type: str = "TRANSMISSIVE"


@dataclass
class OpticalSnapshot:
    channels: List[OpticalChannel] = field(default_factory=list)
