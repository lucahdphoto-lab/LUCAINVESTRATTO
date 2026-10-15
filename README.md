# 🏛️ LUCAINVESTRATTO
**Piattaforma Professionale di Gestione Multi-Conto Bancario, Analisi Estratto Conto & Metriche d'Investimento Istituzionali (FactSet & Investing.com Standard)**

---

## 📌 Panoramica del Progetto

**LUCAINVESTRATTO** è una suite finanziaria completa creata da zero per offrire funzionalità avanzate di aggregazione multi-bancaria, parsing di estratti conto e snapshot visivi, calcolo quantitativo del rischio/rendimento su standard istituzionali (come **FactSet**, **Bloomberg Terminal** e **Investing.com**) e generazione automatica di reportistica nei formati richiesti: **.PDF**, **.XLSX** e **.TXT**.

---

## ✨ Funzionalità Chiave

### 1. 🏦 Gestione Multi-Conto Bancario
- **Aggregazione centralizzata**: Gestione contemporanea di più istituti bancari e broker (es. *FinecoBank*, *Intesa Sanpaolo*, *Degiro*, *Banca Mediolanum*, *Interactive Brokers*, ecc.).
- **Filtro di visualizzazione dinamico**: Possibilità di analizzare **"Tutti i conti (Consolidato)"** o passare con un clic al singolo conto.
- **Tipologie di conto**: Supporto per Conti Correnti, Conti Deposito remunerati, Dossier Titoli / Brokerage e Criptovalute.
- **Monitoraggio patrimonio netto**: Calcolo automatico e istantaneo della liquidità disponibile, del capitale investito e del patrimonio netto complessivo.

### 2. 📥 Importazione Universale Multi-Formato
- **`.xlsx` / `.xls`**: Lettura intelligente di fogli Excel con riconoscimento automatico delle colonne (data, importo, descrizione, ticker, quantità, PMC).
- **`.csv`**: Riconoscimento automatico del separatore (`;`, `,`, tabulazione) e conversione dei formati numerici europei (`1.234,56 €`) e anglosassoni.
- **`.txt`**: Riconoscimento tramite pattern regex avanzati di estratti conto testuali bancari e log transazioni.
- **`.png` / `.jpg`**: Analisi visiva di screenshot bancari e ricevute tramite **Gemini Vision AI Multimodale** e OCR locale fallback, con anteprima e importazione diretta nel database.
- **Inserimento manuale rapido**: Moduli interattivi per aggiungere singole transazioni o posizioni di portafoglio.

### 3. 📅 Maschera di Analisi Estratto Conto per Data
- **Filtri temporali flessibili**: Preset rapidi (*YTD*, *Ultimo Mese*, *Ultimi 3 Mesi*, *Ultimi 6 Mesi*, *Ultimo Anno*, *Tutto lo Storico*, *Range Personalizzato*).
- **KPI di cassa**: Saldo Iniziale, Totale Accrediti/Entrate, Totale Addebiti/Uscite, Flusso Netto di Cassa (Cashflow) e Tasso di Risparmio medio (*Savings Rate %*).
- **Grafico Evoluzione Saldo nel Tempo**: Curva ad area interattiva Plotly del saldo progressivo giornaliero.
- **Grafico Flussi Mensili**: Istogramma comparativo entrate vs uscite e flusso netto mensile.
- **Scomposizione Spese per Categoria**: Grafico a ciambella interattivo e dettaglio delle principali fonti di reddito.
- **Registro movimenti**: Tabella filtrabile per parola chiave o causale.

### 4. 💼 Maschera di Analisi per Asset & Asset Class
- **Asset Allocation Multi-Dimensionale**:
  - Per **Classe di Strumento** (*Azionario*, *Obbligazionario*, *ETF/Fondi*, *Liquidità/Monetario*, *Materie Prime/Oro*, *Crypto*, *Alternativi*).
  - Per **Area Geografica** (*Globale*, *Stati Uniti*, *Europa*, *Italia*, *Emergenti*).
  - Per **Settore Economico** e **Valuta**.
