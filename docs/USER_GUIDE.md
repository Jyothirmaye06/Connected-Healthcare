# Connected Healthcare — User Guide

> **Medical Disclaimer:** This application is an operational decision-support tool for hospital resource planning. It does **not** provide medical advice, diagnose illnesses, or replace consultation with a qualified doctor. In an emergency call 108 immediately.

---

## What Is Connected Healthcare?

Connected Healthcare is a free, easy-to-use website that helps you answer two simple questions before visiting a hospital:

* **"How crowded is the hospital right now?"**
* **"How long will I likely wait?"**

You can also see disease trends in your area and compare nearby hospitals at a glance.

---

## How to Open the App

1. Make sure the computer running the app is switched on.
2. Open any web browser (Chrome, Edge, Firefox).
3. Go to the address shown by the app administrator (e.g. `http://localhost:8501`).
4. The **Public Dashboard** opens automatically — no login required.

---

## Choosing Your Language

In the **left sidebar** (the panel on the left side of the screen) you will see a **Language / భాష / भाषा** selector.

| Option | Language |
|--------|----------|
| 🇬🇧 English | English |
| 🇮🇳 తెలుగు | Telugu |
| 🇮🇳 हिन्दी | Hindi |

Click the language you prefer. All labels, cards, alerts, and disclaimers will switch instantly. Your selected hospital and date range are **not** reset when you change language.

---

## Selecting a Hospital

In the sidebar, find the **Hospital / ఆసుపత్రి / अस्पताल** drop-down menu. Click it and choose the hospital you want to check. The dashboard will update within a few seconds.

---

## Reading the Situation Summary

At the top of the dashboard you will see a short paragraph in plain language, for example:

> *"Apollo Hospital is moderately busy. The estimated waiting time is around 22 minutes. The crowd level is normal for this time of day."*

This single sentence tells you the most important information at a glance.

---

## Key Dashboard Metrics

The dashboard distinguishes the latest stored observations from model forecasts:

| Card | What It Means |
|------|--------------|
| **Current Crowd** | Approximate number of patients currently waiting |
| **Expected Crowd (next observation)** | Model estimate for the next observation |
| **Current Wait** | Estimated minutes you may wait before being attended to |
| **Expected Wait (next observation)** | Model estimate of waiting time for the next observation |
| **Emergency Cases** | Number of high-priority patients currently being handled |
| **Arrivals / Discharges** | Counts recorded for the latest observation period |

Forecasts are estimates from saved machine-learning models, not guaranteed outcomes or clinical advice.

### Understanding the Colours

Every card and badge also carries a **text label** so colour is never the only indicator:

| Text Label | Meaning |
|-----------|---------|
| 🟢 Normal / Low | The hospital is running smoothly |
| 🟡 Moderate / Busy | Slightly busy; expect a short wait |
| 🔴 High / Critical | Very busy; consider alternatives if not urgent |

---

## Hospital Comparison Cards

Further down the page you will see compact cards for hospitals in the selected location. Use these to compare the latest stored observations and forecasts.

Each comparison card shows hospital name, current crowd and waiting time, predicted crowd and waiting time, and a rule/anomaly-based status. These are not live hospital feeds.

---

## Crowd and Wait Trend Charts

The combined line chart shows crowd and waiting-time observations for your selected hospital. Use it to explore recorded patterns:

* Crowd usually peaks in the **morning (9 AM – 12 PM)** and dips in the **afternoon**.
* Waiting time may spike on **weekends** and public holidays.

**Tip:** Hover your mouse over the chart line to see the exact values for any hour.

---

## Public Health / Disease Trends

Scroll down to see a chart showing reported health conditions in your area over time. This section helps communities notice if certain illnesses are increasing. 

> Health-condition values in this project are synthetic demonstration data, not anonymised reports from connected health providers. No patient-level information is displayed.

---

## Status Alerts

If the system detects anything unusual (e.g., a sudden spike in crowd at an odd hour) it will show a coloured **Alert** banner with a plain-language explanation such as:

> *"⚠️ Unusual Activity Detected — Crowd at Apollo Hospital is significantly higher than the normal pattern for Saturday evening. Possible cause: local event or emergency."*

Alerts are for awareness only. They do not mean the hospital is unsafe.

---

## Switching the Date Range

Use the **Date Range** selector in the sidebar to view historical data for a custom period. This affects the trend charts only — the current KPI cards always show the latest values.

---

## Frequently Asked Questions

**Q: Is this information live?**  
A: No. The project does not connect to live hospital systems. The dashboard shows synthetic demonstration observations stored in its SQLite database. A developer can explicitly start scheduled simulation from the Developer/Admin view; it stops when stopped or when that Streamlit session ends.

**Q: Can I rely on the predicted crowd or waiting time?**  
A: Treat both as estimates for demonstration only. The models were trained on synthetic project data; displayed historical evaluation figures are not recalculated on each dashboard load and are not a guarantee of performance on real hospital data.

**Q: What if a hospital is not listed?**  
A: Only hospitals connected to this system appear in the list. Contact your local health authority to request integration.

**Q: I see the word "Synthetic". What does that mean?**  
A: Observations and health-condition data are computer-generated for demonstration. The current database schema does not retain source/provenance for each individual observation, so the project should be treated as synthetic throughout.

**Q: Who do I contact if the app is wrong?**  
A: Please inform the hospital desk administrator or the project contact listed by your institution.

---

## Tips for Best Results

1. Check the app **30–60 minutes before** you plan to visit to catch any building crowd.
2. If the predicted wait for your preferred hospital is high, look at the **comparison cards** to find a less busy alternative.
3. During public holidays the crowd patterns may differ from predictions — always call the hospital to confirm.
4. This app works best on a computer or tablet; mobile browsers are supported but the charts are smaller.

---

*Version 1.0 — Connected Healthcare Project, B.Tech AI/ML Final Year, 2026*
