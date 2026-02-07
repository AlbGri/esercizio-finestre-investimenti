"""Generazione CSV, summary testuale, grafici."""

import csv
import logging
import os
from dataclasses import asdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.analyzer import TickerAnalysis, WindowSizeStats


OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output")

# Colonne CSV nell'ordine specificato dal prompt
CSV_COLUMNS = [
    "dimensione_finestra", "totale_finestre", "finestre_positive",
    "finestre_negative", "pct_positive", "rendimento_medio",
    "rendimento_mediano", "sharpe_ratio", "deviazione_std",
    "best_rendimento", "best_data_inizio", "best_data_fine",
    "worst_rendimento", "worst_data_inizio", "worst_data_fine",
]


def ensure_output_dir() -> None:
    """Crea la directory output se non esiste."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)


def sanitize_filename(ticker: str) -> str:
    """Rimuove caratteri problematici dal nome ticker per usarlo come nome file."""
    return ticker.replace("^", "").replace(".", "_").replace("/", "_")


def write_csv(analysis: TickerAnalysis) -> str:
    """Scrive il CSV dei risultati per un ticker.

    Args:
        analysis: Risultato analisi ticker.

    Returns:
        Percorso del file CSV scritto.
    """
    ensure_output_dir()
    filename = f"results_{sanitize_filename(analysis.ticker)}.csv"
    filepath = os.path.join(OUTPUT_DIR, filename)

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for stats in analysis.stats_per_finestra:
            row = asdict(stats)
            writer.writerow({col: row[col] for col in CSV_COLUMNS})

    logging.info("CSV scritto: %s", filepath)
    return filepath


def format_ticker_summary(analysis: TickerAnalysis) -> str:
    """Formatta la sezione summary per un singolo ticker.

    Args:
        analysis: Risultato analisi ticker.

    Returns:
        Stringa formattata per il summary.
    """
    lines = []
    opt = analysis.finestra_ottimale
    if opt is None:
        lines.append(f"--- TICKER: {analysis.ticker} ---")
        lines.append("Nessuna finestra analizzabile.")
        return "\n".join(lines)

    lines.append(f"--- TICKER: {analysis.ticker} ---")
    lines.append(
        f"Finestra ottimale: {opt.dimensione_finestra} giorni "
        f"({opt.pct_positive}% finestre positive, Sharpe {opt.sharpe_ratio:.2f})"
    )

    dim_label = f"{opt.dimensione_finestra}gg"
    rend_medio_sign = "+" if opt.rendimento_medio >= 0 else ""
    rend_mediano_sign = "+" if opt.rendimento_mediano >= 0 else ""
    best_sign = "+" if opt.best_rendimento >= 0 else ""
    worst_sign = "+" if opt.worst_rendimento >= 0 else ""

    lines.append(
        f"Rendimento medio finestra ottimale ({dim_label}): "
        f"{rend_medio_sign}{opt.rendimento_medio:.1f}%"
    )
    lines.append(
        f"Rendimento mediano finestra ottimale ({dim_label}): "
        f"{rend_mediano_sign}{opt.rendimento_mediano:.1f}%"
    )
    lines.append(
        f"Miglior caso ({dim_label}): "
        f"{best_sign}{opt.best_rendimento:.1f}% ({opt.best_data_inizio} / {opt.best_data_fine})"
    )
    lines.append(
        f"Peggior caso ({dim_label}): "
        f"{worst_sign}{opt.worst_rendimento:.1f}% ({opt.worst_data_inizio} / {opt.worst_data_fine})"
    )

    return "\n".join(lines)


def write_summary(
    analyses: list[TickerAnalysis],
    config: dict,
    n_trading_days: int,
) -> str:
    """Genera e scrive il file summary.txt, e lo stampa nel log.

    Args:
        analyses: Lista analisi per ogni ticker.
        config: Configurazione completa.
        n_trading_days: Numero giorni trading nel periodo comune.

    Returns:
        Percorso del file summary scritto.
    """
    ensure_output_dir()

    sovr_str = "Si" if config["sovrapposte"] else "No"
    lines = [
        "=== ANALISI FINESTRE INVESTIMENTI ===",
        "",
        f"Periodo analisi: {config['data_inizio']} / {config['data_fine']} ({n_trading_days} giorni trading)",
        f"Capitale iniziale: {config['capitale_iniziale']:.2f} EUR",
        f"Commissioni: {config['commissione_fissa']:.2f} EUR fisso + {config['commissione_percentuale']:.2f}%",
        f"Tassa capital gain: {config['tassa_capital_gain']:.2f}%",
        f"Finestre sovrapposte: {sovr_str}",
        "",
    ]

    for analysis in analyses:
        lines.append(format_ticker_summary(analysis))
        lines.append("")

    summary_text = "\n".join(lines)

    filepath = os.path.join(OUTPUT_DIR, "summary.txt")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(summary_text)

    # Stampa anche nel log
    for line in summary_text.strip().split("\n"):
        logging.info(line)

    logging.info("Summary scritto: %s", filepath)
    return filepath


def write_chart(analyses: list[TickerAnalysis], config: dict | None = None) -> str:
    """Genera il grafico di confronto performance per dimensione finestra.

    Args:
        analyses: Lista analisi per ogni ticker (minimo 2).
        config: Configurazione completa (per periodo nel sottotitolo).

    Returns:
        Percorso del file PNG scritto.
    """
    ensure_output_dir()

    colors = ["#1f77b4", "#d62728", "#2ca02c", "#ff7f0e"]
    # Marker e linewidth diversi per distinguere ticker sovrapposti
    pct_markers = ["o", "^", "D", "v"]
    sharpe_markers = ["s", "P", "X", "*"]
    linewidths = [2.5, 2.0, 1.5, 1.5]

    fig, ax1 = plt.subplots(figsize=(14, 7))
    ax2 = ax1.twinx()

    # Raccogliamo il numero di finestre dal primo ticker per le annotazioni
    ref_analysis = next((a for a in analyses if a.stats_per_finestra), None)
    ref_counts = {}
    if ref_analysis:
        for s in ref_analysis.stats_per_finestra:
            ref_counts[s.dimensione_finestra] = s.totale_finestre

    pct_handles = []
    pct_labels = []
    sharpe_handles = []
    sharpe_labels = []

    for i, analysis in enumerate(analyses):
        if not analysis.stats_per_finestra:
            continue

        dims = [s.dimensione_finestra for s in analysis.stats_per_finestra]
        pct_pos = [s.pct_positive for s in analysis.stats_per_finestra]
        sharpe = [s.sharpe_ratio for s in analysis.stats_per_finestra]

        color = colors[i % len(colors)]
        mk_pct = pct_markers[i % len(pct_markers)]
        mk_sh = sharpe_markers[i % len(sharpe_markers)]
        lw = linewidths[i % len(linewidths)]

        h1, = ax1.plot(dims, pct_pos, linestyle="-", marker=mk_pct, color=color,
                       markersize=6, linewidth=lw)
        h2, = ax2.plot(dims, sharpe, linestyle="--", marker=mk_sh, color=color,
                       markersize=6, linewidth=lw, alpha=0.7)

        pct_handles.append(h1)
        pct_labels.append(f"{analysis.ticker} (% positive)")
        sharpe_handles.append(h2)
        sharpe_labels.append(f"{analysis.ticker} (Sharpe)")

    # Asse X: tick a ogni dimensione effettiva
    if ref_analysis:
        all_dims = [s.dimensione_finestra for s in ref_analysis.stats_per_finestra]
        ax1.set_xticks(all_dims)
        ax1.set_xticklabels(all_dims, fontsize=8)

    ax1.set_xlabel("Dimensione finestra (giorni trading)")
    ax1.set_ylabel("Finestre positive (%)")
    ax2.set_ylabel("Sharpe Ratio")

    ax1.set_ylim(bottom=0, top=105)
    ax1.grid(True, alpha=0.3)

    # Annotazione numero campioni sotto ogni tick dell'asse X
    if ref_counts:
        for dim, count in ref_counts.items():
            ax1.annotate(
                f"n={count}",
                xy=(dim, 0), xycoords=("data", "axes fraction"),
                xytext=(0, -28), textcoords="offset points",
                ha="center", va="top", fontsize=6.5, color="#555555",
            )

    # Legenda: riga 1 = % positive, riga 2 = Sharpe
    # matplotlib riempie per colonne, quindi interleave per ottenere
    # ogni colonna = un ticker (riga 0 = %pos, riga 1 = Sharpe)
    n_tickers = len(pct_handles)
    all_handles = []
    all_labels = []
    for ph, pl, sh, sl in zip(pct_handles, pct_labels, sharpe_handles, sharpe_labels):
        all_handles.extend([ph, sh])
        all_labels.extend([pl, sl])
    ax1.legend(all_handles, all_labels,
               loc="upper center", bbox_to_anchor=(0.5, -0.13),
               ncol=n_tickers, fontsize=8.5, framealpha=0.9)

    # Titolo con periodo
    title = "Confronto Performance per Dimensione Finestra"
    if config:
        sovr_label = "Finestre sovrapposte" if config["sovrapposte"] else "Finestre non sovrapposte"
        subtitle = f"Periodo: {config['data_inizio']} / {config['data_fine']}  |  {sovr_label}"
        fig.suptitle(title, fontsize=13, fontweight="bold")
        ax1.set_title(subtitle, fontsize=10, color="#555555", pad=4)
    else:
        plt.title(title)

    plt.tight_layout()
    fig.subplots_adjust(bottom=0.18)

    filepath = os.path.join(OUTPUT_DIR, "comparison_chart.png")
    fig.savefig(filepath, dpi=150)
    plt.close(fig)

    logging.info("Grafico scritto: %s", filepath)
    return filepath
