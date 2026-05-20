# Infrastructure — Document Intelligence Workbench

## Deploy (dev)

```bash
az group create --name docint-dev-rg --location eastus

az deployment group create \
  --resource-group docint-dev-rg \
  --template-file infra/bicep/main.bicep \
  --parameters infra/environments/dev.parameters.json \
  --parameters postgresAdminPassword="$(openssl rand -base64 24)"
```

## Azure Document Intelligence
F0 (free) tier: 500 pages/month. Use for dev only.
S0 tier: Pay-per-use (~$1.50 per 1000 pages). Use for staging and prod.

## Blob Storage
Documents uploaded via the API are stored in the `documents` container.
The storage account connection string is injected via environment variable.
In production, switch to Managed Identity + `DefaultAzureCredential` (see T16).

## Secret handling
`AZURE_DOCUMENT_INTELLIGENCE_KEY` must be stored in Key Vault and mapped to the Container App at deployment time.
Do not inline this key in Bicep.
