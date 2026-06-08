export type InstrumentKind = "fund" | "cash";
export type InstrumentSleeve = "equity" | "fixed_income" | "gold" | "cash";

export type Instrument = {
  ticker: string;
  instrument: string;
  kind: InstrumentKind;
  sleeve: InstrumentSleeve;
  currency?: string;
  searchTerms?: string[];
};

export const instrumentUniverse: Instrument[] = [
  { ticker: "SPY", instrument: "SPDR S&P 500 ETF", kind: "fund", sleeve: "equity", searchTerms: ["s&p", "sp500", "us equity"] },
  { ticker: "VOO", instrument: "Vanguard S&P 500 ETF", kind: "fund", sleeve: "equity", searchTerms: ["s&p", "sp500", "us equity"] },
  { ticker: "VTI", instrument: "Vanguard Total Stock Market ETF", kind: "fund", sleeve: "equity", searchTerms: ["total market", "us equity"] },
  { ticker: "QQQ", instrument: "Invesco QQQ Trust", kind: "fund", sleeve: "equity", searchTerms: ["nasdaq", "technology"] },
  { ticker: "BND", instrument: "Vanguard Total Bond Market ETF", kind: "fund", sleeve: "fixed_income", searchTerms: ["bonds", "fixed income"] },
  { ticker: "TLT", instrument: "iShares 20+ Year Treasury Bond ETF", kind: "fund", sleeve: "fixed_income", searchTerms: ["treasury", "duration", "bonds"] },
  { ticker: "GLD", instrument: "SPDR Gold Shares", kind: "fund", sleeve: "gold", searchTerms: ["gold", "commodity"] },
  { ticker: "CASH_USD", instrument: "USD liquidity position", kind: "cash", sleeve: "cash", currency: "USD", searchTerms: ["cash", "usd", "liquidity"] },
  { ticker: "CASH_EUR", instrument: "EUR liquidity position", kind: "cash", sleeve: "cash", currency: "EUR", searchTerms: ["cash", "eur", "liquidity"] },
  { ticker: "CASH_GBP", instrument: "GBP liquidity position", kind: "cash", sleeve: "cash", currency: "GBP", searchTerms: ["cash", "gbp", "liquidity"] },
  { ticker: "CASH_CHF", instrument: "CHF liquidity position", kind: "cash", sleeve: "cash", currency: "CHF", searchTerms: ["cash", "chf", "liquidity"] },
  { ticker: "CASH_CAD", instrument: "CAD liquidity position", kind: "cash", sleeve: "cash", currency: "CAD", searchTerms: ["cash", "cad", "liquidity"] },
  { ticker: "CASH_AUD", instrument: "AUD liquidity position", kind: "cash", sleeve: "cash", currency: "AUD", searchTerms: ["cash", "aud", "liquidity"] }
];

export const instrumentByTicker = new Map(instrumentUniverse.map((item) => [item.ticker, item]));
