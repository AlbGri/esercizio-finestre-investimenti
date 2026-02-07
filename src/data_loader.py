"""Download dati Yahoo Finance, intersezione date, validazioni."""

import logging
import sys
from datetime import date, timedelta

import pandas as pd
import yfinance as yf


def download_ticker(ticker: str, data_inizio: date, data_fine: date) -> pd.Series:
    """Scarica la serie Adj Close per un ticker da Yahoo Finance.

    Args:
        ticker: Simbolo Yahoo Finance.
        data_inizio: Data inizio periodo.
        data_fine: Data fine periodo.

    Returns:
        Serie pandas con Adj Close indicizzata per data (solo giorni di trading).
    """
    logging.info("Download dati per '%s' dal %s al %s...", ticker, data_inizio, data_fine)
    # yfinance esclude data_fine, aggiungiamo 1 giorno per includerla
    end_str = (data_fine + timedelta(days=1)).isoformat()
    try:
        data = yf.download(
            ticker,
            start=data_inizio.isoformat(),
            end=end_str,
            progress=False,
            auto_adjust=False,
        )
    except Exception as e:
        logging.error("Errore durante il download di '%s': %s", ticker, e)
        logging.error("Verificare ticker su https://finance.yahoo.com")
        sys.exit(1)

    if data.empty:
        logging.error("Ticker '%s' non trovato su Yahoo Finance o nessun dato nel periodo.", ticker)
        logging.error("Verificare ticker su https://finance.yahoo.com")
        sys.exit(1)

    # Estrai Adj Close - gestisci sia MultiIndex che colonne semplici
    if isinstance(data.columns, pd.MultiIndex):
        if "Adj Close" in data.columns.get_level_values(0):
            series = data["Adj Close"]
            if isinstance(series, pd.DataFrame):
                series = series.iloc[:, 0]
        else:
            logging.error("Colonna 'Adj Close' non trovata per ticker '%s'.", ticker)
            sys.exit(1)
    else:
        if "Adj Close" in data.columns:
            series = data["Adj Close"]
        else:
            logging.error("Colonna 'Adj Close' non trovata per ticker '%s'.", ticker)
            sys.exit(1)

    series = series.dropna()
    if series.empty:
        logging.error("Nessun dato valido (Adj Close) per ticker '%s' nel periodo.", ticker)
        sys.exit(1)

    logging.info("Download '%s' completato: %d giorni di trading.", ticker, len(series))
    return series


def get_ticker_currency(ticker: str) -> str | None:
    """Recupera la valuta di un ticker tramite yfinance.

    Args:
        ticker: Simbolo Yahoo Finance.

    Returns:
        Codice valuta (es. "USD", "EUR") oppure None se non disponibile.
    """
    try:
        info = yf.Ticker(ticker).fast_info
        return getattr(info, "currency", None)
    except Exception:
        return None


def load_data(
    ticker_1: str,
    ticker_2: str,
    data_inizio: date,
    data_fine: date,
    min_giorni_finestra: int,
    benchmark_ticker: str | None = None,
) -> dict[str, pd.Series]:
    """Scarica dati per tutti i ticker e calcola intersezione date.

    Args:
        ticker_1: Primo ticker.
        ticker_2: Secondo ticker.
        data_inizio: Data inizio periodo richiesto.
        data_fine: Data fine periodo richiesto.
        min_giorni_finestra: Minimo giorni finestra per verifica sufficienza dati.
        benchmark_ticker: Terzo ticker opzionale per benchmark.

    Returns:
        Dizionario {ticker_name: serie_adj_close} allineato su date comuni.
    """
    tickers = [ticker_1, ticker_2]
    if benchmark_ticker:
        tickers.append(benchmark_ticker)

    # Download
    raw: dict[str, pd.Series] = {}
    for t in tickers:
        raw[t] = download_ticker(t, data_inizio, data_fine)

    # Warning valute diverse
    currencies = {}
    for t in tickers:
        cur = get_ticker_currency(t)
        if cur:
            currencies[t] = cur
    unique_currencies = set(currencies.values())
    if len(unique_currencies) > 1:
        pairs = ", ".join(f"{t} in {c}" for t, c in currencies.items())
        logging.warning("%s - confronto potrebbe non essere significativo.", pairs)

    # Intersezione date
    common_index = raw[tickers[0]].index
    for t in tickers[1:]:
        common_index = common_index.intersection(raw[t].index)
    common_index = common_index.sort_values()

    n_common = len(common_index)
    if n_common < min_giorni_finestra:
        logging.error(
            "Periodo sovrapposizione insufficiente (%d giorni trading), servono almeno %d.",
            n_common, min_giorni_finestra,
        )
        sys.exit(1)

    # Warning se periodo ridotto
    requested_start = pd.Timestamp(data_inizio)
    requested_end = pd.Timestamp(data_fine)
    actual_start = common_index[0]
    actual_end = common_index[-1]
    if actual_start > requested_start or actual_end < requested_end:
        logging.warning(
            "Periodo ridotto a date comuni disponibili: %s / %s",
            actual_start.strftime("%Y-%m-%d"),
            actual_end.strftime("%Y-%m-%d"),
        )

    # Filtra su date comuni
    result: dict[str, pd.Series] = {}
    for t in tickers:
        result[t] = raw[t].loc[common_index]

    logging.info("Dati allineati: %d giorni di trading comuni.", n_common)
    return result
