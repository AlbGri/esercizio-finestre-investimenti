"""Logica rolling windows, calcolo rendimenti, statistiche aggregate."""

import logging
from dataclasses import dataclass, field
from math import sqrt

import numpy as np
import pandas as pd


@dataclass
class WindowResult:
    """Risultato di una singola finestra temporale."""
    data_inizio: str
    data_fine: str
    rendimento_netto: float


@dataclass
class WindowSizeStats:
    """Statistiche aggregate per una dimensione di finestra."""
    dimensione_finestra: int
    totale_finestre: int
    finestre_positive: int
    finestre_negative: int
    pct_positive: float
    rendimento_medio: float
    rendimento_mediano: float
    deviazione_std: float
    sharpe_ratio: float
    best_rendimento: float
    best_data_inizio: str
    best_data_fine: str
    worst_rendimento: float
    worst_data_inizio: str
    worst_data_fine: str


@dataclass
class TickerAnalysis:
    """Risultato completo dell'analisi per un ticker."""
    ticker: str
    stats_per_finestra: list[WindowSizeStats] = field(default_factory=list)
    finestra_ottimale: WindowSizeStats | None = None


def calcola_rendimento_finestra(
    prezzo_iniziale: float,
    prezzo_finale: float,
    capitale_iniziale: float,
    commissione_fissa: float,
    commissione_percentuale: float,
    tassa_capital_gain: float,
) -> float:
    """Calcola il rendimento netto di una singola finestra.

    Args:
        prezzo_iniziale: Adj Close primo giorno finestra.
        prezzo_finale: Adj Close ultimo giorno finestra.
        capitale_iniziale: Capitale investito.
        commissione_fissa: Commissione fissa in euro.
        commissione_percentuale: Commissione percentuale (es. 0.19 = 0.19%).
        tassa_capital_gain: Aliquota tasse su profitti in % (es. 26.0).

    Returns:
        Rendimento netto in percentuale.
    """
    # Commissione acquisto
    costo_acquisto = commissione_fissa + (capitale_iniziale * commissione_percentuale / 100)
    capitale_netto = capitale_iniziale - costo_acquisto

    # Quote e valore finale
    quote = capitale_netto / prezzo_iniziale
    valore_finale = quote * prezzo_finale

    # Rendimento lordo
    rendimento_lordo = ((valore_finale - capitale_iniziale) / capitale_iniziale) * 100

    # Rendimento netto (tasse solo su profitti)
    if rendimento_lordo > 0:
        profitto_lordo = valore_finale - capitale_iniziale
        tasse = profitto_lordo * (tassa_capital_gain / 100)
        valore_finale_netto = valore_finale - tasse
        rendimento_netto = ((valore_finale_netto - capitale_iniziale) / capitale_iniziale) * 100
    else:
        rendimento_netto = rendimento_lordo

    return rendimento_netto


def genera_finestre(
    prices: pd.Series,
    dimensione: int,
    sovrapposte: bool,
) -> list[tuple[int, int]]:
    """Genera indici inizio/fine per le finestre temporali.

    Args:
        prices: Serie prezzi (indice = date trading).
        dimensione: Numero giorni trading per finestra.
        sovrapposte: True per rolling (step=1), False per blocchi consecutivi.

    Returns:
        Lista di tuple (indice_inizio, indice_fine) dove fine e' incluso.
    """
    n = len(prices)
    windows = []

    if sovrapposte:
        for i in range(n - dimensione + 1):
            windows.append((i, i + dimensione - 1))
    else:
        i = 0
        while i + dimensione - 1 < n:
            windows.append((i, i + dimensione - 1))
            i += dimensione

    return windows


