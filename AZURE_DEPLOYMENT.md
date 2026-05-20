# Azure Deployment Guide — Document Intelligence Workbench

## Prerequisites
- Azure CLI 2.50+
- Bicep CLI (`az bicep install`)
- Docker
- Contributor permissions on target subscription/resource group
- Required secrets for OpenAI/Azure OpenAI, OIDC, and database

## First-time deployment

### Step 1 — Create resource group
```bash
az login
az group create \
  --name docint-workbench-dev-rg \
  --location eastus
```

### Step 2 — Deploy infrastructure
```bash
az deployment group create \
  --resource-group docint-workbench-dev-rg \
  --template-file infra/bicep/main.bicep \
  --parameters infra/environments/dev.parameters.json \
  --parameters postgresAdminPassword="$(openssl rand -base64 24)"
```

Save outputs for ACR, Key Vault, and Container Apps.

### Step 3 — Build and push image
```bash
az acr login --name <ACR_NAME>

docker build -t <ACR_LOGIN_SERVER>/docint-workbench:latest .
docker push <ACR_LOGIN_SERVER>/docint-workbench:latest
```

### Step 4 — Add secrets to Key Vault
```bash
az keyvault secret set \
  --vault-name <KEY_VAULT_NAME> \
  --name docint-openai-key \
  --value "$OPENAI_API_KEY"

az keyvault secret set \
  --vault-name <KEY_VAULT_NAME> \
  --name docint-admin-token \
  --value "$ADMIN_TOKEN"

az keyvault secret set \
  --vault-name <KEY_VAULT_NAME> \
  --name docint-database-url \
  --value "postgresql://<user>:<password>@<host>:5432/docint_workbench?sslmode=require"
```

### Step 5 — Configure Container App environment variables
```bash
az containerapp update \
  --name <DOCINT_API_CONTAINER_APP> \
  --resource-group docint-workbench-dev-rg \
  --set-env-vars \
    LLM_PROVIDER=azure \
    DOCINT_DATABASE_BACKEND=postgres \
    DOCINT_DATABASE_URL="postgresql://<user>:<password>@<host>:5432/docint_workbench?sslmode=require" \
    AZURE_OPENAI_ENDPOINT=https://<your-openai-resource>.openai.azure.com/ \
    AZURE_KEY_VAULT_URL=https://<your-keyvault>.vault.azure.net/
```

### Step 6 — Verify
```bash
curl https://<DOCINT_API_FQDN>/health
curl https://<DOCINT_API_FQDN>/metrics/summary
```
Expected `200` responses on both checks.

## Ongoing deployments
- Push new image to ACR.
- Update API and dashboard Container App revisions.
- Validate `/health`, `/metrics/summary`, and a sample `/documents/process` call.

## Rollback
Use revision rollback steps in `RUNBOOK.md`.
