# PROMPT.MD - Esercizio Finestre Investimenti

## PARTE 1 - CONFIGURAZIONE AMBIENTE

### Contesto sistema sviluppatore
Sto lavorando su **Windows 11** con la seguente configurazione:
- **Python**: NON e' installato a livello di sistema. Il comando `python` nel terminale punta allo stub Microsoft Store e non funziona.
- **Gestore ambienti**: Uso **Miniconda**, installato in `C:\ProgramData\miniconda3` (installazione di sistema, read-only).
- **Conda version**: 25.1.1 (o successiva)
- **Solver**: libmamba
- **Directory environments**: `C:\Users\Alberto\.conda\envs\`
- **pip e python** funzionano SOLO dentro un conda environment attivato.
- **VS Code**: e' il mio IDE principale. L'interprete Python va selezionato dall'environment conda del progetto.

### Istruzioni per la verifica ambiente
Prima di sviluppare qualsiasi progetto Python, segui questa procedura:

1. **NON eseguire** `python --version` o `pip --version` direttamente: falliranno perche' Python non e' nel PATH di sistema.

2. **Verifica conda** con:
   ```
   powershell.exe -Command "& 'C:\ProgramData\miniconda3\Scripts\conda.exe' --version"
   ```

3. **Lista environment esistenti**:
   ```
   powershell.exe -Command "& 'C:\ProgramData\miniconda3\Scripts\conda.exe' env list"
   ```

4. **Crea un nuovo environment dedicato** per il progetto (nome che richiami il progetto):
   ```
   powershell.exe -Command "& 'C:\ProgramData\miniconda3\Scripts\conda.exe' create -n NOME_ENV python=3.12 -y"
   ```

5. **Installa dipendenze** usando il python dell'environment:
   ```
   powershell.exe -Command "& 'C:\Users\Alberto\.conda\envs\NOME_ENV\python.exe' -m pip install PACCHETTO"
   ```

6. **Esegui script** usando il python dell'environment:
   ```
   powershell.exe -Command "& 'C:\Users\Alberto\.conda\envs\NOME_ENV\python.exe' script.py"
   ```

### Note importanti
- Se il terminale Claude Code usa bash (Git Bash/WSL), i comandi Windows con backslash non funzionano. Usa sempre `powershell.exe -Command "..."` come wrapper.
- I percorsi conda dell'utente sono: `C:\Users\Alberto\.conda\envs\`
- Ogni progetto deve avere il **proprio environment isolato**.
- Il file `requirements.txt` deve essere presente in ogni progetto per riproducibilita.
- L'utente attivera' l'environment nel terminale VS Code con `conda activate NOME_ENV` prima di lavorare interattivamente.

### Setup VS Code per il progetto
Dopo aver creato l'environment, l'utente dovra':
1. Aprire VS Code nel progetto
2. `Ctrl + Shift + P` > "Python: Select Interpreter"
3. Selezionare l'environment conda del progetto
4. Il terminale integrato usera' automaticamente quell'environment se configurato con:
   ```
   "python.condaPath": "C:\\ProgramData\\miniconda3\\Scripts\\conda.exe"
   ```

---

## PARTE 2 - OBIETTIVO PROGETTO

### Scopo
Creare un tool Python per analizzare rendimenti storici di strumenti finanziari (azioni, ETF, ETN) su finestre temporali variabili. Il tool confronta le performance di due ticker su periodi definiti dall'utente, identificando la dimensione di finestra temporale che massimizza la probabilita' di rendimento positivo.

### Principio base
Dato un capitale iniziale, il tool simula investimenti ripetuti su finestre temporali di diversa durata (esempio: 5 giorni, 10 giorni, 15 giorni, ecc.) e calcola:
- Quante volte avresti guadagnato (finestre positive)
- Quanto avresti guadagnato in media
- Qual e' la finestra temporale piu' "affidabile" (massima percentuale di successo)

### Caso d'uso esempio
Utente vuole sapere: "Se avessi investito 5000 euro in S&P500 vs NASDAQ100 negli ultimi 2 anni, quale finestra temporale (10 giorni? 30 giorni? 60 giorni?) avrebbe dato piu' probabilita' di guadagno?"

---

## PARTE 3 - REQUISITI FUNZIONALI

### 3.1 Parametri di Input

#### Parametri obbligatori (configurabili via YAML o CLI):
- `ticker_1`: str - Ticker Yahoo Finance del primo strumento (es. "SPY", "3USL.MI")
- `ticker_2`: str - Ticker Yahoo Finance del secondo strumento (es. "QQQ", "VUSA.L")
- `data_inizio`: date - Data inizio periodo analisi (formato YYYY-MM-DD)
- `data_fine`: date - Data fine periodo analisi (formato YYYY-MM-DD)
- `capitale_iniziale`: float - Capitale investito in ogni finestra (es. 5000.0)
- `min_giorni_finestra`: int - Dimensione minima finestra in giorni di trading (es. 5)
- `max_giorni_finestra`: int - Dimensione massima finestra in giorni di trading (es. 90)
- `step_giorni`: int - Incremento tra dimensioni finestre (es. 5 significa: 5, 10, 15, ..., 90)
- `sovrapposte`: bool - True = finestre rolling (scorrimento giornaliero), False = finestre consecutive non sovrapposte

#### Parametri opzionali con default:
- `benchmark_ticker`: str - Ticker terzo strumento per confronto (default: None)
- `commissione_fissa`: float - Costo fisso per operazione in euro (default: 0.0)
- `commissione_percentuale`: float - Costo percentuale su capitale (default: 0.0, es. 0.19 = 0.19%)
- `tassa_capital_gain`: float - Aliquota fiscale su profitti in % (default: 26.0 per Italia)
- `soglia_positiva`: float - Soglia minima rendimento per considerare finestra "positiva" (default: 0.0)
- `risk_free_rate`: float - Tasso risk-free annualizzato per calcolo Sharpe (default: 0.0)

### 3.2 Validazione Input

Prima di procedere, il tool deve verificare:
- `data_inizio` < `data_fine`
- `min_giorni_finestra` < `max_giorni_finestra`
- `step_giorni` > 0
- `capitale_iniziale` > 0
- Ticker non vuoti

In caso di errore: stampare messaggio chiaro e terminare con `sys.exit(1)`.

### 3.3 Download Dati Storici

**Fonte dati**: Yahoo Finance tramite libreria `yfinance`

**Campo da utilizzare**: `Adj Close` (prezzo aggiustato per dividendi e split)

**Processo**:
1. Scarica dati per `ticker_1`, `ticker_2` (e `benchmark_ticker` se presente) nel periodo richiesto
2. Se ticker non trovato: messaggio "Ticker X non trovato su Yahoo Finance, verificare su finance.yahoo.com" e terminare
3. Se ticker in valute diverse: warning "[WARNING] Ticker1 in USD, Ticker2 in EUR - confronto potrebbe non essere significativo"
4. Calcola **intersezione delle date** disponibili per tutti i ticker
5. Se periodo comune < `min_giorni_finestra`: errore "Periodo sovrapposizione insufficiente (X giorni trading), servono almeno Y" e terminare
6. Se periodo ridotto rispetto a richiesta utente: warning "[WARNING] Periodo ridotto a date comuni disponibili: YYYY-MM-DD / YYYY-MM-DD"

**Nota giorni**: Utilizzare **giorni di trading** (sessioni di borsa effettive). Yahoo Finance fornisce gia' solo giorni trading (weekend/festivi esclusi automaticamente).

### 3.4 Logica Analisi Finestre

Per ogni ticker e per ogni dimensione finestra (da `min_giorni` a `max_giorni` con `step`):

#### Generazione finestre

**Se `sovrapposte = True` (rolling windows):**
- Scorri i dati giorno per giorno
- Ogni finestra parte dal giorno N e copre N+dimensione_finestra giorni trading
- Esempio: con 365 giorni trading e finestra 30gg, generi circa 336 finestre

**Se `sovrapposte = False` (blocchi consecutivi):**
- Dividi periodo in blocchi consecutivi non sovrapposti
- Esempio: con 365 giorni trading e finestra 30gg, generi circa 12 finestre
- Eventuali giorni rimanenti alla fine vengono scartati

#### Calcolo rendimento per singola finestra

Per ogni finestra:

1. **Prezzo iniziale**: `Adj Close` del primo giorno finestra
2. **Prezzo finale**: `Adj Close` dell'ultimo giorno finestra
3. **Calcolo capitale netto dopo commissioni acquisto** (nota: si modella solo la commissione di acquisto, non di vendita, per semplicita'):
   ```
   costo_acquisto = commissione_fissa + (capitale_iniziale * commissione_percentuale / 100)
   capitale_netto = capitale_iniziale - costo_acquisto
   ```
4. **Quote acquistabili**: `capitale_netto / prezzo_iniziale`
5. **Valore finale lordo**: `quote * prezzo_finale`
6. **Rendimento lordo %**: `((valore_finale - capitale_iniziale) / capitale_iniziale) * 100`
7. **Rendimento netto (dopo tasse)**:
   ```
   Se rendimento_lordo > 0:
       profitto_lordo = valore_finale - capitale_iniziale
       tasse = profitto_lordo * (tassa_capital_gain / 100)
       valore_finale_netto = valore_finale - tasse
       rendimento_netto = ((valore_finale_netto - capitale_iniziale) / capitale_iniziale) * 100
   Altrimenti:
       rendimento_netto = rendimento_lordo  (nessuna tassa su perdite)
   ```

### 3.5 Statistiche Aggregate

Per ogni combinazione (ticker, dimensione_finestra) calcolare.
**Nota**: tutte le statistiche aggregate (media, mediana, deviazione standard, Sharpe, soglia positiva) utilizzano il `rendimento_netto` (dopo commissioni e tasse) calcolato in 3.4.

#### Statistiche base:
- Totale finestre analizzate
- Numero finestre con rendimento > `soglia_positiva` (finestre positive)
- Numero finestre con rendimento <= `soglia_positiva` (finestre negative)
- Percentuale finestre positive: `(positive / totale) * 100`
- Rendimento medio % (media aritmetica di tutti i rendimenti)
- Rendimento mediano % (mediana di tutti i rendimenti)
- Deviazione standard dei rendimenti

#### Best/Worst case:
- **Migliore finestra**: rendimento massimo con date inizio/fine
- **Peggior finestra**: rendimento minimo con date inizio/fine

#### Metriche rischio/rendimento:
- **Sharpe Ratio**:
  ```
  Calcolo:
  1. Calcola rendimento_medio delle finestre
  2. Annualizza: rendimento_medio_annuo = rendimento_medio * (252 / dimensione_finestra)
     (252 = giorni trading standard in un anno)
  3. Sottrai tasso risk-free: excess_return = rendimento_medio_annuo - risk_free_rate
  4. Annualizza deviazione standard: std_annua = std_dev * sqrt(252 / dimensione_finestra)
  5. Sharpe = excess_return / std_annua
  ```

### 3.6 Identificazione Finestra Ottimale

Per ciascun ticker, identificare la dimensione di finestra che **massimizza la percentuale di finestre positive** nel range testato (min_giorni - max_giorni).

In caso di parita', preferire la finestra con Sharpe Ratio piu' alto.

---

## PARTE 4 - REQUISITI TECNICI

### 4.1 Dipendenze

**requirements.txt**:
```
yfinance>=0.2.0
pandas>=2.0.0
numpy>=1.24.0
matplotlib>=3.7.0
pyyaml>=6.0
```

### 4.2 Struttura Repository

```
esercizio-finestre-investimenti/
├── README.md                 # Istruzioni uso + esempio configurazione
├── requirements.txt          # Dipendenze Python
├── config.yaml              # File configurazione esempio
├── main.py                  # Entry point, parsing argomenti CLI
├── src/
│   ├── __init__.py
│   ├── data_loader.py       # Download dati Yahoo Finance, intersezione date
│   ├── analyzer.py          # Logica rolling windows, calcolo rendimenti, statistiche
│   ├── reporter.py          # Generazione CSV, summary testuale, grafici
│   └── utils.py             # Validazione input, gestione errori, logging
└── output/                  # Directory creata automaticamente per risultati
    ├── results_ticker1.csv
    ├── results_ticker2.csv
    ├── results_benchmark.csv  (se presente)
    ├── summary.txt
    └── comparison_chart.png
