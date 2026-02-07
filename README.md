# Esercizio Finestre Investimenti

Tool Python per analizzare rendimenti storici di strumenti finanziari (azioni, ETF, ETN) su finestre temporali variabili. Confronta le performance di due ticker su periodi definiti dall'utente, identificando la dimensione di finestra temporale che massimizza la probabilita' di rendimento positivo.

Per una spiegazione dei concetti (ticker, Sharpe ratio, finestre temporali, come interpretare i risultati) consulta la [Guida ai concetti](docs/guida.md).

## Requisiti

- Python 3.12+
- Miniconda (o Anaconda)

## Installazione

Creare un environment conda dedicato e installare le dipendenze:

```bash
conda create -n finestre-inv python=3.12 -y
conda activate finestre-inv
pip install -r requirements.txt
```

## Configurazione

Modificare il file `config.yaml` con i parametri desiderati:

```yaml
# Ticker da analizzare
ticker_1: "SPY"
ticker_2: "QQQ"
benchmark_ticker: null  # opzionale, esempio: "^GSPC"

# Periodo analisi
data_inizio: "2023-01-01"
data_fine: "2025-02-06"

# Capitale e costi
capitale_iniziale: 5000.0
commissione_fissa: 0.0
commissione_percentuale: 0.0
tassa_capital_gain: 26.0

# Parametri finestre
min_giorni_finestra: 5
max_giorni_finestra: 90
step_giorni: 5
sovrapposte: true

# Metriche
soglia_positiva: 0.0
risk_free_rate: 0.0
```

## Uso

### Esecuzione con file di configurazione (default: config.yaml)

```bash
python main.py
```

### Esecuzione con file di configurazione specifico

```bash
python main.py --config percorso/mio_config.yaml
```

### Override parametri da CLI

Qualsiasi parametro del config.yaml puo' essere sovrascritto da CLI:

```bash
python main.py --ticker-1 AAPL --ticker-2 MSFT --data-inizio 2022-01-01 --data-fine 2024-12-31
```

```bash
python main.py --capitale-iniziale 10000 --commissione-fissa 2.95 --sovrapposte false
```

### Esempio completo solo da CLI

```bash
python main.py --ticker-1 SPY --ticker-2 QQQ --data-inizio 2020-01-01 --data-fine 2025-02-06 --capitale-iniziale 10000 --min-giorni-finestra 5 --max-giorni-finestra 60 --step-giorni 5 --sovrapposte true
```

## Output

I risultati vengono salvati nella directory `output/`:

- **results_{ticker}.csv** - Una riga per ogni dimensione finestra testata, con statistiche aggregate (percentuale positive, rendimento medio/mediano, Sharpe ratio, best/worst case con date).
- **summary.txt** - Riepilogo testuale con finestra ottimale per ciascun ticker e statistiche principali.
- **comparison_chart.png** - Grafico con asse X = dimensione finestra, linee continue per percentuale finestre positive, linee tratteggiate per Sharpe ratio.

## Note

- **Adj Close**: Il tool utilizza il prezzo di chiusura aggiustato (Adjusted Close) fornito da Yahoo Finance, che tiene conto di dividendi e split azionari.
- **Giorni di trading**: Le finestre sono espresse in giorni di borsa effettivi (weekend e festivi esclusi). Yahoo Finance fornisce solo dati per giorni di trading.
- **Commissioni**: Viene modellata solo la commissione di acquisto (non di vendita) per semplicita'.
- **Tasse**: L'aliquota capital gain (default 26% Italia) si applica solo ai profitti, non alle perdite.
- **Valute diverse**: Se i ticker sono quotati in valute diverse, il tool mostra un warning. Il confronto in quel caso potrebbe non essere significativo poiche' non vengono effettuate conversioni valutarie.
- **Finestre sovrapposte**: Con `sovrapposte: true`, le finestre scorrono giorno per giorno (rolling windows) generando molti piu' campioni. Con `sovrapposte: false`, i periodi sono blocchi consecutivi non sovrapposti.
- **Fonte dati**: Yahoo Finance tramite libreria yfinance. La disponibilita' e accuratezza dei dati dipendono dal servizio.

## Esempi configurazione

### Confronto ETF S&P500 vs NASDAQ con benchmark

```yaml
ticker_1: "SPY"
ticker_2: "QQQ"
benchmark_ticker: "^GSPC"
data_inizio: "2020-01-01"
data_fine: "2025-02-06"
capitale_iniziale: 10000.0
min_giorni_finestra: 5
max_giorni_finestra: 60
step_giorni: 5
sovrapposte: true
```

### Finestre non sovrapposte (analisi piu' veloce)

```yaml
sovrapposte: false
min_giorni_finestra: 30
max_giorni_finestra: 90
step_giorni: 30
```

### Con costi reali

```yaml
commissione_fissa: 2.95
commissione_percentuale: 0.0
tassa_capital_gain: 26.0
capitale_iniziale: 5000.0
```
