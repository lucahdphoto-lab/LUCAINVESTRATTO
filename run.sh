#!/usr/bin/env bash
# ==============================================================================
# LUCAINVESTRATTO - Launch Script
# ==============================================================================
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

echo "============================================================"
echo " 🏛️  Avvio LUCAINVESTRATTO (FactSet & Investing.com Suite)"
echo "============================================================"

# Check Python command
if command -v python3 &>/dev/null; then
    PY_CMD="python3"
elif command -v python &>/dev/null; then
    PY_CMD="python"
else
    echo "Errore: Python non trovato nel sistema."
    exit 1
fi

echo "Verifica dipendenze..."
$PY_CMD -c "import streamlit, pandas, numpy, scipy, plotly, reportlab, openpyxl, PIL" 2>/dev/null || {
    echo "Installazione dipendenze richieste..."
    $PY_CMD -m pip install -r requirements.txt
}

echo "Avvio interfaccia grafica Streamlit..."
$PY_CMD -m streamlit run app.py --server.port 8501 --server.headless false
