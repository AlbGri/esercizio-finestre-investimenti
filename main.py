"""Entry point: parsing argomenti CLI, caricamento YAML, orchestrazione."""

import argparse
import logging
import os
import sys

import yaml

from src.utils import setup_logging, validate_config
from src.data_loader import load_data
from src.analyzer import analizza_ticker
from src.reporter import write_csv, write_summary, write_chart


def load_yaml_config(path: str) -> dict:
    """Carica configurazione da file YAML.

    Args:
        path: Percorso al file YAML.

    Returns:
        Dizionario configurazione.
    """
    if not os.path.isfile(path):
        logging.error("File configurazione non trovato: %s", path)
        sys.exit(1)
    with open(path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    if not isinstance(config, dict):
        logging.error("Il file configurazione '%s' non contiene un dizionario YAML valido.", path)
        sys.exit(1)
    return config


def build_parser() -> argparse.ArgumentParser:
    """Costruisce il parser argomenti CLI."""
    parser = argparse.ArgumentParser(
        description="Analisi finestre investimenti: confronta performance di ticker su finestre temporali variabili.",
    )
    parser.add_argument("--config", default="config.yaml",
                        help="Percorso file configurazione YAML (default: config.yaml)")
    # Override dei parametri YAML
    parser.add_argument("--ticker-1", dest="ticker_1")
    parser.add_argument("--ticker-2", dest="ticker_2")
    parser.add_argument("--benchmark-ticker", dest="benchmark_ticker")
    parser.add_argument("--data-inizio", dest="data_inizio")
    parser.add_argument("--data-fine", dest="data_fine")
    parser.add_argument("--capitale-iniziale", dest="capitale_iniziale", type=float)
    parser.add_argument("--commissione-fissa", dest="commissione_fissa", type=float)
    parser.add_argument("--commissione-percentuale", dest="commissione_percentuale", type=float)
    parser.add_argument("--tassa-capital-gain", dest="tassa_capital_gain", type=float)
    parser.add_argument("--min-giorni-finestra", dest="min_giorni_finestra", type=int)
    parser.add_argument("--max-giorni-finestra", dest="max_giorni_finestra", type=int)
    parser.add_argument("--step-giorni", dest="step_giorni", type=int)
    parser.add_argument("--sovrapposte", dest="sovrapposte", type=str,
                        help="true/false")
    parser.add_argument("--soglia-positiva", dest="soglia_positiva", type=float)
    parser.add_argument("--risk-free-rate", dest="risk_free_rate", type=float)
    return parser


def merge_cli_overrides(config: dict, args: argparse.Namespace) -> dict:
    """Sovrascrive valori YAML con argomenti CLI se specificati.

    Args:
        config: Configurazione da YAML.
        args: Argomenti parsati da CLI.

    Returns:
        Configurazione con override applicati.
    """
    cli_dict = vars(args)
    for key in ["ticker_1", "ticker_2", "benchmark_ticker", "data_inizio",
                 "data_fine", "capitale_iniziale", "commissione_fissa",
                 "commissione_percentuale", "tassa_capital_gain",
                 "min_giorni_finestra", "max_giorni_finestra", "step_giorni",
                 "sovrapposte", "soglia_positiva", "risk_free_rate"]:
        val = cli_dict.get(key)
        if val is not None:
            config[key] = val
    return config


def main() -> None:
    """Funzione principale: carica config, scarica dati, analizza, genera output."""
    setup_logging()

    parser = build_parser()
    args = parser.parse_args()

    # Carica YAML (se esiste)
    config: dict = {}
    if os.path.isfile(args.config):
        config = load_yaml_config(args.config)
    else:
        logging.warning("File configurazione '%s' non trovato, uso solo parametri CLI.", args.config)

    # Override CLI
    config = merge_cli_overrides(config, args)

    # Validazione
    config = validate_config(config)

    logging.info("Configurazione validata. Avvio analisi...")

    # Download dati
    data = load_data(
        ticker_1=config["ticker_1"],
        ticker_2=config["ticker_2"],
        data_inizio=config["data_inizio"],
        data_fine=config["data_fine"],
        min_giorni_finestra=config["min_giorni_finestra"],
        benchmark_ticker=config["benchmark_ticker"],
    )

    n_trading_days = len(next(iter(data.values())))

    # Parametri comuni analisi
    analysis_params = dict(
        capitale_iniziale=config["capitale_iniziale"],
        min_giorni=config["min_giorni_finestra"],
        max_giorni=config["max_giorni_finestra"],
        step_giorni=config["step_giorni"],
        sovrapposte=config["sovrapposte"],
        commissione_fissa=config["commissione_fissa"],
        commissione_percentuale=config["commissione_percentuale"],
        tassa_capital_gain=config["tassa_capital_gain"],
        soglia_positiva=config["soglia_positiva"],
        risk_free_rate=config["risk_free_rate"],
    )

    # Analisi ticker
    tickers_to_analyze = [config["ticker_1"], config["ticker_2"]]
    if config["benchmark_ticker"]:
        tickers_to_analyze.append(config["benchmark_ticker"])

    analyses = []
    for ticker in tickers_to_analyze:
        analysis = analizza_ticker(
            ticker=ticker,
            prices=data[ticker],
            **analysis_params,
        )
        analyses.append(analysis)

    # Output CSV
    for analysis in analyses:
        write_csv(analysis)

    # Summary
    write_summary(analyses, config, n_trading_days)

    # Grafico
    write_chart(analyses, config)

    logging.info("Analisi completata. Risultati nella directory 'output/'.")


if __name__ == "__main__":
    main()
