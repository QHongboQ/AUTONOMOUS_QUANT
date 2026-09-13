"""Qlib-owned Alpha158 configuration for OHLCV-only ragged panels."""

from qlib.contrib.data.handler import Alpha158
from qlib.contrib.data.loader import Alpha158DL


class RaggedAlpha158(Alpha158):
    """Use upstream Alpha158DL operators without requesting unavailable VWAP."""

    def get_feature_config(self):
        return Alpha158DL.get_feature_config({
            "kbar": {},
            "price": {"windows": [0], "feature": ["OPEN", "HIGH", "LOW"]},
            "rolling": {},
        })

    def get_label_config(self):
        # The current-session ratio makes a masked close produce a NaN label;
        # Qlib's native DropnaLabel then excludes that sample from learning.
        return ["($close/$close)*(Ref($close, -2)/Ref($close, -1) - 1)"], ["LABEL0"]
