# Document Intelligence Workbench

Structured extraction from invoices, contracts, forms, statements, and scanned documents with human review.

## Solution Overview

Manual document processing is common in back-office teams. This project demonstrates a practical system that extracts data, flags low-confidence fields, validates outputs, and exports clean structured data.

## Local-First Build

Planned local components:

- FastAPI backend
- Streamlit or React review UI
- Local file storage
- SQLite or DuckDB metadata
- PDF and docx parsing
- OCR placeholder or local OCR option
- LLM structured extraction
- CSV and JSON export

## Azure Later

Requires Azure credentials only when deploying cloud mode:

- Azure AI Document Intelligence
- Azure Blob Storage
- Azure Cosmos DB or PostgreSQL
- Azure Container Apps
- Key Vault
- Application Insights

## Demo Goal

Upload invoices and contracts, extract fields with confidence scores, review low-confidence values, validate totals or clauses, and export CSV/JSON.