```

### 4.3 Stile Codice

**Principi fondamentali**:
- Codice semplice, leggibile, ben commentato
- NO complessita' inutile, NO over-engineering
- Preferire chiarezza a performance estreme

**Standard**:
- Python 3.12+
- Type hints su tutte le funzioni pubbliche
- Docstrings in formato Google style per classi e funzioni pubbliche
- Commenti inline per logica non ovvia
- Nomi variabili descrittivi (no abbreviazioni criptiche)
- Formattazione: seguire PEP 8 base (line length 100 caratteri accettabile)

**Logging**:
- Usare modulo `logging` standard (NO print per output informativo)
- Livello INFO per progress (es. "Download ticker X completato")
- Livello WARNING per situazioni non bloccanti (es. valute diverse, periodo ridotto)
- Livello ERROR per problemi bloccanti
- Output su console, non su file

**NO**:
- NO emoji in codice, commenti, log, output
- NO print() per informazioni di servizio (usare logging)
- NO dipendenze esterne non necessarie
- NO database (tutto in memoria/CSV)
- NO GUI (tool CLI)

### 4.4 Gestione Errori

**Strategia**:
- Validazione input all'inizio (fail-fast)
- Try-except su operazioni esterne (network, file I/O)
- Messaggi di errore chiari e actionable per l'utente
- Preferire terminazione pulita (con messaggio) a comportamenti imprevedibili

**Esempio approccio**:
```python
# In caso di errore critico:
logging.error("Ticker SPY non trovato su Yahoo Finance")
logging.error("Verificare ticker su https://finance.yahoo.com")
sys.exit(1)