def calcola_statistiche_finestra(
    results: list[WindowResult],
    dimensione: int,
    soglia_positiva: float,
    risk_free_rate: float,
) -> WindowSizeStats:
    """Calcola statistiche aggregate per una dimensione di finestra.

    Args:
        results: Lista risultati singole finestre.
        dimensione: Dimensione finestra in giorni trading.
        soglia_positiva: Soglia minima per considerare finestra positiva.
        risk_free_rate: Tasso risk-free annualizzato in %.

    Returns:
        Statistiche aggregate.
    """
    rendimenti = np.array([r.rendimento_netto for r in results])
    totale = len(rendimenti)

    positive = int(np.sum(rendimenti > soglia_positiva))
    negative = totale - positive
    pct_positive = (positive / totale) * 100 if totale > 0 else 0.0

    rend_medio = float(np.mean(rendimenti))
    rend_mediano = float(np.median(rendimenti))
    std_dev = float(np.std(rendimenti, ddof=1)) if totale > 1 else 0.0

    # Sharpe ratio annualizzato
    periodi_anno = 252 / dimensione
    rend_medio_annuo = rend_medio * periodi_anno
    excess_return = rend_medio_annuo - risk_free_rate
    std_annua = std_dev * sqrt(periodi_anno) if periodi_anno > 0 else 0.0
    sharpe = excess_return / std_annua if std_annua > 0 else 0.0

    # Best / worst
    best_idx = int(np.argmax(rendimenti))
    worst_idx = int(np.argmin(rendimenti))

    return WindowSizeStats(
        dimensione_finestra=dimensione,
        totale_finestre=totale,
        finestre_positive=positive,
        finestre_negative=negative,
        pct_positive=round(pct_positive, 2),
        rendimento_medio=round(rend_medio, 4),
        rendimento_mediano=round(rend_mediano, 4),
        deviazione_std=round(std_dev, 4),
        sharpe_ratio=round(sharpe, 4),
        best_rendimento=round(float(rendimenti[best_idx]), 4),
        best_data_inizio=results[best_idx].data_inizio,
        best_data_fine=results[best_idx].data_fine,
        worst_rendimento=round(float(rendimenti[worst_idx]), 4),
        worst_data_inizio=results[worst_idx].data_inizio,
        worst_data_fine=results[worst_idx].data_fine,
    )


def analizza_ticker(
    ticker: str,
    prices: pd.Series,
    capitale_iniziale: float,
    min_giorni: int,
    max_giorni: int,
    step_giorni: int,
    sovrapposte: bool,
    commissione_fissa: float,
    commissione_percentuale: float,
    tassa_capital_gain: float,
    soglia_positiva: float,
    risk_free_rate: float,
) -> TickerAnalysis:
    """Esegue l'analisi completa per un ticker su tutte le dimensioni finestra.

    Args:
        ticker: Nome ticker.
        prices: Serie Adj Close.
        capitale_iniziale: Capitale investito per finestra.
        min_giorni: Dimensione minima finestra.
        max_giorni: Dimensione massima finestra.
        step_giorni: Incremento dimensione finestra.
        sovrapposte: True per rolling windows.
        commissione_fissa: Commissione fissa per acquisto.
        commissione_percentuale: Commissione percentuale per acquisto.
        tassa_capital_gain: Aliquota tasse su profitti.
        soglia_positiva: Soglia rendimento per finestra positiva.
        risk_free_rate: Tasso risk-free annualizzato.

    Returns:
        Analisi completa con statistiche per ogni dimensione finestra.
    """
    analysis = TickerAnalysis(ticker=ticker)
    dates = prices.index
    values = prices.values

    dimensioni = list(range(min_giorni, max_giorni + 1, step_giorni))
    logging.info("Analisi '%s': %d dimensioni finestra da %d a %d (step %d).",
                 ticker, len(dimensioni), min_giorni, dimensioni[-1], step_giorni)

    for dim in dimensioni:
        windows = genera_finestre(prices, dim, sovrapposte)

        if not windows:
            logging.warning("Nessuna finestra generabile per '%s' con dimensione %d.", ticker, dim)
            continue

        results: list[WindowResult] = []
        for start_idx, end_idx in windows:
            p_inizio = float(values[start_idx])
            p_fine = float(values[end_idx])

            rend = calcola_rendimento_finestra(
                prezzo_iniziale=p_inizio,
                prezzo_finale=p_fine,
                capitale_iniziale=capitale_iniziale,
                commissione_fissa=commissione_fissa,
                commissione_percentuale=commissione_percentuale,
                tassa_capital_gain=tassa_capital_gain,
            )

            results.append(WindowResult(
                data_inizio=str(dates[start_idx].date()),
                data_fine=str(dates[end_idx].date()),
                rendimento_netto=rend,
            ))

        stats = calcola_statistiche_finestra(results, dim, soglia_positiva, risk_free_rate)
        analysis.stats_per_finestra.append(stats)

        logging.info(
            "  Finestra %3d gg: %d finestre, %.1f%% positive, Sharpe %.2f",
            dim, stats.totale_finestre, stats.pct_positive, stats.sharpe_ratio,
        )

    # Identifica finestra ottimale (max pct_positive, a parita' max Sharpe)
    if analysis.stats_per_finestra:
        analysis.finestra_ottimale = max(
            analysis.stats_per_finestra,
            key=lambda s: (s.pct_positive, s.sharpe_ratio),
        )
        logging.info(
            "Finestra ottimale '%s': %d giorni (%.1f%% positive, Sharpe %.2f).",
            ticker,
            analysis.finestra_ottimale.dimensione_finestra,
            analysis.finestra_ottimale.pct_positive,
            analysis.finestra_ottimale.sharpe_ratio,
        )

    return analysis
