from .base import BaseParser, create_http_session
from .binance import BinanceParser
from .bitget import BitgetParser
from .bybit import BybitParser
from .gate import GateParser
from .mexc import MexcParser
from .okx import OkxParser

PARSERS: list[type[BaseParser]] = [
    BinanceParser,
    OkxParser,
    BybitParser,
    BitgetParser,
    GateParser,
    MexcParser,
]

__all__ = ["PARSERS", "BaseParser", "create_http_session"]