# In caso di warning:
logging.warning("Ticker1 in USD, Ticker2 in EUR - confronto potrebbe non essere significativo")
# ... continua esecuzione
```

### 4.5 Configurazione

**File config.yaml esempio**:
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

**CLI override**: permettere di sovrascrivere config.yaml con argomenti CLI (usando argparse).

---

## PARTE 5 - OUTPUT E REPORTING

### 5.1 File CSV

**Nome file**: `results_{ticker_name}.csv` (esempio: `results_SPY.csv`)

**Colonne**:
- `dimensione_finestra` (int): giorni trading della finestra
- `totale_finestre` (int): numero finestre analizzate
- `finestre_positive` (int): count finestre con rendimento > soglia
- `finestre_negative` (int): count finestre con rendimento <= soglia
- `pct_positive` (float): percentuale finestre positive
- `rendimento_medio` (float): media rendimenti in %
- `rendimento_mediano` (float): mediana rendimenti in %
- `sharpe_ratio` (float): Sharpe ratio annualizzato
- `deviazione_std` (float): deviazione standard rendimenti
- `best_rendimento` (float): rendimento massimo osservato
- `best_data_inizio` (str): data inizio finestra migliore (YYYY-MM-DD)
- `best_data_fine` (str): data fine finestra migliore (YYYY-MM-DD)
- `worst_rendimento` (float): rendimento minimo osservato
- `worst_data_inizio` (str): data inizio finestra peggiore (YYYY-MM-DD)
- `worst_data_fine` (str): data fine finestra peggiore (YYYY-MM-DD)

**Formato**: una riga per ogni dimensione finestra testata.

### 5.2 Summary Testuale

**File**: `summary.txt` (e anche stampato su console)

**Formato esempio**:
```
=== ANALISI FINESTRE INVESTIMENTI ===

