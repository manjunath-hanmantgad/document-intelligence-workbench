import os

# LLM
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "mock")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

# Azure placeholders
AZURE_OPENAI_ENDPOINT = os.environ.get("AZURE_OPENAI_ENDPOINT", "")
AZURE_OPENAI_KEY = os.environ.get("AZURE_OPENAI_KEY", "")
AZURE_OPENAI_CHAT_DEPLOYMENT = os.environ.get("AZURE_OPENAI_CHAT_DEPLOYMENT", "")
AZURE_OPENAI_EMBED_DEPLOYMENT = os.environ.get("AZURE_OPENAI_EMBED_DEPLOYMENT", "")

# Database
PROCUREAI_DB_PATH = os.environ.get("PROCUREAI_DB_PATH", "data/procureai.db")

# Policy
PROCUREAI_POLICY_PATH = os.environ.get("PROCUREAI_POLICY_PATH", "data/procurement_policy.md")

# Approval Matrix
APPROVAL_MATRIX_PATH = os.environ.get("APPROVAL_MATRIX_PATH", "data/approval_matrix.yaml")

# Server
HOST = os.environ.get("HOST", "127.0.0.1")
PORT = int(os.environ.get("PORT", "8004"))

# CORS
CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "*")

# Logging
JSON_LOGS = os.environ.get("JSON_LOGS", "false").lower() == "true"
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