- **Analisi Prezzo Medio di Carico (PMC)**: Confronto tra capitale investito originario e controvalore attuale di mercato.
- **Plus/Minusvalenze Latenti (P&L)**: Calcolo in euro e in percentuale con evidenziazione dei *Top Gainers* e *Top Losers*.
- **Cash Flow Cedolare e Dividendi**: Stima dei dividendi e delle cedole annuali attese e calcolo del Dividend Yield medio del portafoglio.

### 5. 📈 Analisi Investimento Avanzata (Standard FactSet & Investing.com)
Implementazione rigorosa di tutti gli indicatori quantitativi utilizzati dai software finanziari istituzionali:
- **Rendimento**: Rendimento Cumulativo e Rendimento Composto Annualizzato (**CAGR**).
- **Indice di Sharpe** ($\frac{R_p - R_f}{\sigma_p}$): Misura dell'extra-rendimento generato per unità di rischio totale.
- **Indice di Sortino** ($\frac{R_p - R_f}{\text{Downside Deviation}}$): Penalizzazione esclusiva della volatilità negativa (downside risk).
- **Indice di Calmar** ($\frac{\text{CAGR}}{|\text{Max Drawdown}|}$): Efficienza rispetto al massimo ribasso storico.
- **Indice di Treynor**: Efficienza rispetto al rischio sistematico (Beta).
- **Massimo Drawdown (MDD %)**: Picco-valle massimo e **Curva Underwater (Drawdown Chart)** interattiva.
- **Value at Risk (VaR)**:
  - **VaR 95% e 99% Storico** (orizzonte 1 giorno e 1 anno).
  - **VaR 95% Parametrico** e controvalore monetario massimo di perdita in euro.
  - **Conditional VaR (CVaR / Expected Shortfall 95%)**: Perdita media attesa nel 5% degli scenari peggiori.
- **Confronto con Benchmark Istituzionali**:
  - Benchmark selezionabili: *MSCI World*, *S&P 500*, *FTSE MIB*, *Bloomberg Euro-Aggregate Bond*, *EUR Cash (€STR)*.
  - **Beta ($\beta$)**: Sensibilità alle oscillazioni del mercato.
  - **Alfa di Jensen ($\alpha$)**: Extra-rendimento generato rispetto al modello CAPM.
  - **Tracking Error & Information Ratio**: Consistenza e qualità rispetto all'indice di mercato.
  - **Correlazione ($r$)** e **Coefficiente di Determinazione ($R^2$)**.

### 6. 📑 Esportazione Report (.pdf, .xlsx, .txt)
- **📄 Report PDF (`.pdf`)**: Layout istituzionale in formato A4 (stile *Private Wealth / FactSet Executive Summary*) con tabelle formattate, KPI patrimoniali, ripartizione asset allocation, top posizioni e avvertenze legali.
- **📊 Cartella Excel (`.xlsx`)**: File Excel professionale a 4 fogli (*Sintesi & Metriche Rischio*, *Asset Allocation*, *Posizioni Portafoglio*, *Estratto Conto Transazioni*) con formattazione celle, valuta e stili grafici corporate navy.
- **📑 Report Testo ASCII (`.txt`)**: Report monospaziato stile *Bloomberg Terminal* ideale per rapida consultazione, log e prompt AI.

---

### 7. ⚙️ Impostazioni, Colori, Alert & Allineamento Dati
- **🎨 Modifica e Scelta Colori**:
  - Selezione tra preset istituzionali (*FactSet Dark Navy*, *Bloomberg Amber & Black*, *Private Wealth Emerald*, *Cyber Violet*, *Classic Slate*).
  - Color pickers manuali per impostare colori primari e di accento personalizzati.
- **🔔 Notifiche & Alert Personalizzati**:
  - Regole e soglie configurabili per *Massimo Drawdown*, *Giacenza di Liquidità Minima*, *Sovra-allocazione / Concentrazione Singolo Titolo* e *Uscite / Spese Rilevanti*.
  - Centro notifiche attive in tempo reale con badge dinamico nell'intestazione.
