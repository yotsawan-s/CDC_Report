"""
Central configuration — every value that's worth tweaking lives here.
แก้ที่นี่ที่เดียว ไม่ต้องเปิดไฟล์อื่น
"""

from pathlib import Path

# ==============================================================================
# Assets to track
# ==============================================================================
ASSETS = [
    ("BTC/USD",              "binance",  "BTCUSDT"),
    ("BTC/THB",              "bitkub",   "BTC_THB"),
    ("DOGE/THB",             "bitkub",   "DOGE_THB"),
    ("KUB/THB",              "bitkub",   "KUB_THB"),
    ("XAU/USD (Gold)",       "yfinance", "GC=F"),
    ("TSM",                  "yfinance", "TSM"),
    ("AMD",                  "yfinance", "AMD"),
    ("NVDA",                 "yfinance", "NVDA"),
    ("TSLA",                 "yfinance", "TSLA"),
    ("GOOGL",                "yfinance", "GOOGL"),
    ("MU (Micron)",          "yfinance", "MU"),
    ("SNDK (Sandisk)",       "yfinance", "SNDK"),
    ("WD (Western digital)", "yfinance", "WD"),
    ("CCET (Thailand)",      "yfinance", "CCET.BK"),
    ("QCOM (Qualcomm)",      "yfinance", "QCOM"),
]

# ==============================================================================
# CDC parameters
# ==============================================================================
FAST_EMA = 12
SLOW_EMA = 26
SMOOTH = 1
LOOKBACK_DAYS = 300
HISTORY_DAYS = 14

# ==============================================================================
# Output
# ==============================================================================
OUTPUT_DIR = Path("docs")

# ==============================================================================
# News (Phase 2+)
# ==============================================================================
NEWS_ENABLED = True
NEWS_COUNT = 5
NEWS_CACHE_DAYS = 14

NEWS_SOURCES = [
    {"name": "Reuters",         "rss": "https://feeds.reuters.com/reuters/businessNews"},
    {"name": "CNBC",            "rss": "https://www.cnbc.com/id/100003114/device/rss/rss.html"},
    {"name": "CoinDesk",        "rss": "https://www.coindesk.com/arc/outboundfeeds/rss/"},
    {"name": "MarketWatch",     "rss": "https://feeds.marketwatch.com/marketwatch/topstories/"},
    {"name": "The Conversation","rss": "https://theconversation.com/global/business/articles.atom"},
]

# Keywords used to score relevance vs ASSETS — แก้/เพิ่มได้
NEWS_ASSET_ALIASES = {
    "BTC":   ["bitcoin", "btc", "crypto", "cryptocurrency"],
    "DOGE":  ["dogecoin", "doge"],
    "KUB":   ["bitkub", "kub coin"],
    "XAU":   ["gold", "bullion", "precious metals"],
    "TSM":   ["tsmc", "taiwan semiconductor"],
    "AMD":   ["amd", "advanced micro devices"],
    "NVDA":  ["nvidia", "nvda"],
    "TSLA":  ["tesla", "tsla", "elon musk"],
    "GOOGL": ["alphabet", "google", "googl"],
    "MU":    ["micron"],
    "SNDK":  ["sandisk"],
    "WD":    ["western digital"],
    "CCET":  ["ccet", "thailand", "charoen pokphand"],
    "QCOM":  ["qualcomm", "qcom", "snapdragon"],
}

CLAUDE_MODEL = "claude-sonnet-4-6"
CLAUDE_MAX_TOKENS = 1500
CLAUDE_INLINE_RETRY_WAIT = 90  # max seconds to sleep inline before deferring
