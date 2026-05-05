# Deployment

## Local Deployment

### Prerequisites
- Python 3.12+
- pip

### Steps

```bash
cd procureai
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python -c "from app.db.seed import seed_all; seed_all()"
python -c "from app.rag.ingest_policy import ingest_policy_document; ingest_policy_document()"
uvicorn app.main:app --host 127.0.0.1 --port 8004
```

### Docker Deployment

```bash
docker-compose up --build
```

The API is available at `http://localhost:8004`.

## Azure Deployment

### Infrastructure

The system can be deployed to Azure Container Apps with the following architecture:

- **Azure Container Apps**: Runs the FastAPI application with auto-scaling.
- **Azure PostgreSQL**: Managed database replacing SQLite.
- **Azure AI Search**: Replaces local keyword RAG with semantic/hybrid search.
- **Azure OpenAI**: Provides LLM capabilities.
- **Azure Key Vault**: Stores secrets and API keys.
- **Application Insights**: Request tracing, performance monitoring, and structured logging.
- **Azure Blob Storage**: Stores policy documents, vendor master, and reference data.
- **Microsoft Entra ID**: Authentication and authorization.

### Configuration

Set the following environment variables in Azure Container Apps:

```env
LLM_PROVIDER=azure
AZURE_OPENAI_ENDPOINT=https://your-openai.openai.azure.com
AZURE_OPENAI_KEY=@Microsoft.KeyVault(SecretUri=https://your-vault.vault.azure.net/secrets/openai-key)
AZURE_OPENAI_CHAT_DEPLOYMENT=gpt-4o
AZURE_OPENAI_EMBED_DEPLOYMENT=text-embedding-3-small

PROCUREAI_DB_PATH=/mnt/data/procureai.db
STORAGE_BACKEND=postgres
DATABASE_URL=@Microsoft.KeyVault(SecretUri=https://your-vault.vault.azure.net/secrets/db-url)

CORS_ORIGINS=https://your-app.azurecontainerapps.io
JSON_LOGS=true
LOG_LEVEL=INFO
```

### Deployment Steps

1. Create Azure resource group, Container Apps environment, PostgreSQL, AI Search, and Key Vault.
2. Build and push Docker image to Azure Container Registry.
3. Configure Container App with the image and environment variables.
4. Set up managed identity between Container App and Azure resources.
5. Configure auto-scaling rules based on HTTP traffic or request queue depth.

## Cloud Portability Notes

- LLM provider is abstracted behind `LLM_PROVIDER` environment variable (mock, openai, azure).
- Database backend can be switched from SQLite to PostgreSQL via `STORAGE_BACKEND` and `DATABASE_URL`.
- RAG retrieval can be switched from local keyword to Azure AI Search.
- The system runs in Docker Compose and can be deployed to AWS ECS/Fargate or Kubernetes with minimal changes.

## CI/CD Pipeline

The GitHub Actions workflow (`.github/workflows/ci.yml`):

1. Runs Ruff linting
2. Seeds reference data and ingests policy documents
3. Runs pytest test suite
4. Builds Docker image (publish step optional)
