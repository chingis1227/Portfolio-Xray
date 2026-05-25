from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from src.data_ibkr import IBKRConnectionConfig, fetch_historical_daily, fetch_latest_quotes


@dataclass
class FakeContract:
    symbol: str
    exchange: str
    currency: str


@dataclass
class FakeTicker:
    bid: float | None = None
    ask: float | None = None
    last: float | None = None
    close: float | None = None

    def marketPrice(self) -> float | None:
        return None


@dataclass
class FakeBar:
    date: date
    close: float


class FakeIB:
    def __init__(self) -> None:
        self.connected = False
        self.disconnected = False
        self.market_data_type = None
        self.cancelled = []

    def connect(self, host, port, clientId, timeout, readonly=True):
        self.connected = True
        self.connect_args = (host, port, clientId, timeout, readonly)

    def disconnect(self):
        self.disconnected = True

    def reqMarketDataType(self, market_data_type):
        self.market_data_type = market_data_type

    def qualifyContracts(self, contract):
        return [contract]

    def reqMktData(self, contract, genericTickList="", snapshot=False, regulatorySnapshot=False):
        return FakeTicker(bid=100.0, ask=101.0, last=99.0, close=98.0)

    def cancelMktData(self, contract):
        self.cancelled.append(contract.symbol)

    def sleep(self, seconds):
        self.sleep_seconds = seconds

    def reqHistoricalData(
        self,
        contract,
        endDateTime,
        durationStr,
        barSizeSetting,
        whatToShow,
        useRTH,
        formatDate,
    ):
        return [FakeBar(date(2026, 5, 20), 99.5), FakeBar(date(2026, 5, 21), 100.5)]


def test_fetch_latest_quotes_uses_readonly_connection_and_mid_price():
    fake_ib = FakeIB()

    quotes = fetch_latest_quotes(
        ["voo"],
        config=IBKRConnectionConfig(client_id=77),
        market_data_type=3,
        snapshot_seconds=0,
        ib_factory=lambda: fake_ib,
        stock_factory=FakeContract,
    )

    assert fake_ib.connect_args == ("127.0.0.1", 7497, 77, 8.0, True)
    assert fake_ib.market_data_type == 3
    assert fake_ib.cancelled == ["VOO"]
    assert fake_ib.disconnected is True
    assert quotes[0].symbol == "VOO"
    assert quotes[0].price == 100.5
    assert quotes[0].price_source == "mid"
    assert quotes[0].delayed is True


def test_fetch_historical_daily_returns_close_frame():
    fake_ib = FakeIB()

    df = fetch_historical_daily(
        "spy",
        config=IBKRConnectionConfig(client_id=78),
        duration="2 D",
        ib_factory=lambda: fake_ib,
        stock_factory=FakeContract,
    )

    assert list(df.columns) == ["Close"]
    assert df.index.name == "Date"
    assert list(df["Close"]) == [99.5, 100.5]
    assert df.index[-1].strftime("%Y-%m-%d") == "2026-05-21"
    assert fake_ib.disconnected is True