Periodo analisi: 2023-01-01 / 2025-02-06 (504 giorni trading)
Capitale iniziale: 5000.00 EUR
Commissioni: 0.00 EUR fisso + 0.00%
Tassa capital gain: 26.00%
Finestre sovrapposte: Si

--- TICKER 1: SPY ---
Finestra ottimale: 15 giorni (92.3% finestre positive, Sharpe 1.85)
Rendimento medio finestra ottimale (15gg): +3.2%
Rendimento mediano finestra ottimale (15gg): +2.8%
Miglior caso (15gg): +18.5% (2024-03-15 / 2024-04-14)
Peggior caso (15gg): -12.3% (2024-08-01 / 2024-08-31)

--- TICKER 2: QQQ ---
Finestra ottimale: 10 giorni (89.1% finestre positive, Sharpe 1.62)
Rendimento medio finestra ottimale (10gg): +4.1%
Rendimento mediano finestra ottimale (10gg): +3.5%
Miglior caso (10gg): +22.1% (2024-03-15 / 2024-04-14)
Peggior caso (10gg): -15.7% (2024-08-01 / 2024-08-31)

--- BENCHMARK: ^GSPC (opzionale, se presente) ---
[stesse statistiche]

[Eventuali WARNING emessi durante l'analisi]
```

### 5.3 Grafico

**File**: `comparison_chart.png`

**Contenuto**:
- Grafico unico con asse X = dimensione finestra (giorni)
- Asse Y sinistro: percentuale finestre positive (0-100%)
- Asse Y destro: Sharpe Ratio
- Linee:
  - Linea continua ticker_1 (% positive)
  - Linea continua ticker_2 (% positive)
  - Linea tratteggiata ticker_1 (Sharpe)
  - Linea tratteggiata ticker_2 (Sharpe)
  - (Se benchmark presente: aggiungere terze linee)
- Legenda chiara
- Titolo: "Confronto Performance per Dimensione Finestra"
- Griglia per leggibilita'

**Stile**:
- Colori distinti per ticker (es. blu, rosso, verde)
- Dimensione adeguata (es. 12x6 inch)
- DPI 150 per qualita' sufficiente

---

## PARTE 6 - README.md

Il file README.md deve contenere:

1. **Descrizione progetto**: cosa fa in 2-3 frasi
2. **Requisiti**: Python 3.12+, Miniconda
3. **Installazione**:
   - Creazione environment conda dedicato
   - Installazione dipendenze da requirements.txt
4. **Configurazione**: come modificare config.yaml
5. **Uso**:
   - Esecuzione con config file
   - Esecuzione con argomenti CLI
   - Esempi pratici
6. **Output**: descrizione file generati
7. **Note**:
   - Utilizzo Adj Close per dividendi
   - Definizione "giorni trading"
   - Limitazioni (valute diverse, dati Yahoo Finance)
8. **Esempi configurazione** per casi d'uso comuni

---

## PARTE 7 - NOTE IMPLEMENTATIVE

### Priorita' sviluppo

**Fase 1 - Core minimo**:
1. `data_loader.py`: download dati, intersezione date, validazioni base
2. `analyzer.py`: generazione finestre, calcolo rendimenti, statistiche aggregate
3. `reporter.py`: CSV output e summary testuale
4. `main.py`: orchestrazione e argparse

**Fase 2 - Completamento**:
5. Grafici (matplotlib)
6. Supporto benchmark (terzo ticker)
7. Logging strutturato
8. README completo

### Testing

Non e' richiesta suite completa di test, ma e' utile verificare manualmente:
- Ticker inesistenti (deve fallire gracefully)
- Periodo con pochi dati (deve avvisare o bloccare)
- Configurazioni edge case (min=max, step>range, ecc.)
- Valute diverse (deve mostrare warning)

### Performance

Non e' un requisito critico, ma considera:
- Con `sovrapposte=True` e 500 giorni trading, finestra 5gg, step 1: circa 500 finestre per dimensione
- Se test 18 dimensioni (5 a 90 step 5): 9000 finestre totali per ticker
- Dovrebbe completare in < 30 secondi su hardware medio

Se troppo lento: logging progress ogni X finestre processate.

---

## PARTE 8 - COSA NON FARE

Per mantenere progetto snello:

**NO**:
- NO database (SQLite, PostgreSQL, ecc.)
- NO web interface/API
- NO ottimizzazioni premature (numba, cython, multiprocessing)
- NO export formati esotici (Excel con formattazione, PDF reports)
- NO backtesting avanzato (trailing stop, rebalancing, ecc.)
- NO machine learning per predizioni
- NO gestione portfolio multipli contemporaneamente
- NO interfaccia grafica (GUI)
- NO conversioni valute automatiche
- NO gestione split/dividendi manuale (yfinance lo fa gia')
- NO test coverage obbligatorio (ma benvenuto se utile)

**SI' (mantenere focus)**:
- Codice leggibile e manutenibile
- Validazioni chiare con errori informativi
- Output utilizzabile (CSV + grafico)
- Configurazione flessibile (YAML + CLI)
- Documentazione essenziale

---

## PARTE 9 - ESEMPI CASI D'USO

### Caso 1: Confronto ETF S&P500 vs NASDAQ
```yaml
ticker_1: "SPY"
ticker_2: "QQQ"
data_inizio: "2020-01-01"
data_fine: "2025-02-06"
capitale_iniziale: 10000.0
min_giorni_finestra: 5
max_giorni_finestra: 60
step_giorni: 5
sovrapposte: true
```

### Caso 2: Analisi con benchmark
```yaml
ticker_1: "VUSA.L"  # ETF S&P500 quotato Londra
ticker_2: "EQQQ.L"  # ETF NASDAQ quotato Londra
benchmark_ticker: "^GSPC"  # Indice S&P500
```

### Caso 3: Finestre non sovrapposte (piu' veloce)
```yaml
sovrapposte: false
min_giorni_finestra: 30
max_giorni_finestra: 90
step_giorni: 30  # Testa solo 30, 60, 90 giorni
```

### Caso 4: Con costi reali
```yaml
commissione_fissa: 2.95  # Degiro esempio
commissione_percentuale: 0.0
tassa_capital_gain: 26.0  # Italia
capitale_iniziale: 5000.0
```

