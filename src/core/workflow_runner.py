"""
src.core.workflow_runner
Orchestrates sweep data parsing into 48 optical counts and 16 reference voltages.
"""
from typing import Dict, Any, List
from bnr_sdk.models import HibouHeadSnapshot, HibouBoard

class WorkflowRunner:
    # Hardware ADC counts-to-voltage conversion calibration factors
    @staticmethod
    def _convert_rail_counts_to_volts(raw_counts: List[int]) -> Dict[str, float]:
        """
        Channels 12-15 correspond to:
          - Ch 12: +12V (divided down to ~2.5V on 3.3V ADC)
          - Ch 13: -12V (inverted/offset scaled via R229 network)
          - Ch 14: +3.3V (ratiometric/divided logic rail)
          - Ch 15: GND (ground bounce offset)
        """
        c_12v, c_m12v, c_3v3, c_gnd = raw_counts[12:16]

        v_12v = round((c_12v / 1023.0) * 3.3 * 4.95, 2)
        v_m12v = round(-((1023.0 - c_m12v) / 1023.0) * 3.3 * 4.85, 2)
        v_3v3 = round((c_3v3 / 1023.0) * 3.3 * 1.33, 2)
        v_gnd = round((c_gnd / 1023.0) * 3.3 * 0.05, 3)

        return {
            "+12V": v_12v,
            "-12V": v_m12v,
            "+3.3V": v_3v3,
            "GND": v_gnd
        }

    @classmethod
    def parse_snapshot(cls, snapshot: HibouHeadSnapshot) -> Dict[str, Dict[str, Any]]:
        """
        Extracts both the 12 optical counts and 4 rail voltages for each of the 4 boards.
        """
        boards = {
            "red": snapshot.get_board_channels(HibouBoard.RED_UPPER_OPTICAL),
            "green": snapshot.get_board_channels(HibouBoard.GREEN_LOWER_OPTICAL),
            "blue": snapshot.get_board_channels(HibouBoard.BLUE_UPPER_EXIT),
            "black": snapshot.get_board_channels(HibouBoard.BLACK_LOWER_EXIT),
        }

        parsed = {}
        for name, ch_objs in boards.items():
            raw_counts = [ch.raw_ad_count for ch in ch_objs]
            parsed[name] = {
                "optical": raw_counts[:12],
                "rails": cls._convert_rail_counts_to_volts(raw_counts)
            }

        return parsed