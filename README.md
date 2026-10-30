# AI Circuit Explainer & Verification Studio

A local Flask application for theoretical calculations and verification-record management for eight basic electronic circuits.

## Run

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000.

If PowerShell blocks activation, run `.\.venv\Scripts\python.exe -m pip install -r requirements.txt` and `.\.venv\Scripts\python.exe app.py` instead.

## Features

- Calculators for RC low/high-pass filters, voltage divider, BJT amplifier, inverting op-amp, half-wave rectifier, LED resistor, and Zener regulator.
- Beginner and advanced explanations.
- Manual AI and simulator-result entry.
- Percentage-error calculation using |hand calculation − simulation| / |simulation| × 100.
- In-memory verification records downloadable as CSV.

Calculation results are theoretical. Record only actual LTspice or Falstad observations as simulation results.
