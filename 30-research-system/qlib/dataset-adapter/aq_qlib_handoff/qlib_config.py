"""Qlib-owned Alpha158 configuration for OHLCV-only ragged panels."""

from qlib.contrib.data.handler import Alpha158
from qlib.contrib.data.loader import Alpha158DL
from qlib.data.filter import ExpressionDFilter


def current_close_filter() -> ExpressionDFilter:
    """Return Qlib's native dynamic filter for current-session close availability."""
    return ExpressionDFilter(rule_expression="$close == $close", keep=False)


class RaggedAlpha158(Alpha158):
    """Use upstream Alpha158DL operators without requesting unavailable VWAP."""

    def get_feature_config(self):
        return Alpha158DL.get_feature_config({
            "kbar": {},
            "price": {"windows": [0], "feature": ["OPEN", "HIGH", "LOW"]},
            "rolling": {},
        })
