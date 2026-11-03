# Source register and verification notes

Sources below were checked on **4 November 2026**. No government raw district extract is included in this repository.

## Primary data sources

1. **MGNREGA Public Data Portal (Ministry of Rural Development / NIC)**: [dynamic report](https://mnregaweb4.nic.in/netnrega/dynamic2/dynamicreport_new4.aspx). The public page is accessible. Its interface lists worker participation, job cards, demand for work, employment provided, SC/ST households above 100 days, person-day bands, monthly demand/work, expenditure and work details. The visible geographic levels are State, District, Block and GP. The visible FY selector spans 2022–23, 2023–24, 2024–25, 2025–26 and 2026–27. The page includes “View data” and “Download data.” During this project, an attempt to run the report and use the download control did not yield district rows or a local export file. The actual export format, exact downloadable column schema, refresh schedule and revision policy therefore remain **unverified**. Do not assume that the button produces CSV or Excel.

2. **Open Government Data Platform India (data.gov.in)**: searching the supplied portal route returned 404. A Government resource record identified by secondary catalog references as “District-wise MGNREGA Data at a Glance” (`ee03643a-ee4c-48c2-ac30-9f2ff26ab722`) was checked at its official resource URL: [record page](https://www.data.gov.in/resource/ee03643a-ee4c-48c2-ac30-9f2ff26ab722). The official page returned **“Record not found”** on the check date. No date coverage, resource fields, download format or functioning API endpoint could be verified. This project does not rely on the third-party catalog references as data.

3. **Department of Rural Development, State Performance Report 2024–25**: [official PDF](https://www.dord.gov.in/static/uploads/2025/09/d81193f25cde78b36f36b559ffabbb18.pdf). This report provides national FY 2024–25 summary values and a state table for the percentage of working households completing 100 days. It is not a downloadable district-year panel. Summary metric labels are preserved as printed, including “Persondays of Central Liability so far.” The excerpt reviewed does not specify a precise snapshot date for every summary value; treat them as official report figures, not an immutable final extract.

4. **Ministry of Rural Development, MGNREGA dashboard**: [national dashboard](https://dashboard.dord.gov.in/dashboardnew/mgnrega.aspx). It provides physical, financial and programme-specific indicators with FY and state selectors, but the live page reviewed displayed FY 2026–27. Those current-period values are not used as annual MGNREGA findings in this project.

## Definitions and legal time boundary

5. **FAQs MGNREGA, Ministry of Rural Development**: [official PDF](https://nregaplus.nic.in/Circular_Archive/archive/nrega_doc_FAQs.pdf). It describes the mandate as at least 100 days of guaranteed wage employment in a financial year for each rural household whose adult members volunteer for unskilled manual work, and states that the scheme is demand-driven.

6. **PIB FAQ: Viksit Bharat–G RAM G Act, 2025**: [official FAQ](https://www.pib.gov.in/FaqDetails.aspx?ModuleId=4&NoteId=158511&lang=1&reg=3). Published 11 May 2026. It says the successor Act came into force nationwide on 1 July 2026 and Mahatma Gandhi NREGA stood repealed from that date; the successor Act provides 125 days. FY 2026–27 therefore straddles two statutory regimes. This dashboard flags that year and the report does not treat it as a continuous MGNREGA annual observation.

## Formats, coverage and reproducibility

- **Verified availability**: public HTML pages and report PDF; the MGNREGA portal visibly advertises a download action.
- **Not verified**: a successful portal-generated district file, the file’s format, dataset-specific historical coverage behind the report, full field definitions for each download, machine-readable OGD resource/API access, and a source refresh/revision timestamp.
- The pipeline supports local CSV and Excel files, but this describes the **software importer**, not a claim about the government portal’s export format. The input must first be mapped to the canonical fields in `DATA_DICTIONARY.md` and the original source file’s title, URL, period, access date, unit and exact metric labels recorded in the accompanying metadata.
- The synthetic CSV under `tests/fixtures/` is fabricated solely to exercise software; it is not an official or representative MGNREGA dataset.
