"""
bnr_sdk/compensator.py
Custom optical offset compensation and vignette normalization engine.
"""

from typing import List, Tuple, Optional


class CustomOffsetCompensator:
    EDGE_CHANNELS = {0, 11, 16, 27, 32, 43, 48, 59}

    def __init__(self, target_count: int = 200):
        self.target = target_count
        self.dark_offsets = [0] * 64
        self.scale_factors = [1.0] * 64
        self.is_calibrated = False

    def capture_dark_reference(self, raw_unlit_counts: List[int]):
        self.dark_offsets = [max(0, int(val)) for val in raw_unlit_counts[:64]]
        if len(self.dark_offsets) < 64:
            self.dark_offsets.extend([0] * (64 - len(self.dark_offsets)))

    def calibrate_with_coupon(self, raw_sweep_counts: List[int]) -> bool:
        if len(raw_sweep_counts) < 60:
            return False

        for ch in range(64):
            raw = raw_sweep_counts[ch] if ch < len(raw_sweep_counts) else 0
            dark = self.dark_offsets[ch]
            net_signal = max(1, raw - dark)

            if net_signal < 10 and ch not in self.EDGE_CHANNELS:
                self.scale_factors[ch] = 0.0
            else:
                factor = float(self.target) / float(net_signal)
                self.scale_factors[ch] = max(0.4, min(4.0, factor))

        self.is_calibrated = True
        return True

    def apply_compensation(self, raw_counts: List[int]) -> List[int]:
        if not self.is_calibrated:
            return raw_counts

        compensated = []
        for ch in range(len(raw_counts)):
            if ch >= 64:
                break
            raw = raw_counts[ch]
            dark = self.dark_offsets[ch]
            factor = self.scale_factors[ch]

            if factor == 0.0:
                compensated.append(0)
            else:
                val = int((raw - dark) * factor)
                compensated.append(max(0, min(255, val)))

        return compensated

    @staticmethod
    def parse_size_check(bnr_instance) -> Tuple[Optional[float], Optional[float], str]:
        try:
            from Mei.Bnr import SizeCheckAlgoDetailedResult
            
            # Robust reflection call handling overloads (parameterless vs index 0/1)
            rec = None
            if hasattr(bnr_instance, "GetDetailedRecognitionResult"):
                try:
                    rec = bnr_instance.GetDetailedRecognitionResult()
                except Exception:
                    try:
                        rec = bnr_instance.GetDetailedRecognitionResult(0)
                    except Exception:
                        try:
                            rec = bnr_instance.GetDetailedRecognitionResult(1)
                        except Exception:
                            pass

            if rec and hasattr(rec, "AlgorithmDetailedResult"):
                for algo in rec.AlgorithmDetailedResult:
                    if isinstance(algo, SizeCheckAlgoDetailedResult):
                        w_mm = algo.BillWidthInMom / 10.0
                        l_mm = algo.BillLengthInMom / 10.0
                        status = str(algo.Result)
                        return (w_mm, l_mm, status)
        except Exception as ex:
            print(f"[SIZE CHECK EXCEPTION] {ex}")

        return (None, None, "Unavailable")
