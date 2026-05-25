# Tradeoffs

This document outlines three things deliberately *not* built for this prototype and why.

## 1. Automated Emission Factor Calculation

**What was not built:** The system normalizes the quantity and unit (e.g., `1000 kWh`) but does not automatically multiply it by an emission factor (e.g., `0.5 kgCO2e/kWh` for a specific grid region) to generate final carbon numbers.
**Why:** The assignment explicitly stated the "hard part isn't computing carbon, it's that every client's data lives somewhere different". The focus was correctly placed on ingestion, normalization, and review. Building a robust emission factor library (which requires complex regional and temporal lookups) would distract from the core requirement of solving the ingestion and validation UX.

## 2. Dynamic Column Mapping UI

**What was not built:** A user interface allowing the analyst to drag-and-drop or select which column in their uploaded CSV corresponds to "Quantity" or "Date".
**Why:** While essential for a mature product, building a robust mapping UI takes significant time. For this prototype, the backend parsers are hardcoded to expect specific (but realistic) column names based on the researched sources (e.g., SAP `MENGE` for quantity). This proves the normalization engine works without spending days on front-end mapping logic.

## 3. Real API Integrations & Webhooks

**What was not built:** We did not build a live OAuth2 connection to Concur or a webhook listener. Instead, we use file uploads of JSON payloads to simulate the API response.
**Why:** Dealing with third-party sandbox provisioning, OAuth flows, and network tunneling for a 4-day prototype is high-risk and low-reward. The core value of the prototype is how it *handles* the JSON payload (normalizing and flagging missing distances), not how the HTTP request was transported. File upload achieves the exact same data ingestion state reliably.
