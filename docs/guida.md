# Guida al Tool - Finestre Investimenti

Questa guida spiega in modo semplice come funziona il tool, cosa significano i termini usati e come interpretare i risultati. Non servono conoscenze finanziarie avanzate.

---

## 1. Cosa fa questo tool

Immagina di voler capire: "Se avessi investito una somma in un certo strumento finanziario, dopo quanti giorni avrei avuto piu' probabilita' di rivendere in guadagno?"

Il tool risponde a questa domanda. Prende i dati storici dei prezzi, simula centinaia di operazioni "compra e vendi dopo X giorni" e conta quante volte avresti guadagnato e quante perso. Lo fa per diverse durate (5 giorni, 10 giorni, 15 giorni, ecc.) e ti dice quale durata ha funzionato meglio nel periodo analizzato.

**Attenzione**: i risultati si basano sul passato. Non sono previsioni sul futuro.

---

## 2. Concetti base

### Ticker

Un **ticker** e' il codice che identifica uno strumento finanziario sui mercati. Esempi:
- `SPY` = ETF che replica l'indice S&P 500 (le 500 aziende piu' grandi USA)
- `QQQ` = ETF che replica il NASDAQ-100 (le 100 aziende tech piu' grandi)
- `^GSPC` = L'indice S&P 500 stesso (non acquistabile direttamente)

Puoi cercare i ticker su [finance.yahoo.com](https://finance.yahoo.com).

### ETF

Un **ETF** (Exchange-Traded Fund) e' un fondo che puoi comprare e vendere come un'azione normale. Replica l'andamento di un indice, un settore o un paniere di titoli. Per esempio, comprare SPY equivale a comprare un pezzettino di tutte le 500 aziende dell'S&P 500.

### Adj Close (Prezzo di chiusura aggiustato)

Ogni giorno di borsa, un titolo ha un prezzo di apertura e uno di chiusura. L'**Adj Close** e' il prezzo di chiusura "aggiustato" per tenere conto di dividendi distribuiti e split azionari. E' il dato piu' corretto da usare per calcolare i rendimenti reali.

### Giorni di trading

La borsa non e' aperta tutti i giorni: e' chiusa nei weekend e nei giorni festivi. Quando il tool parla di "15 giorni", intende 15 **giorni di borsa aperta** (circa 3 settimane di calendario).

Riferimento approssimativo:
- 5 giorni di trading = circa 1 settimana
- 21 giorni di trading = circa 1 mese
- 63 giorni di trading = circa 3 mesi
- 252 giorni di trading = circa 1 anno

---

## 3. Come funziona l'analisi

### Finestra temporale

Una **finestra** e' un periodo di tempo in cui si simula un investimento: compri il primo giorno e vendi l'ultimo giorno della finestra.

Esempio con finestra di 10 giorni e dati dal 2 al 16 gennaio:
- Compri il 2 gennaio, vendi il 15 gennaio (10 giorni di borsa)
- Risultato: se il prezzo e' salito, hai guadagnato; se e' sceso, hai perso

### Finestre sovrapposte vs non sovrapposte

**Sovrapposte (rolling)**: il tool fa scorrere la finestra un giorno alla volta.
- Finestra 1: giorno 1-10
- Finestra 2: giorno 2-11
- Finestra 3: giorno 3-12
- ...e cosi' via

Questo genera molti campioni (centinaia), dando risultati statisticamente piu' stabili.

**Non sovrapposte**: le finestre sono blocchi consecutivi senza sovrapposizione.
- Finestra 1: giorno 1-10
- Finestra 2: giorno 11-20
- Finestra 3: giorno 21-30

Genera meno campioni ma sono indipendenti tra loro.

**Quando usare quale**: le finestre sovrapposte sono preferibili nella maggior parte dei casi perche' danno piu' dati. Quelle non sovrapposte sono utili se vuoi campioni completamente indipendenti.

### Il rendimento

Il **rendimento** e' la percentuale di guadagno o perdita rispetto al capitale investito.

Esempio: investi 5000 EUR, dopo 15 giorni il valore e' 5150 EUR.
- Rendimento = ((5150 - 5000) / 5000) * 100 = +3.0%

Se il valore fosse sceso a 4800 EUR:
- Rendimento = ((4800 - 5000) / 5000) * 100 = -4.0%

Il tool calcola il rendimento **netto**, cioe' dopo aver sottratto:
1. **Commissioni di acquisto** (se impostate)
2. **Tasse sui profitti** (solo se hai guadagnato - in Italia il 26%)

---

## 4. Le metriche nei risultati

### Percentuale finestre positive

La metrica piu' intuitiva: su tutte le finestre simulate, quante hanno chiuso in guadagno?

Esempio: "90% finestre positive con finestra 30 giorni" significa che, nel periodo analizzato, 9 volte su 10 avresti guadagnato comprando e vendendo dopo 30 giorni di trading.

### Rendimento medio e mediano

- **Media**: somma tutti i rendimenti e divide per il numero di finestre. Puo' essere influenzata da valori estremi (un singolo guadagno enorme alza la media).
- **Mediana**: il valore "centrale" se metti tutti i rendimenti in ordine. Piu' rappresentativa del caso tipico.

Se media e mediana sono simili, i risultati sono distribuiti in modo uniforme. Se la media e' molto piu' alta della mediana, ci sono pochi casi di guadagno molto alto che alzano la media.

### Deviazione standard

Misura quanto i rendimenti variano rispetto alla media. In parole semplici:
- **Deviazione standard bassa**: i rendimenti sono abbastanza simili tra loro (risultati prevedibili)
- **Deviazione standard alta**: i rendimenti variano molto (risultati imprevedibili)

Esempio: due investimenti con rendimento medio +3%:
- Investimento A: deviazione standard 1% (i rendimenti vanno tipicamente da +2% a +4%)
- Investimento B: deviazione standard 5% (i rendimenti vanno tipicamente da -2% a +8%)

L'investimento A e' piu' "tranquillo", il B e' piu' rischioso anche se in media rendono uguale.

### Sharpe Ratio

Lo **Sharpe Ratio** combina rendimento e rischio in un unico numero. Risponde alla domanda: "Quanto rendimento ottengo per ogni unita' di rischio che mi assumo?"

Formula semplificata: Sharpe = (rendimento - rendimento senza rischio) / deviazione standard

Interpretazione pratica:
- **Sharpe < 0**: rendimento negativo, stai perdendo soldi
- **Sharpe tra 0 e 1**: rendimento positivo ma modesto rispetto al rischio
- **Sharpe tra 1 e 2**: buon rapporto rendimento/rischio
- **Sharpe > 2**: ottimo rapporto rendimento/rischio

**Attenzione ai valori molto alti** (es. Sharpe > 5): di solito indicano pochi campioni o un periodo particolarmente favorevole, non un investimento miracoloso.

Il **risk-free rate** (tasso privo di rischio) e' il rendimento di un investimento considerato sicuro (es. titoli di stato a breve termine). Se lo imposti a 0, il tool confronta i rendimenti rispetto a "non fare nulla".

### Finestra ottimale

E' la dimensione di finestra con la **percentuale piu' alta di finestre positive**. Se due dimensioni hanno la stessa percentuale, il tool preferisce quella con Sharpe Ratio piu' alto (miglior rapporto rendimento/rischio).

### Best/Worst case

Il **miglior caso** e il **peggior caso** mostrano gli estremi: il massimo guadagno e la massima perdita osservati in una singola finestra, con le relative date. Servono a capire quanto si poteva guadagnare o perdere nello scenario piu' favorevole e piu' sfavorevole.

---

## 5. Come configurare il tool

### Parametri essenziali

| Parametro | Cosa significa | Esempio |
|-----------|---------------|---------|
| `ticker_1`, `ticker_2` | I due strumenti da confrontare | `"SPY"`, `"QQQ"` |
| `data_inizio`, `data_fine` | Periodo storico da analizzare | `"2020-01-01"`, `"2025-01-01"` |
| `capitale_iniziale` | Quanto investi in ogni simulazione | `5000.0` |
| `min_giorni_finestra` | Finestra piu' corta da testare | `5` |
| `max_giorni_finestra` | Finestra piu' lunga da testare | `90` |
| `step_giorni` | Ogni quanti giorni testare | `5` (testa 5, 10, 15, ..., 90) |
| `sovrapposte` | Finestre rolling o a blocchi | `true` (consigliato) |

### Parametri opzionali

| Parametro | Cosa significa | Default |
|-----------|---------------|---------|
| `benchmark_ticker` | Terzo strumento per confronto | `null` (nessuno) |
| `commissione_fissa` | Costo fisso per acquisto in EUR | `0.0` |
| `commissione_percentuale` | Costo percentuale per acquisto | `0.0` |
| `tassa_capital_gain` | Aliquota tasse sui guadagni | `26.0` (Italia) |
| `soglia_positiva` | Rendimento minimo per "positivo" | `0.0` |
| `risk_free_rate` | Tasso annuo privo di rischio | `0.0` |

### Consigli per la configurazione

**Periodo di analisi**: piu' lungo e', meglio e'. Con meno di 1 anno di dati i risultati sono poco affidabili. Ideale: 3-5 anni.

**Step giorni**: con step 5 testi molte dimensioni (5, 10, 15, ...). Con step piu' grande (es. 10 o 30) l'analisi e' piu' veloce ma meno dettagliata.

**Soglia positiva**: se la imposti a 0.5, il tool considera "positiva" una finestra solo se il rendimento netto supera lo 0.5%. Utile se vuoi escludere guadagni minimi che nella pratica verrebbero mangiati da costi non modellati.

**Benchmark**: utile per confrontare i due ticker rispetto a un riferimento. Esempio: se confronti due ETF settoriali, puoi usare `^GSPC` (S&P 500) come benchmark per vedere se fanno meglio o peggio del mercato generale. Non usare come benchmark lo stesso indice che un ticker gia' replica (es. SPY con ^GSPC) perche' le curve sarebbero quasi identiche.

---

## 6. Come leggere i risultati

### Il file summary.txt

Mostra un riepilogo per ogni ticker con la finestra ottimale e le statistiche principali. Esempio:

```
--- TICKER: SPY ---
Finestra ottimale: 15 giorni (100.0% finestre positive, Sharpe 11.84)
Rendimento medio finestra ottimale (15gg): +1.9%
```

Questo significa: nel periodo analizzato, comprando SPY e vendendo dopo 15 giorni di trading, tutte le volte (100%) avresti chiuso in positivo, con un guadagno medio dell'1.9%.

### I file CSV

Contengono una riga per ogni dimensione di finestra testata, con tutte le statistiche. Puoi aprirli con Excel o LibreOffice Calc per analizzarli in dettaglio o creare grafici personalizzati.

### Il grafico (comparison_chart.png)

- **Linee continue** (con cerchi, triangoli, rombi): mostrano la percentuale di finestre positive per ogni dimensione. Piu' sono in alto, meglio e'.
- **Linee tratteggiate** (con quadrati, croci): mostrano lo Sharpe Ratio. Piu' sono in alto, migliore e' il rapporto rendimento/rischio.
- **Asse X**: dimensione della finestra in giorni di trading.
- **Asse Y sinistro**: percentuale finestre positive (0-100%).
- **Asse Y destro**: Sharpe Ratio.

Se due linee continue si sovrappongono, significa che quei due strumenti hanno performance molto simili (come succede con SPY e ^GSPC, che rappresentano lo stesso indice).

---

## 7. Limiti da tenere a mente

- **Il passato non predice il futuro**: un'alta percentuale di finestre positive nel passato non garantisce risultati futuri.
- **Campioni piccoli**: con periodi brevi o finestre grandi si generano pochi campioni. Risultati con meno di 30 campioni vanno presi con cautela.
- **Valute diverse**: confrontare ticker in valute diverse (es. EUR vs USD) senza conversione puo' distorcere il confronto.
- **Commissioni semplificate**: il tool modella solo le commissioni di acquisto, non quelle di vendita. I costi reali potrebbero essere leggermente superiori.
- **Finestre sovrapposte**: generano molti campioni ma non sono indipendenti (la finestra "giorno 1-10" e "giorno 2-11" condividono 9 giorni su 10). Questo puo' rendere le statistiche piu' "lisce" di quanto siano nella realta'.
