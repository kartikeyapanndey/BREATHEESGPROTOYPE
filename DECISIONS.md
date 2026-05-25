# Decisions

This document outlines the key ambiguities resolved and the subsets of data chosen for the prototype.

## Ambiguity 1: Scope of Data Handled

**Decision:** The prototype handles three specific narrow subsets of data instead of a generalized mapping engine for any file.
*   **Why:** A full dynamic mapping engine would take months. By picking realistic constraints (e.g., standard SAP column headers, standard utility billing structures), we can demonstrate a solid architecture and user experience within 4 days.
*   **What was ignored:** We ignore data beyond Scope 1 (Fuel), Scope 2 (Electricity), and Scope 3 (Business Travel - flights/hotels). We ignore complex utility tariff riders and demand charges, focusing strictly on total consumption.

## Ambiguity 2: Ingestion Mechanisms

**Decision:**
*   **SAP Data:** Upload a TSV/CSV. (Flat file export is chosen over IDocs due to the typical analyst workflow not having direct PI/PO integration access).
*   **Utility Data:** Upload a CSV. (Preferred over scraping PDFs, which is error-prone, or APIs, which are rarely available for smaller utilities).
*   **Concur Data:** Upload a JSON file. (We simulate an API pull by allowing the user to drop the JSON response of an Itinerary API call into the dashboard).
*   **Why:** It keeps the prototype self-contained while accurately reflecting how analysts often receive or dump data into a system.

## Ambiguity 3: Distance Calculation in Travel

**Decision:** For flights without distance data (only departure/arrival airport codes provided), we mock a simple estimation by flagging it in validation errors instead of building a full Haversine formula geospatial engine for the prototype.
*   **Why:** Demonstrates that the system recognizes the data gap (a crucial part of an analyst's review process) without over-engineering a side feature.

## Questions for the PM
1. **SAP:** Are our clients standardized on a specific unit of measure for fuel globally, or do we need a unit conversion engine running at ingestion time?
2. **Utilities:** Do we care about cost data for financial reconciliation, or just the consumption (kWh) for carbon accounting?
3. **Audit:** Does the auditor require the original raw file (e.g., the exact CSV bytes), or is the `original_payload` row-level JSON sufficient for "source-of-truth" tracking?
