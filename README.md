# Measurement-aware Environmental AI for TMS

> **Submission to 2026 AX Idea Competition (Korea Climate-Energy-Environment Ministry × KOWEPO)**
> Track: Designated Analysis — Korea Western Power (한국서부발전)
> Author: Kim Yong-Beom, Ph.D. (Measurement Science · ISO 18516 contributor)

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Streamlit](https://img.shields.io/badge/Streamlit-Demo-FF4B4B.svg)](#live-demo)

## What's New (and Different)

Most environmental AI takes raw sensor data and feeds it to ML.
**This system treats sensor uncertainty as a first-class citizen** —
the GUM (ISO/IEC Guide 98-3) combined standard uncertainty propagates
into model loss, anomaly detection, operator alarms, and trade-cost
estimation alike.

### Three Innovations (none of which other contestants will do)

1. **Measurement-aware ML (Innovation A)** — GUM-weighted PyTorch loss.
   Sensor reading with smaller uncertainty contributes more to learning.
   Heteroscedastic Gaussian NLL + Monte Carlo uncertainty propagation.

2. **Cross-Source Calibration Drift Detection (Innovation B)** —
   TMS readings are continuously cross-checked against nearby AirKorea
   stations. Distance, elevation, and wind dilution are baked in.
   Page-Hinkley test triggers calibration **before** the legal 90-day
   cycle expires.

3. **Operator Trust Calibration (Innovation F)** — A 0–100
   trust score combining measurement quality, model confidence, XAI
   consistency, and historical accuracy. Drives P1/P2/P3 alarm tiers.

Plus an Extension D simulator for **EU CBAM (Carbon Border Adjustment
Mechanism, in force from 2026-01-01)** showing how 1%p improvement in
measurement accuracy translates to ~₩100B+ annual savings per unit.

## Quick Start

```bash
git clone https://github.com/kyb8801/ax2026-tms-seobu.git
cd ax2026-tms-seobu
pip install -r requirements.txt

# Self-tests for each module
python src/innovation/gum_uncertainty.py
python src/innovation/measurement_aware_loss.py
python src/innovation/calibration_drift.py
python src/innovation/operator_trust.py

# End-to-end integration test
python tests/test_e2e_pipeline.py

# Live Streamlit demo
streamlit run streamlit_app.py
```

## Live Demo

(Will be deployed at `https://kyb8801-ax2026-tms-seobu.streamlit.app` after data ingestion.)

## Architecture

```
4-source data → ETL → Core ML (LSTM-AE + IForest) → Innovation Layer → Operator
   ↓             ↓        ↓                            ↓
TMS           ETL      GUM-weighted loss        OTS 0-100
AirKorea     fusion    Cross-source drift       P1/P2/P3 alarm
KMA          quality   Operator Trust           CBAM cost
KPX          report                              accounting
```

## Why This Matters

For Korean power producers facing both domestic environmental regulation
**and** the EU CBAM trade barrier, measurement accuracy is no longer just
a compliance issue — it's a billion-won line item. This repository turns
ISO 17025-grade measurement science into operational AI.

## License

MIT (code only). TMS data is subject to KOWEPO and Climate-Energy-Environment
Ministry's competition data usage agreement.

## Citation

If this work helps your research, please cite:

```bibtex
@misc{kim2026measurementaware,
  author       = {Kim, Yong-Beom},
  title        = {Measurement-aware Environmental AI for TMS:
                  GUM-Weighted ML and Cross-Source Calibration Drift Detection},
  year         = {2026},
  howpublished = {2026 AX Idea Competition, Korea Climate-Energy-Environment Ministry},
}
```

Related standards:
- ISO/IEC Guide 98-3 (GUM)
- ISO/IEC 17025:2017
- ISO 17034:2016
- **ISO 18516:2019** (1st-author contribution by Kim, Y.-B.)
