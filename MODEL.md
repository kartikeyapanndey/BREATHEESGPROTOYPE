# Data Model

The data model is built around multi-tenancy, traceability (source of truth tracking), and normalization, as these are critical for an enterprise ESG data platform preparing for audit.

## Core Models

### 1. `Tenant`
Represents the client company onboarding onto the Breathe ESG platform.
*   `id` (UUID): Primary Key
*   `name` (String): Company name
*   `created_at` (Datetime)

### 2. `DataSource`
Represents a specific ingestion event. This tracks *how* and *when* data arrived.
*   `id` (UUID): Primary Key
*   `tenant_id` (ForeignKey): Links to Tenant
*   `source_type` (Enum): `SAP_FLAT_FILE`, `UTILITY_CSV`, `CONCUR_JSON`
*   `upload_date` (Datetime): When it was ingested
*   `status` (Enum): `PROCESSING`, `COMPLETED`, `FAILED`
*   `file_name` (String): Original file name or API payload reference

### 3. `EmissionRecord`
This is the core normalized table. Every row from every source type maps to a row here.
*   `id` (UUID): Primary Key
*   `tenant_id` (ForeignKey): Multi-tenancy isolation at the row level.
*   `source_id` (ForeignKey): Links to the `DataSource` for traceability.
*   `category` (Enum): `SCOPE_1`, `SCOPE_2`, `SCOPE_3`
*   `original_payload` (JSONB): The exact raw data row before any normalization. **Why?** If the auditor asks "where did this number come from?", we can prove exactly what was passed to us, without needing to dig into old files.
*   `start_date` (Date): For point-in-time transactions, this is the transaction date. For utility bills spanning periods, this is the start of the billing period.
*   `end_date` (Date, Optional): Used for utility bills spanning periods.
*   `quantity` (Decimal): The normalized amount.
*   `unit` (String): Normalized unit (e.g., `L` for liters, `kWh` for electricity, `km` for distance).
*   `status` (Enum): `PENDING_REVIEW`, `APPROVED`, `REJECTED`. All records start as `PENDING_REVIEW` to allow the analyst to approve them.
*   `validation_errors` (JSONB): An array of strings describing what looks suspicious (e.g., `["Plant code 9999 not found", "Unit GAL not standard"]`).
*   `audit_trail` (JSONB): Tracks who edited what and when. Example: `[{"action": "updated", "field": "quantity", "old": "100", "new": "1000", "user": "analyst@breathe.com", "timestamp": "..."}]`

## Handling Specific Source Nuances

### SAP Fuel & Procurement
*   Maps to `SCOPE_1`.
*   SAP date formats (e.g., `DD.MM.YYYY`) are parsed into standard SQL dates.
*   German headers (like `BUDAT` for Posting Date, `MENGE` for Quantity) are mapped during the parser phase.
*   Missing Plant lookups trigger a validation error in the `validation_errors` array.

### Utility Electricity (CSV)
*   Maps to `SCOPE_2`.
*   Billing periods (e.g., Jan 15 - Feb 14) are handled by storing both `start_date` and `end_date`.
*   If tariff structures are present but we only care about usage, the extra columns are kept in `original_payload` for audit, but ignored in normalization.

### Corporate Travel (Concur API JSON)
*   Maps to `SCOPE_3`.
*   If distances are missing (e.g., only `SFO -> JFK` is provided), the parser flags this in `validation_errors` as `["Distance missing, estimation required"]`.

## Why this model?
A single unified `EmissionRecord` table is used rather than separate tables for `FuelRecord`, `ElectricityRecord`, etc. This allows the analyst review dashboard to be generic and unified. They can review 100 SAP rows and 50 Utility rows in the same view. The `original_payload` JSON field ensures we never lose the schema-specific data from the source, satisfying audit requirements without bloating our normalized schema.
