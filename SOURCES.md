# Sources Researched

This document details the research conducted on the three real-world data sources, what was learned, how the sample data is structured based on that reality, and what might break in production.

## 1. SAP Fuel and Procurement Data

**Format Researched:** SAP ALV Grid Flat File Export (TSV/CSV) & Standard IDocs (MBGMCR)
*   **What I learned:** While IDocs (like MBGMCR for goods receipts) are standard for system-to-system integration, they are heavily nested and rarely handled directly by a sustainability analyst. A far more common pattern for *ad-hoc analysis* is the analyst running a custom ABAP report or a standard material document list (Transaction MB51) and exporting the ALV grid to a local spreadsheet or text file.
*   **Sample Data Shape:** The sample data uses a CSV structure mimicking a raw SAP export. It includes German technical headers: `BUDAT` (Posting Date), `WERKS` (Plant code), `MATNR` (Material Number), `MAKTX` (Material Description), `MENGE` (Quantity), `MEINS` (Base Unit of Measure).
*   **Why it looks like this:** SAP exports notoriously preserve technical field names if the user doesn't specifically choose a user-friendly layout. The date format `DD.MM.YYYY` is very common in European SAP configurations.
*   **What would break in real deployment:** 
    *   Encoding issues (e.g., UTF-16 LE from SAP GUI exports breaking standard CSV parsers).
    *   Plant codes (`WERKS`) that don't exist in our Tenant's lookup table, requiring a complex master data sync before transactional data can be processed.

## 2. Utility Data (Electricity)

**Format Researched:** Utility Web Portal CSV Exports
*   **What I learned:** Unlike banking, utility data has no universal API standard (Green Button is not universally adopted). Facilities managers typically download CSVs from portals. These CSVs often contain billing cycles that do not align with calendar months (e.g., mid-month to mid-month) and mix consumption data with financial data.
*   **Sample Data Shape:** The sample data includes `Account Number`, `Service Address`, `Billing Period Start`, `Billing Period End`, `Total Usage (kWh)`, and `Total Charges ($)`.
*   **Why it looks like this:** It reflects a typical summary billing view rather than 15-minute interval smart meter data, which is often a separate, much larger export.
*   **What would break in real deployment:** 
    *   Missing dates: Utilities sometimes just say "January Bill" instead of explicit start/end dates.
    *   Unit inconsistencies: Some portals export in MWh or Therms, requiring dynamic conversion logic.

## 3. Corporate Travel (Flights, Hotels)

**Format Researched:** Concur Travel Itinerary API
*   **What I learned:** The Concur Itinerary API returns deep JSON structures containing trips, which contain bookings, which contain segments (Air, Hotel, Car). A key nuance is that for flights, it often provides the origin and destination airport codes (e.g., SFO, LHR) but *not* the actual flight distance.
*   **Sample Data Shape:** The sample data is a JSON payload mimicking the `Segments` array of a Concur Trip. It includes `SegmentType` (`Air` or `Hotel`), vendors, and for flights, `DepartureCode` and `ArrivalCode`.
*   **Why it looks like this:** It mimics the hierarchical JSON nature of modern REST APIs, contrasting with the flat files of SAP and Utilities.
*   **What would break in real deployment:**
    *   Missing distance calculations: We would need to implement or license an airport-to-airport distance calculator (like the Great Circle distance) to compute emissions, as the API often omits this.
    *   Pagination and rate limits on the real API when pulling historical data for thousands of employees.
