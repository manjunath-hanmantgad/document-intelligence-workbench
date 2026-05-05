# AI Analytics Copilot

Text-to-SQL analytics assistant that generates safe SQL, charts, and plain-English business insights.

## Solution Overview

Business teams repeatedly ask analysts for the same reports. This project demonstrates a self-serve analytics assistant with SQL safety controls and visual output.

## Local-First Build

Planned local components:

- SQLite or Postgres demo database
- Schema inspector
- LLM SQL generator
- SQL validator and safety layer
- Query executor
- Plotly charts
- Streamlit UI

## Azure Later

Requires Azure credentials only when deploying cloud mode:

- Azure PostgreSQL
- Azure Cache for Redis
- Azure OpenAI
- Application Insights
- Container Apps

## Demo Goal

Ask a sales or finance question, generate safe SQL, render a chart, and show a blocked unsafe query.
