# Enterprise RAG

Secure company document question answering with citations, ingestion, access control, and retrieval evaluation.

## Solution Overview

Internal documents are often scattered across PDFs, wikis, and shared folders. This project demonstrates a client-ready RAG system that answers questions with source citations while respecting access control.

## Local-First Build

Planned local components:

- FastAPI query API
- Qdrant or Chroma vector store
- Local document ingestion
- SQLite or Postgres metadata
- Streamlit or lightweight web UI
- RBAC-aware retrieval filters

## Azure Later

Requires Azure credentials only when deploying cloud mode:

- Azure AI Search
- Azure Blob Storage
- Azure OpenAI embeddings
- Entra ID
- Container Apps or AKS

## Demo Goal

Show the same question asked by different users and prove that retrieval results respect document permissions.
