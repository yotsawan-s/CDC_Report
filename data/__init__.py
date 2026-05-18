"""Data source dispatcher — `fetch_data(source, symbol) -> DataFrame[date, close]`."""

from .binance import fetch_binance
from .bitkub import fetch_bitkub
from .yfinance_src import fetch_yfinance

_FETCHERS = {
    "binance":  fetch_binance,
    "bitkub":   fetch_bitkub,
    "yfinance": fetch_yfinance,
}


def fetch_data(source, symbol):
    return _FETCHERS[source](symbol)