- **🧹 Azzeramento Selettivo**:
  - Pulizia mirata di sole transazioni (con eventuale filtro per conto o per data).
  - Pulizia mirata delle sole posizioni di portafoglio.
  - Ripristino totale di fabbrica (*Factory Reset*) protetto da conferma esplicita.
- **🔄 Ricalcolo & Allineamento Dati**:
  - Rapporto diagnostico con verifica di integrità: record orfani, transazioni duplicate, sbilanciamenti nei giroconti.
  - Ricalcolo automatico e sincronizzazione di saldi progressivi, quote e controvalori.

---

## 🏗️ Architettura del Software

```
proud-bardeen/
├── app.py                         # Entry point dell'applicazione Streamlit
├── requirements.txt               # Dipendenze Python
├── run.sh                         # Script bash di avvio automatico
├── data/
│   ├── lucainvestratto.db         # Database SQLite persistente
│   └── settings.json              # Configurazione salvata di temi e notifiche
├── lucainvestratto/
│   ├── config.py                  # Costanti, valute, benchmark istituzionali
│   ├── db.py                      # Engine SQLite, repository CRUD e demo data loader
│   ├── models.py                  # Dataclass: BankAccount, Transaction, Holding, RiskMetrics
│   ├── settings.py                # Gestore preferenze utente, palette e soglie alert
│   ├── analytics/                 # Motori di calcolo quantitativo
│   │   ├── cashflow.py            # Analisi flussi, saldi giornalieri e categorie
│   │   ├── assets.py              # Asset allocation, pesi, PMC e P&L
│   │   ├── risk.py                # Sharpe, Sortino, VaR, MDD, Beta, Alpha, Underwater
│   │   ├── notifications.py       # Motore di valutazione alert in tempo reale
│   │   └── recalc.py              # Diagnostica integrità, allineamento saldi e deduplicazione
│   ├── parsers/                   # Parser multi-formato
│   │   ├── base.py                # Utility di pulizia valute e date
│   │   ├── csv_parser.py          # Parser CSV auto-delimiter
│   │   ├── excel_parser.py        # Parser fogli Excel (.xlsx, .xls)
│   │   ├── txt_parser.py          # Parser testi ed estratti conto .txt
│   │   └── image_parser.py        # Parser screenshot .png / .jpg (Gemini Vision AI / OCR)
│   ├── export/                    # Generatori di report
│   │   ├── pdf_report.py          # Generatore PDF ReportLab
│   │   ├── excel_report.py        # Generatore cartelle OpenPyXL
│   │   └── txt_report.py          # Generatore report ASCII
│   └── ui/                        # Interfaccia grafica Streamlit
│       ├── theme.py               # Tema scuro/chiaro FactSet, badge e card KPI dinamiche
│       └── views/                 # Maschere di analisi modulari
│           ├── accounts_view.py   # Gestione multi-conto
│           ├── import_view.py     # Importazione file e input manuale
│           ├── cashflow_view.py   # Estratto conto per data
│           ├── asset_view.py      # Analisi per asset
│           ├── investment_view.py # Analisi investimento FactSet
│           ├── export_view.py     # Download report .pdf, .xlsx, .txt
│           └── settings_view.py   # Impostazioni colori, alert, azzeramenti e ricalcolo
└── tests/
    └── test_parsers.py            # Suite di test unitari automatizzati
```

---

## 🚀 Come Avviare l'Applicazione

### Metodo 1: Script Diretto (Consigliato)
Apri il terminale nella cartella del progetto ed esegui:
```bash
./run.sh
```

### Metodo 2: Comando Streamlit
```bash
python3 -m streamlit run app.py
```

L'applicazione si aprirà automaticamente nel tuo browser predefinito all'indirizzo:
👉 `http://localhost:8501`

---

## 🧪 Esecuzione dei Test Automatizzati
Per eseguire l'intera suite di test e verificare il corretto funzionamento di tutti i parser e generatori di report:
```bash
python3 -m unittest discover -s tests
```
Tutti i test devono restituire `OK`.
