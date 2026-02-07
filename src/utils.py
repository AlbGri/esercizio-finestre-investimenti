"""Validazione input, setup logging, gestione errori."""

import logging
import sys
from datetime import date, datetime
from typing import Any


def setup_logging() -> None:
    """Configura logging su console con formato leggibile."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def parse_date(value: str, field_name: str) -> date:
    """Converte stringa YYYY-MM-DD in oggetto date.

    Args:
        value: Stringa data in formato YYYY-MM-DD.
        field_name: Nome del campo per messaggi di errore.

    Returns:
        Oggetto date corrispondente.
    """
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        logging.error("Campo '%s': formato data non valido '%s'. Usare YYYY-MM-DD.", field_name, value)
        sys.exit(1)


def validate_config(config: dict[str, Any]) -> dict[str, Any]:
    """Valida la configurazione e applica valori di default.

    Args:
        config: Dizionario di configurazione da YAML/CLI.

    Returns:
        Configurazione validata con default applicati.
    """
    # Campi obbligatori
    required = ["ticker_1", "ticker_2", "data_inizio", "data_fine",
                 "capitale_iniziale", "min_giorni_finestra",
                 "max_giorni_finestra", "step_giorni", "sovrapposte"]
    for field in required:
        if field not in config or config[field] is None:
            logging.error("Campo obbligatorio mancante: '%s'", field)
            sys.exit(1)

    # Default per campi opzionali
    defaults = {
        "benchmark_ticker": None,
        "commissione_fissa": 0.0,
        "commissione_percentuale": 0.0,
        "tassa_capital_gain": 26.0,
        "soglia_positiva": 0.0,
        "risk_free_rate": 0.0,
    }
    for key, default_val in defaults.items():
        if key not in config or config[key] is None:
            config[key] = default_val

    # Validazioni tipo e valore
    ticker_1 = str(config["ticker_1"]).strip()
    ticker_2 = str(config["ticker_2"]).strip()
    if not ticker_1:
        logging.error("ticker_1 non puo' essere vuoto.")
        sys.exit(1)
    if not ticker_2:
        logging.error("ticker_2 non puo' essere vuoto.")
        sys.exit(1)
    config["ticker_1"] = ticker_1
    config["ticker_2"] = ticker_2

    if config["benchmark_ticker"] is not None:
        config["benchmark_ticker"] = str(config["benchmark_ticker"]).strip() or None

    # Parse date
    config["data_inizio"] = parse_date(str(config["data_inizio"]), "data_inizio")
    config["data_fine"] = parse_date(str(config["data_fine"]), "data_fine")

    if config["data_inizio"] >= config["data_fine"]:
        logging.error("data_inizio (%s) deve essere precedente a data_fine (%s).",
                      config["data_inizio"], config["data_fine"])
        sys.exit(1)

    # Numerici
    capitale = float(config["capitale_iniziale"])
    if capitale <= 0:
        logging.error("capitale_iniziale deve essere > 0 (ricevuto: %s).", capitale)
        sys.exit(1)
    config["capitale_iniziale"] = capitale

    min_g = int(config["min_giorni_finestra"])
    max_g = int(config["max_giorni_finestra"])
    step = int(config["step_giorni"])

    if min_g >= max_g:
        logging.error("min_giorni_finestra (%d) deve essere < max_giorni_finestra (%d).", min_g, max_g)
        sys.exit(1)
    if step <= 0:
        logging.error("step_giorni deve essere > 0 (ricevuto: %d).", step)
        sys.exit(1)
    if min_g <= 0:
        logging.error("min_giorni_finestra deve essere > 0 (ricevuto: %d).", min_g)
        sys.exit(1)

    config["min_giorni_finestra"] = min_g
    config["max_giorni_finestra"] = max_g
    config["step_giorni"] = step

    config["commissione_fissa"] = float(config["commissione_fissa"])
    config["commissione_percentuale"] = float(config["commissione_percentuale"])
    config["tassa_capital_gain"] = float(config["tassa_capital_gain"])
    config["soglia_positiva"] = float(config["soglia_positiva"])
    config["risk_free_rate"] = float(config["risk_free_rate"])

    # Bool
    sovr = config["sovrapposte"]
    if isinstance(sovr, str):
        config["sovrapposte"] = sovr.lower() in ("true", "1", "si", "yes")
    else:
        config["sovrapposte"] = bool(sovr)

    return config
