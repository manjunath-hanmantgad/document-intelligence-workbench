# AI Portfolio — Azure Integration Guide
### Extension to: AI_Portfolio_Build_Guide.md

> **How to use this document:**
> This is the Azure layer on top of the base build guide.
> Read Part 0 first (one-time setup). Then go directly to whichever project you are building.
> Each project section tells you exactly what changes from the base guide and what gets added.

---

## TABLE OF CONTENTS

- Part 0: Azure Foundation Setup
- Part 1: Entra ID — Complete Guide (implementation + client Q&A)
- Part 2: Vector Database Abstraction Layer (all 5 databases, switchable)
- Part 3: Project 1 — LLM Observatory (Azure)
- Part 4: Project 2 — Multi-Agent BPA (Azure)
- Part 5: Project 3 — LLM Fine-Tuning Pipeline (Azure)
- Part 6: Project 4 — Domain AI Copilot (Azure)
- Part 7: Project 5 — Code Review Agent (Azure)
- Part 8: Project 6 — Data Copilot (Azure)
- Part 9: Project 7 — Enterprise RAG (Azure)

---

---

# PART 0: AZURE FOUNDATION SETUP

> Do this once. Every project builds on this foundation.

---

## Step 1 — Install Azure CLI and tools

```bash
# Azure CLI
brew install azure-cli          # macOS
az --version                    # verify: should show 2.x

# Bicep CLI (comes with az cli, but verify)
az bicep version

# Terraform
brew tap hashicorp/tap
brew install hashicorp/tap/terraform
terraform --version

# Azure Developer CLI (optional but useful)
brew install azd
```

---

## Step 2 — Login and set subscription

```bash
az login                        # opens browser, sign in with your Microsoft account
az account list --output table  # see all subscriptions
az account set --subscription "YOUR_SUBSCRIPTION_ID"

# Verify
az account show --query "{name:name, id:id}" --output table
```

---

## Step 3 — Create a Resource Group naming convention

All projects follow this convention:

```
rg-<project-short-name>-<environment>
Example: rg-llm-observatory-dev
         rg-enterprise-rag-prod
```

```bash
# Create resource group for a project (run once per project)
az group create \
  --name rg-llm-observatory-dev \
  --location eastus2
```

> **Why eastus2?** Azure OpenAI has broadest model availability in East US 2.
> Other good options: swedencentral (EU data residency), australiaeast.

---

## Step 4 — Provision Azure OpenAI (once per subscription)

```bash
# Create Azure OpenAI resource
az cognitiveservices account create \
  --name aoai-portfolio-dev \
  --resource-group rg-llm-observatory-dev \
  --location eastus2 \
  --kind OpenAI \
  --sku S0

# Deploy models
az cognitiveservices account deployment create \
  --name aoai-portfolio-dev \
  --resource-group rg-llm-observatory-dev \
  --deployment-name gpt-4o \
  --model-name gpt-4o \
  --model-version "2024-11-20" \
  --model-format OpenAI \
  --sku-capacity 10 \
  --sku-name Standard

az cognitiveservices account deployment create \
  --name aoai-portfolio-dev \
  --resource-group rg-llm-observatory-dev \
  --deployment-name text-embedding-3-small \
  --model-name text-embedding-3-small \
  --model-version "1" \
  --model-format OpenAI \
  --sku-capacity 10 \
  --sku-name Standard

# Get endpoint and key
az cognitiveservices account show \
  --name aoai-portfolio-dev \
  --resource-group rg-llm-observatory-dev \
  --query properties.endpoint

az cognitiveservices account keys list \
  --name aoai-portfolio-dev \
  --resource-group rg-llm-observatory-dev
```

---

## Step 5 — Azure OpenAI Client Wrapper (used in ALL projects)

Create `shared/llm_client.py` — copy this into every project:

```python
import os
from openai import AzureOpenAI, OpenAI

def get_llm_client():
    """
    Returns either Azure OpenAI or direct OpenAI client based on env config.
    Switch via LLM_PROVIDER env var: 'azure' (default) or 'openai'
    """
    provider = os.getenv("LLM_PROVIDER", "azure")

    if provider == "azure":
        return AzureOpenAI(
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_KEY"),
            api_version="2024-02-01"
        )
    else:
        return OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_model_name(purpose: str = "chat") -> str:
    """
    Returns the correct model name/deployment name based on provider.
    Azure uses deployment names; OpenAI uses model names.
    """
    provider = os.getenv("LLM_PROVIDER", "azure")
    models = {
        "azure": {
            "chat": os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT", "gpt-4o"),
            "mini": os.getenv("AZURE_OPENAI_MINI_DEPLOYMENT", "gpt-4o-mini"),
            "embed": os.getenv("AZURE_OPENAI_EMBED_DEPLOYMENT", "text-embedding-3-small")
        },
        "openai": {
            "chat": "gpt-4o",
            "mini": "gpt-4o-mini",
            "embed": "text-embedding-3-small"
        }
    }
    return models[provider][purpose]

# Usage in any project:
# client = get_llm_client()
# model = get_model_name("chat")
# response = client.chat.completions.create(model=model, messages=[...])
```

### Shared `.env.example` (all projects extend this)

```
# Provider switch
LLM_PROVIDER=azure                  # "azure" or "openai"

# Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://aoai-portfolio-dev.openai.azure.com/
AZURE_OPENAI_KEY=your_key_here
AZURE_OPENAI_CHAT_DEPLOYMENT=gpt-4o
AZURE_OPENAI_MINI_DEPLOYMENT=gpt-4o-mini
AZURE_OPENAI_EMBED_DEPLOYMENT=text-embedding-3-small

# Direct OpenAI (fallback)
OPENAI_API_KEY=

# Azure Entra ID
AZURE_TENANT_ID=
AZURE_CLIENT_ID=
AZURE_CLIENT_SECRET=

# Key Vault
AZURE_KEY_VAULT_URL=https://kv-portfolio-dev.vault.azure.net/
```

---

## Step 6 — Azure Key Vault (secrets management)

Never put real secrets in `.env` files in production. Use Key Vault.

```bash
# Create Key Vault
az keyvault create \
  --name kv-portfolio-dev \
  --resource-group rg-llm-observatory-dev \
  --location eastus2

# Store secrets
az keyvault secret set --vault-name kv-portfolio-dev \
  --name "azure-openai-key" --value "your_key"
az keyvault secret set --vault-name kv-portfolio-dev \
  --name "postgres-password" --value "your_password"
```

Create `shared/secrets.py`:

```python
import os
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential, ClientSecretCredential

def get_secret(secret_name: str) -> str:
    """
    Fetch secret from Azure Key Vault.
    Falls back to environment variable if Key Vault URL not set (local dev).
    """
    vault_url = os.getenv("AZURE_KEY_VAULT_URL")

    if not vault_url:
        # Local dev: read from env directly
        env_key = secret_name.upper().replace("-", "_")
        return os.getenv(env_key, "")

    credential = DefaultAzureCredential()
    client = SecretClient(vault_url=vault_url, credential=credential)
    return client.get_secret(secret_name).value

# Usage:
# db_password = get_secret("postgres-password")
# aoai_key = get_secret("azure-openai-key")
```

---

## Step 7 — Azure Container Registry (for all projects)

```bash
# Create ACR (one per portfolio)
az acr create \
  --name acrportfoliodev \
  --resource-group rg-llm-observatory-dev \
  --sku Basic \
  --admin-enabled true

# Login to ACR
az acr login --name acrportfoliodev

# Build and push image (template — run from each project folder)
docker build -t acrportfoliodev.azurecr.io/PROJECT_NAME:latest .
docker push acrportfoliodev.azurecr.io/PROJECT_NAME:latest
```

---

## Step 8 — Application Insights (shared monitoring)

```bash
# Create Log Analytics Workspace
az monitor log-analytics workspace create \
  --workspace-name law-portfolio-dev \
  --resource-group rg-llm-observatory-dev \
  --location eastus2

# Create Application Insights
az monitor app-insights component create \
  --app appi-portfolio-dev \
  --location eastus2 \
  --resource-group rg-llm-observatory-dev \
  --workspace law-portfolio-dev

# Get connection string
az monitor app-insights component show \
  --app appi-portfolio-dev \
  --resource-group rg-llm-observatory-dev \
  --query connectionString
```

Add to every project:

```bash
uv pip install opencensus-ext-azure applicationinsights
```

Create `shared/telemetry.py`:

```python
import os
import logging
from opencensus.ext.azure.log_exporter import AzureLogHandler
from opencensus.ext.azure import metrics_exporter
from opencensus.stats import aggregation, measure, view, stats

CONNECTION_STRING = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")

def setup_telemetry(service_name: str):
    """Wire up Application Insights logging for any service."""
    if not CONNECTION_STRING:
        return  # local dev — skip

    logger = logging.getLogger(service_name)
    logger.addHandler(AzureLogHandler(connection_string=CONNECTION_STRING))
    logger.setLevel(logging.INFO)
    return logger

def track_event(name: str, properties: dict = None):
    """Track a custom event to Application Insights."""
    from applicationinsights import TelemetryClient
    if not CONNECTION_STRING:
        return
    tc = TelemetryClient(CONNECTION_STRING)
    tc.track_event(name, properties)
    tc.flush()

# Usage:
# logger = setup_telemetry("llm-gateway")
# logger.info("Request processed", extra={"custom_dimensions": {"latency_ms": 230}})
# track_event("hallucination_detected", {"endpoint": "legal-copilot", "severity": "high"})
```

---

---

# PART 1: ENTRA ID — COMPLETE GUIDE

> This section has two parts:
> 1. Practical implementation you will use in projects
> 2. Client Q&A reference — everything you need to answer enterprise questions confidently

---

## 1.1 What Is Entra ID? (Conceptual)

**Entra ID** (formerly Azure Active Directory / Azure AD) is Microsoft's cloud identity platform. Every Microsoft 365 or Azure customer already has a tenant. It handles:

- **Who are you?** → Authentication (proving identity)
- **What can you do?** → Authorization (permissions)
- **How do you prove it?** → OAuth 2.0 / OIDC tokens (JWTs)

### Key Concepts

| Concept | What It Is | Analogy |
|---------|-----------|---------|
| **Tenant** | Your organization's identity namespace | Your company's "account" with Microsoft |
| **App Registration** | Registers your application as an OAuth client | Like registering a new app in any OAuth system |
| **Service Principal** | The runtime identity of your app in a tenant | The app's "user account" |
| **Managed Identity** | Auto-managed identity for Azure resources (no secrets needed) | An IAM role in AWS |
| **Access Token** | JWT issued after login — proves who you are and what you can do | A signed badge |
| **Groups** | Collections of users — used to assign roles at scale | Teams |
| **App Roles** | Permissions defined in your App Registration | Custom claims in the token |
| **Conditional Access** | Policies that apply before a token is issued (e.g., require MFA, block non-corporate devices) | Firewall rules for identity |

---

## 1.2 Authentication Flows — What Clients Will Ask About

### Flow 1: Authorization Code Flow (user-facing web app)

```
User → Your App → Redirect to Microsoft Login Page
                ← User logs in with their org account
                ← Microsoft issues Authorization Code
Your App → Exchange code for Access Token + Refresh Token
Your App → Call your API with Bearer Token
API → Validate token → Serve request
```

**When used:** Any web app where a human logs in (most enterprise apps).

### Flow 2: Client Credentials Flow (service-to-service, no user)

```
Your AI Agent → POST to Entra ID token endpoint
                  (client_id + client_secret or certificate)
              ← Access Token (JWT, no user context)
Your AI Agent → Call downstream API with Bearer Token
```

**When used:** Background jobs, AI agents calling APIs, microservice-to-microservice calls.

### Flow 3: Managed Identity (Azure-to-Azure, no credentials at all)

```
Your Container App → Request token from Azure Instance Metadata Service
                   ← Token (no client_id/secret needed — Azure handles it)
Your Container App → Call Azure OpenAI / Key Vault / Storage with token
```

**When used:** Any Azure resource calling another Azure resource. No secrets needed anywhere. This is the most secure option.

---

## 1.3 Practical Implementation (Simple Version for Portfolio)

**What we implement:** Validate Bearer tokens issued by Entra ID in our FastAPI apps. Extract user groups. Map groups to app-level roles.

### Step 1 — Register your app in Entra ID

```
Azure Portal → Entra ID → App Registrations → New Registration

Name: ai-portfolio-app
Supported account types: Accounts in this organizational directory only
Redirect URI: (leave blank for API-only apps)

After creation:
- Copy: Application (client) ID  → AZURE_CLIENT_ID
- Copy: Directory (tenant) ID   → AZURE_TENANT_ID

Then: Certificates & Secrets → New client secret
- Copy the secret value         → AZURE_CLIENT_SECRET
```

### Step 2 — Define App Roles (in App Registration)

```
App Registration → App Roles → Create app role

Role 1:
  Display name: AI.Admin
  Value: AI.Admin
  Description: Full access to all AI systems

Role 2:
  Display name: AI.User
  Value: AI.User
  Description: Read-only access, can query AI systems

Role 3:
  Display name: AI.Viewer
  Value: AI.Viewer
  Description: View dashboards only
```

### Step 3 — Assign users to roles

```
Azure Portal → Entra ID → Enterprise Applications → ai-portfolio-app
→ Users and Groups → Add user/group → Select role
```

### Step 4 — Token validation in FastAPI

```bash
uv pip install python-jose[cryptography] httpx
```

Create `shared/auth.py`:

```python
import os
import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from functools import lru_cache

TENANT_ID = os.getenv("AZURE_TENANT_ID")
CLIENT_ID = os.getenv("AZURE_CLIENT_ID")

# Entra ID OIDC config URL
OIDC_CONFIG_URL = f"https://login.microsoftonline.com/{TENANT_ID}/v2.0/.well-known/openid-configuration"

security = HTTPBearer()

@lru_cache(maxsize=1)
def get_oidc_config():
    """Fetch OIDC config once and cache it."""
    response = httpx.get(OIDC_CONFIG_URL)
    return response.json()

@lru_cache(maxsize=1)
def get_jwks():
    """Fetch public signing keys from Microsoft. Cached."""
    config = get_oidc_config()
    response = httpx.get(config["jwks_uri"])
    return response.json()

def validate_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    Validate an Entra ID JWT token.
    Returns decoded token payload (contains user info + roles).
    """
    token = credentials.credentials
    jwks = get_jwks()

    try:
        # Decode and validate the JWT
        payload = jwt.decode(
            token,
            jwks,
            algorithms=["RS256"],
            audience=CLIENT_ID,
            options={"verify_exp": True}
        )
        return payload

    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}"
        )

def require_role(required_role: str):
    """
    Dependency factory — use as: Depends(require_role("AI.Admin"))
    Checks that the token contains the required app role.
    """
    def role_checker(payload: dict = Depends(validate_token)):
        roles = payload.get("roles", [])
        if required_role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{required_role}' required. Your roles: {roles}"
            )
        return payload
    return role_checker

def get_current_user(payload: dict = Depends(validate_token)) -> dict:
    """Extract user info from validated token."""
    return {
        "user_id": payload.get("oid"),           # object ID (unique per user)
        "email": payload.get("preferred_username"),
        "name": payload.get("name"),
        "roles": payload.get("roles", []),
        "tenant_id": payload.get("tid")
    }
```

### Step 5 — Use in FastAPI routes

```python
from fastapi import FastAPI, Depends
from shared.auth import get_current_user, require_role

app = FastAPI()

# Any authenticated user
@app.get("/query")
def query(user=Depends(get_current_user)):
    return {"message": f"Hello {user['email']}", "roles": user["roles"]}

# Only AI.Admin role
@app.delete("/documents/{doc_id}")
def delete_doc(doc_id: str, user=Depends(require_role("AI.Admin"))):
    return {"deleted": doc_id, "by": user["email"]}

# Only AI.User or AI.Admin
@app.post("/ingest")
def ingest(user=Depends(require_role("AI.User"))):
    return {"status": "ingesting", "user": user["email"]}
```

### Step 6 — Getting a token for testing

```bash
# Get a token using client credentials (service-to-service test)
curl -X POST \
  https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials" \
  -d "client_id={CLIENT_ID}" \
  -d "client_secret={CLIENT_SECRET}" \
  -d "scope=api://{CLIENT_ID}/.default"

# Use the returned access_token:
curl -X GET http://localhost:8000/query \
  -H "Authorization: Bearer {ACCESS_TOKEN}"
```

---

## 1.4 Managed Identity (The Right Way for Production)

When your Container App calls Azure OpenAI or Key Vault, **do not use API keys**. Use Managed Identity:

```bash
# Enable system-assigned managed identity on a Container App
az containerapp identity assign \
  --name ca-llm-observatory \
  --resource-group rg-llm-observatory-dev \
  --system-assigned

# Grant the Container App access to Azure OpenAI
az role assignment create \
  --role "Cognitive Services OpenAI User" \
  --assignee $(az containerapp identity show \
    --name ca-llm-observatory \
    --resource-group rg-llm-observatory-dev \
    --query principalId -o tsv) \
  --scope $(az cognitiveservices account show \
    --name aoai-portfolio-dev \
    --resource-group rg-llm-observatory-dev \
    --query id -o tsv)
```

In code (uses Managed Identity automatically):

```python
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from openai import AzureOpenAI

# DefaultAzureCredential tries: Managed Identity → VS Code → CLI → env vars
credential = DefaultAzureCredential()
token_provider = get_bearer_token_provider(
    credential, "https://cognitiveservices.azure.com/.default"
)

client = AzureOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    azure_ad_token_provider=token_provider,  # no API key needed
    api_version="2024-02-01"
)
```

---

## 1.5 Client Q&A Reference

> Memorize these. These come up in every enterprise sales conversation.

---

**Q: We already use Azure AD / Entra ID for all our apps. Can your system integrate with it?**

> "Yes, it's designed for it. Your users log in with their existing Microsoft accounts — no new passwords, no new identity system. I register the app in your tenant, you assign your existing groups or users to roles I define, and the app enforces those roles on every API call. If someone leaves your organization and gets disabled in Entra ID, they lose access to the AI system immediately — no manual cleanup needed."

---

**Q: Does it support MFA?**

> "MFA is enforced at the Entra ID level, not in the application. If your tenant's Conditional Access policy requires MFA, users will be prompted before they receive a token. The application never sees a password or MFA code — it only sees the signed token, which proves Microsoft already verified the user."

---

**Q: What about Conditional Access? We require compliant devices.**

> "Conditional Access policies apply before a token is issued. If your policy requires a compliant device or a specific network location, a user on an unmanaged device simply won't get a token — my app never even receives the request. That's the value of delegating to Entra ID rather than building access control in the app."

---

**Q: How do we control which employees can access the AI system?**

> "Two ways. First, in App Registration → Users and Groups, you can restrict the app to specific users or groups — only those assigned can log in. Second, I define App Roles (like AI.Admin, AI.User, AI.Viewer), and you assign your existing Entra ID groups to those roles. Your IT team controls access entirely from the Azure portal — no code changes needed."

---

**Q: What about the AI agents running in the background — they don't have a human login?**

> "Service-to-service calls use the Client Credentials flow — the agent authenticates with its own App Registration (client ID + secret or certificate) and gets a token without a user involved. In production I'd recommend a Managed Identity instead — it's an identity Azure assigns to the container directly, no secrets stored anywhere, Azure rotates everything automatically."

---

**Q: Can you audit who queried what?**

> "Every API call includes the user's object ID from the token, which maps to a specific person in your Entra ID directory. I log that to Application Insights or a database. You can query: which user ran which query, when, and what the response was. Combined with Entra ID's sign-in logs, you have a complete audit trail."

---

**Q: What if we're on-premises Active Directory, not Entra ID?**

> "If you have AD Connect (on-prem AD synced to Entra ID), it works exactly the same — your on-prem users are available in Entra ID. If you're fully on-prem with no sync, we'd need to discuss options: either set up AD Connect, use ADFS (Active Directory Federation Services) as a SAML/OIDC bridge, or implement a different auth strategy."

---

**Q: How is this different from just using API keys?**

> "API keys are static credentials — if one leaks, it's compromised until manually rotated. Entra ID tokens expire (typically 1 hour), are tied to a specific user's identity, can be revoked instantly, and carry role claims so we don't need a separate role database. For a single developer using an API, keys are fine. For a 500-person organization, you want identity-based access that integrates with your existing HR and IT processes."

---

---

# PART 2: VECTOR DATABASE ABSTRACTION LAYER

> One interface. Five backends. Switch via config.
> Every RAG/copilot project uses this layer.

---

## 2.1 Why an Abstraction Layer

```
Without abstraction:          With abstraction:
  Project uses Qdrant           config: VECTOR_DB=qdrant
  Client wants Pinecone         config: VECTOR_DB=pinecone
  → Rewrite ingestion code      → Change one env var
  → Rewrite search code         → Done
  → Rewrite all tests
```

---

## 2.2 The Interface

Create `shared/vector_store/base.py`:

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class SearchResult:
    text: str
    score: float
    metadata: dict
    id: str

class VectorStore(ABC):
    """Abstract interface all vector store implementations must follow."""

    @abstractmethod
    def create_collection(self, collection_name: str, dimension: int = 1536):
        """Create a collection/index if it doesn't exist."""
        pass

    @abstractmethod
    def upsert(self, collection_name: str, ids: List[str],
               vectors: List[List[float]], payloads: List[dict]):
        """Insert or update vectors with metadata."""
        pass

    @abstractmethod
    def search(self, collection_name: str, query_vector: List[float],
               top_k: int = 5, filters: Optional[dict] = None) -> List[SearchResult]:
        """Search for similar vectors. Filters are key-value pairs for metadata filtering."""
        pass

    @abstractmethod
    def delete(self, collection_name: str, ids: List[str]):
        """Delete vectors by ID."""
        pass

    @abstractmethod
    def count(self, collection_name: str) -> int:
        """Return number of vectors in collection."""
        pass
```

---

## 2.3 Implementation: Azure AI Search

Create `shared/vector_store/azure_search.py`:

```python
import os
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex, SearchField, SearchFieldDataType,
    VectorSearch, HnswAlgorithmConfiguration,
    VectorSearchProfile, SimpleField, SearchableField
)
from azure.search.documents.models import VectorizedQuery
from azure.core.credentials import AzureKeyCredential
from .base import VectorStore, SearchResult

class AzureAISearch(VectorStore):
    def __init__(self):
        endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
        key = os.getenv("AZURE_SEARCH_KEY")
        self.credential = AzureKeyCredential(key)
        self.endpoint = endpoint
        self.index_client = SearchIndexClient(endpoint, self.credential)

    def create_collection(self, collection_name: str, dimension: int = 1536):
        fields = [
            SimpleField(name="id", type=SearchFieldDataType.String, key=True),
            SearchableField(name="text", type=SearchFieldDataType.String),
            SimpleField(name="source", type=SearchFieldDataType.String, filterable=True),
            SimpleField(name="department", type=SearchFieldDataType.String, filterable=True),
            SimpleField(name="tenant_id", type=SearchFieldDataType.String, filterable=True),
            SearchField(
                name="vector",
                type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                vector_search_dimensions=dimension,
                vector_search_profile_name="hnsw-profile"
            )
        ]
        vector_search = VectorSearch(
            algorithms=[HnswAlgorithmConfiguration(name="hnsw-algo")],
            profiles=[VectorSearchProfile(name="hnsw-profile", algorithm_configuration_name="hnsw-algo")]
        )
        index = SearchIndex(name=collection_name, fields=fields, vector_search=vector_search)
        self.index_client.create_or_update_index(index)

    def upsert(self, collection_name: str, ids, vectors, payloads):
        client = SearchClient(self.endpoint, collection_name, self.credential)
        documents = [
            {"id": id_, "vector": vec, **payload}
            for id_, vec, payload in zip(ids, vectors, payloads)
        ]
        client.upload_documents(documents)

    def search(self, collection_name: str, query_vector, top_k=5, filters=None):
        client = SearchClient(self.endpoint, collection_name, self.credential)

        filter_str = None
        if filters:
            filter_str = " and ".join([f"{k} eq '{v}'" for k, v in filters.items()])

        vector_query = VectorizedQuery(
            vector=query_vector, k_nearest_neighbors=top_k, fields="vector"
        )

        results = client.search(
            search_text=None,
            vector_queries=[vector_query],
            filter=filter_str,
            top=top_k
        )

        return [SearchResult(
            text=r["text"], score=r["@search.score"],
            metadata={k: v for k, v in r.items() if k not in ["text", "vector", "@search.score"]},
            id=r["id"]
        ) for r in results]

    def delete(self, collection_name: str, ids):
        client = SearchClient(self.endpoint, collection_name, self.credential)
        client.delete_documents([{"id": id_} for id_ in ids])

    def count(self, collection_name: str) -> int:
        client = SearchClient(self.endpoint, collection_name, self.credential)
        return client.get_document_count()
```

---

## 2.4 Implementation: Qdrant

Create `shared/vector_store/qdrant_store.py`:

```python
import os
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct,
    Filter, FieldCondition, MatchValue
)
from .base import VectorStore, SearchResult

class QdrantStore(VectorStore):
    def __init__(self):
        url = os.getenv("QDRANT_URL", "http://localhost:6333")
        api_key = os.getenv("QDRANT_API_KEY")  # for Qdrant Cloud
        self.client = QdrantClient(url=url, api_key=api_key)

    def create_collection(self, collection_name: str, dimension: int = 1536):
        existing = [c.name for c in self.client.get_collections().collections]
        if collection_name not in existing:
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=dimension, distance=Distance.COSINE)
            )

    def upsert(self, collection_name: str, ids, vectors, payloads):
        points = [
            PointStruct(id=id_, vector=vec, payload=payload)
            for id_, vec, payload in zip(ids, vectors, payloads)
        ]
        self.client.upsert(collection_name=collection_name, points=points)

    def search(self, collection_name: str, query_vector, top_k=5, filters=None):
        qdrant_filter = None
        if filters:
            conditions = [
                FieldCondition(key=k, match=MatchValue(value=v))
                for k, v in filters.items()
            ]
            qdrant_filter = Filter(must=conditions)

        results = self.client.search(
            collection_name=collection_name,
            query_vector=query_vector,
            query_filter=qdrant_filter,
            limit=top_k,
            with_payload=True
        )

        return [SearchResult(
            text=r.payload["text"], score=r.score,
            metadata={k: v for k, v in r.payload.items() if k != "text"},
            id=str(r.id)
        ) for r in results]

    def delete(self, collection_name: str, ids):
        self.client.delete(collection_name=collection_name, points_selector=ids)

    def count(self, collection_name: str) -> int:
        return self.client.count(collection_name=collection_name).count
```

---

## 2.5 Implementation: Chroma

Create `shared/vector_store/chroma_store.py`:

```python
import os
import chromadb
from .base import VectorStore, SearchResult

class ChromaStore(VectorStore):
    def __init__(self):
        mode = os.getenv("CHROMA_MODE", "local")  # "local" or "http"
        if mode == "http":
            self.client = chromadb.HttpClient(
                host=os.getenv("CHROMA_HOST", "localhost"),
                port=int(os.getenv("CHROMA_PORT", 8000))
            )
        else:
            self.client = chromadb.PersistentClient(
                path=os.getenv("CHROMA_PERSIST_PATH", "./chroma_data")
            )

    def create_collection(self, collection_name: str, dimension: int = 1536):
        self.client.get_or_create_collection(name=collection_name)

    def upsert(self, collection_name: str, ids, vectors, payloads):
        collection = self.client.get_or_create_collection(collection_name)
        texts = [p.get("text", "") for p in payloads]
        collection.upsert(
            ids=[str(id_) for id_ in ids],
            embeddings=vectors,
            documents=texts,
            metadatas=payloads
        )

    def search(self, collection_name: str, query_vector, top_k=5, filters=None):
        collection = self.client.get_collection(collection_name)
        where = filters if filters else None
        results = collection.query(
            query_embeddings=[query_vector],
            n_results=top_k,
            where=where
        )
        output = []
        for i, doc in enumerate(results["documents"][0]):
            output.append(SearchResult(
                text=doc,
                score=1 - results["distances"][0][i],  # chroma returns distances
                metadata=results["metadatas"][0][i],
                id=results["ids"][0][i]
            ))
        return output

    def delete(self, collection_name: str, ids):
        collection = self.client.get_collection(collection_name)
        collection.delete(ids=[str(id_) for id_ in ids])

    def count(self, collection_name: str) -> int:
        return self.client.get_collection(collection_name).count()
```

---

## 2.6 Implementation: FAISS

Create `shared/vector_store/faiss_store.py`:

```python
import os
import pickle
import numpy as np
import faiss
from pathlib import Path
from .base import VectorStore, SearchResult

class FAISSStore(VectorStore):
    """
    FAISS is a local, in-memory/disk index. No server required.
    Best for: local dev, privacy-sensitive clients, offline demos.
    Not suitable for: multi-instance production (no distributed support).
    """
    def __init__(self):
        self.persist_dir = Path(os.getenv("FAISS_PERSIST_PATH", "./faiss_data"))
        self.persist_dir.mkdir(exist_ok=True)
        self.indexes = {}    # collection_name -> faiss index
        self.metadata = {}   # collection_name -> list of payload dicts
        self.id_maps = {}    # collection_name -> list of string IDs

    def _index_path(self, name): return self.persist_dir / f"{name}.index"
    def _meta_path(self, name): return self.persist_dir / f"{name}.pkl"

    def _load(self, collection_name: str):
        if collection_name not in self.indexes:
            idx_path = self._index_path(collection_name)
            meta_path = self._meta_path(collection_name)
            if idx_path.exists():
                self.indexes[collection_name] = faiss.read_index(str(idx_path))
                with open(meta_path, "rb") as f:
                    data = pickle.load(f)
                    self.metadata[collection_name] = data["metadata"]
                    self.id_maps[collection_name] = data["ids"]

    def _save(self, collection_name: str):
        faiss.write_index(self.indexes[collection_name], str(self._index_path(collection_name)))
        with open(self._meta_path(collection_name), "wb") as f:
            pickle.dump({
                "metadata": self.metadata[collection_name],
                "ids": self.id_maps[collection_name]
            }, f)

    def create_collection(self, collection_name: str, dimension: int = 1536):
        self._load(collection_name)
        if collection_name not in self.indexes:
            self.indexes[collection_name] = faiss.IndexFlatIP(dimension)  # inner product = cosine on normalized vecs
            self.metadata[collection_name] = []
            self.id_maps[collection_name] = []

    def upsert(self, collection_name: str, ids, vectors, payloads):
        self._load(collection_name)
        arr = np.array(vectors, dtype=np.float32)
        faiss.normalize_L2(arr)  # normalize for cosine similarity
        self.indexes[collection_name].add(arr)
        self.metadata[collection_name].extend(payloads)
        self.id_maps[collection_name].extend([str(id_) for id_ in ids])
        self._save(collection_name)

    def search(self, collection_name: str, query_vector, top_k=5, filters=None):
        self._load(collection_name)
        if collection_name not in self.indexes:
            return []
        arr = np.array([query_vector], dtype=np.float32)
        faiss.normalize_L2(arr)
        scores, indices = self.indexes[collection_name].search(arr, top_k * 3)  # oversample for filtering

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1: continue
            payload = self.metadata[collection_name][idx]
            if filters and not all(payload.get(k) == v for k, v in filters.items()):
                continue
            results.append(SearchResult(
                text=payload.get("text", ""),
                score=float(score),
                metadata={k: v for k, v in payload.items() if k != "text"},
                id=self.id_maps[collection_name][idx]
            ))
            if len(results) == top_k:
                break
        return results

    def delete(self, collection_name: str, ids): pass  # FAISS flat index doesn't support deletion natively

    def count(self, collection_name: str) -> int:
        self._load(collection_name)
        return self.indexes.get(collection_name, faiss.IndexFlatIP(1536)).ntotal
```

---

## 2.7 Implementation: Pinecone

Create `shared/vector_store/pinecone_store.py`:

```python
import os
from pinecone import Pinecone, ServerlessSpec
from .base import VectorStore, SearchResult

class PineconeStore(VectorStore):
    def __init__(self):
        self.pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        self.cloud = os.getenv("PINECONE_CLOUD", "aws")
        self.region = os.getenv("PINECONE_REGION", "us-east-1")

    def create_collection(self, collection_name: str, dimension: int = 1536):
        existing = [idx.name for idx in self.pc.list_indexes()]
        if collection_name not in existing:
            self.pc.create_index(
                name=collection_name,
                dimension=dimension,
                metric="cosine",
                spec=ServerlessSpec(cloud=self.cloud, region=self.region)
            )

    def upsert(self, collection_name: str, ids, vectors, payloads):
        index = self.pc.Index(collection_name)
        vectors_with_meta = [
            (str(id_), vec, payload)
            for id_, vec, payload in zip(ids, vectors, payloads)
        ]
        index.upsert(vectors=vectors_with_meta)

    def search(self, collection_name: str, query_vector, top_k=5, filters=None):
        index = self.pc.Index(collection_name)
        results = index.query(
            vector=query_vector,
            top_k=top_k,
            filter=filters,
            include_metadata=True
        )
        return [SearchResult(
            text=r.metadata.get("text", ""),
            score=r.score,
            metadata={k: v for k, v in r.metadata.items() if k != "text"},
            id=r.id
        ) for r in results.matches]

    def delete(self, collection_name: str, ids):
        self.pc.Index(collection_name).delete(ids=[str(id_) for id_ in ids])

    def count(self, collection_name: str) -> int:
        return self.pc.Index(collection_name).describe_index_stats()["total_vector_count"]
```

---

## 2.8 The Factory — One Line to Switch

Create `shared/vector_store/__init__.py`:

```python
import os
from .base import VectorStore

def get_vector_store() -> VectorStore:
    """
    Returns the configured vector store implementation.
    Set VECTOR_DB env var to switch:
      azure_search | qdrant | chroma | faiss | pinecone
    Default: qdrant (local dev), azure_search (production)
    """
    db = os.getenv("VECTOR_DB", "qdrant")

    if db == "azure_search":
        from .azure_search import AzureAISearch
        return AzureAISearch()
    elif db == "qdrant":
        from .qdrant_store import QdrantStore
        return QdrantStore()
    elif db == "chroma":
        from .chroma_store import ChromaStore
        return ChromaStore()
    elif db == "faiss":
        from .faiss_store import FAISSStore
        return FAISSStore()
    elif db == "pinecone":
        from .pinecone_store import PineconeStore
        return PineconeStore()
    else:
        raise ValueError(f"Unknown VECTOR_DB: {db}. Options: azure_search, qdrant, chroma, faiss, pinecone")
```

Usage in any project:

```python
from shared.vector_store import get_vector_store

store = get_vector_store()   # reads VECTOR_DB env var
store.create_collection("my-collection")
store.upsert("my-collection", ids=["1"], vectors=[[...]], payloads=[{"text": "hello"}])
results = store.search("my-collection", query_vector=[...], top_k=5)
```

---

## 2.9 Vector DB Comparison — Client Reference

| Database | Best For | Hosted Option | Filtering | Scale | Cost |
|----------|---------|---------------|-----------|-------|------|
| **Azure AI Search** | Enterprise Azure shops, hybrid search + BM25, compliance | Azure (managed) | Rich (OData filters) | Very high | $$ |
| **Qdrant** | Production self-hosted, RBAC metadata, high performance | Qdrant Cloud | Payload filters | High | $ (OSS free) |
| **Pinecone** | Fully managed, no ops, fast setup | Pinecone Cloud | Metadata filters | Very high | $$$ |
| **Chroma** | Local dev, prototyping, Python-native simplicity | Chroma Cloud (beta) | Where filters | Medium | Free (OSS) |
| **FAISS** | Privacy-first/offline, no network, pure local | None (local only) | Manual (post-filter) | Medium (single node) | Free |

**When a client asks "which should we use?":**
- Azure shop with compliance requirements → Azure AI Search
- Startup, full control, own infra → Qdrant
- Wants zero infra management, fine with SaaS → Pinecone
- Sensitive data, cannot use external services → FAISS
- Rapid prototype, doesn't matter yet → Chroma

---

---

# PART 3: PROJECT 1 — LLM OBSERVATORY (AZURE)

## What changes from base guide

| Component | Base Guide | Azure Version |
|-----------|-----------|---------------|
| LLM calls | OpenAI SDK | Azure OpenAI via wrapper |
| Metrics storage | DuckDB | DuckDB (local) + Azure Cosmos DB (prod) |
| Dashboard | Streamlit | Streamlit + Azure Monitor workbooks |
| Alerts | Slack webhook | Slack + Azure Monitor alert rules |
| Deployment | Docker Compose | Azure Container Apps |
| Secrets | .env file | Azure Key Vault |

---

## Azure Architecture

```
[FastAPI Gateway] → [Azure OpenAI] (all LLM calls logged)
       ↓
[Eval Engine] → [Azure OpenAI] (LLM-as-judge)
       ↓
[Cosmos DB NoSQL] (metrics, eval results)
       ↓
[Azure Monitor + App Insights] → [Streamlit Dashboard]
       ↓
[Alert Rules] → [Slack / Email / PagerDuty]

All deployed as: Azure Container Apps
Secrets in: Azure Key Vault
Images in: Azure Container Registry
Auth: Azure Entra ID
```

---

## Step 1 — Update gateway to use Azure OpenAI

Replace the OpenAI client in `gateway/gateway.py`:

```python
# Replace: from openai import OpenAI
import sys
sys.path.insert(0, "..")
from shared.llm_client import get_llm_client, get_model_name
from shared.telemetry import setup_telemetry, track_event

logger = setup_telemetry("llm-gateway")
client = get_llm_client()

@app.post("/chat")
async def chat(request: Request):
    body = await request.json()
    model = get_model_name("chat")   # reads from env, returns deployment name
    # ... rest of code unchanged
```

---

## Step 2 — Add Cosmos DB for production metrics

Install:
```bash
uv pip install azure-cosmos
```

Create `storage/cosmos_store.py`:

```python
import os
from azure.cosmos import CosmosClient, PartitionKey
from datetime import datetime

COSMOS_URL = os.getenv("COSMOS_URL")
COSMOS_KEY = os.getenv("COSMOS_KEY")
DB_NAME = "llm_observatory"

def get_container(container_name: str):
    client = CosmosClient(COSMOS_URL, COSMOS_KEY)
    db = client.create_database_if_not_exists(id=DB_NAME)
    return db.create_container_if_not_exists(
        id=container_name,
        partition_key=PartitionKey(path="/endpoint")
    )

def log_request(log_entry: dict):
    container = get_container("llm_logs")
    log_entry["id"] = log_entry.get("id", str(datetime.now().timestamp()))
    container.upsert_item(log_entry)

def log_eval_result(eval_entry: dict):
    container = get_container("eval_results")
    container.upsert_item(eval_entry)
```

---

## Step 3 — Bicep Deployment

Create `infra/bicep/main.bicep`:

```bicep
@description('Environment name')
param envName string = 'dev'

@description('Azure region')
param location string = resourceGroup().location

// Container Apps Environment
resource cae 'Microsoft.App/managedEnvironments@2023-05-01' = {
  name: 'cae-llm-observatory-${envName}'
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalytics.properties.customerId
        sharedKey: logAnalytics.listKeys().primarySharedKey
      }
    }
  }
}

// Log Analytics
resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2022-10-01' = {
  name: 'law-llm-observatory-${envName}'
  location: location
  properties: { sku: { name: 'PerGB2018' } }
}

// Key Vault
resource kv 'Microsoft.KeyVault/vaults@2023-02-01' = {
  name: 'kv-obs-${envName}'
  location: location
  properties: {
    sku: { family: 'A', name: 'standard' }
    tenantId: subscription().tenantId
    enableRbacAuthorization: true
  }
}

// Gateway Container App
resource gatewayApp 'Microsoft.App/containerApps@2023-05-01' = {
  name: 'ca-gateway-${envName}'
  location: location
  identity: { type: 'SystemAssigned' }  // Managed Identity
  properties: {
    managedEnvironmentId: cae.id
    configuration: {
      ingress: {
        external: true
        targetPort: 8001
      }
      secrets: [
        {
          name: 'aoai-key'
          keyVaultUrl: '${kv.properties.vaultUri}secrets/azure-openai-key'
          identity: 'system'
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'gateway'
          image: 'acrportfoliodev.azurecr.io/llm-gateway:latest'
          resources: { cpu: json('0.5'), memory: '1Gi' }
          env: [
            { name: 'LLM_PROVIDER', value: 'azure' }
            { name: 'AZURE_OPENAI_ENDPOINT', value: 'https://aoai-portfolio-dev.openai.azure.com/' }
            { name: 'AZURE_OPENAI_KEY', secretRef: 'aoai-key' }
          ]
        }
      ]
      scale: { minReplicas: 1, maxReplicas: 5 }
    }
  }
}

output gatewayUrl string = 'https://${gatewayApp.properties.configuration.ingress.fqdn}'
```

Deploy:
```bash
az deployment group create \
  --resource-group rg-llm-observatory-dev \
  --template-file infra/bicep/main.bicep \
  --parameters envName=dev
```

---

## Step 4 — Terraform Equivalent

Create `infra/terraform/main.tf`:

```hcl
terraform {
  required_providers {
    azurerm = { source = "hashicorp/azurerm", version = "~> 3.0" }
  }
}

provider "azurerm" { features {} }

variable "env_name" { default = "dev" }
variable "location" { default = "eastus2" }
variable "rg_name"  { default = "rg-llm-observatory-dev" }

# Container Apps Environment
resource "azurerm_container_app_environment" "main" {
  name                = "cae-llm-observatory-${var.env_name}"
  resource_group_name = var.rg_name
  location            = var.location
  log_analytics_workspace_id = azurerm_log_analytics_workspace.main.id
}

resource "azurerm_log_analytics_workspace" "main" {
  name                = "law-llm-observatory-${var.env_name}"
  resource_group_name = var.rg_name
  location            = var.location
  sku                 = "PerGB2018"
}

resource "azurerm_key_vault" "main" {
  name                = "kv-obs-${var.env_name}"
  resource_group_name = var.rg_name
  location            = var.location
  tenant_id           = data.azurerm_client_config.current.tenant_id
  sku_name            = "standard"
  enable_rbac_authorization = true
}

data "azurerm_client_config" "current" {}

resource "azurerm_container_app" "gateway" {
  name                         = "ca-gateway-${var.env_name}"
  container_app_environment_id = azurerm_container_app_environment.main.id
  resource_group_name          = var.rg_name
  revision_mode                = "Single"

  identity { type = "SystemAssigned" }

  template {
    container {
      name   = "gateway"
      image  = "acrportfoliodev.azurecr.io/llm-gateway:latest"
      cpu    = 0.5
      memory = "1Gi"
      env {
        name  = "LLM_PROVIDER"
        value = "azure"
      }
      env {
        name  = "AZURE_OPENAI_ENDPOINT"
        value = "https://aoai-portfolio-dev.openai.azure.com/"
      }
    }
    min_replicas = 1
    max_replicas = 5
  }

  ingress {
    external_enabled = true
    target_port      = 8001
  }
}

output "gateway_url" {
  value = "https://${azurerm_container_app.gateway.ingress[0].fqdn}"
}
```

```bash
cd infra/terraform
terraform init
terraform plan
terraform apply
```

---

## Step 5 — GitHub Actions CI/CD

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy LLM Observatory

on:
  push:
    branches: [main]

env:
  ACR_NAME: acrportfoliodev
  RG_NAME: rg-llm-observatory-dev
  APP_NAME: ca-gateway-dev

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Azure Login
        uses: azure/login@v1
        with:
          creds: ${{ secrets.AZURE_CREDENTIALS }}

      - name: Build and push to ACR
        run: |
          az acr login --name $ACR_NAME
          docker build -t $ACR_NAME.azurecr.io/llm-gateway:${{ github.sha }} .
          docker push $ACR_NAME.azurecr.io/llm-gateway:${{ github.sha }}

      - name: Deploy to Container Apps
        run: |
          az containerapp update \
            --name $APP_NAME \
            --resource-group $RG_NAME \
            --image $ACR_NAME.azurecr.io/llm-gateway:${{ github.sha }}

      - name: Get App URL
        run: |
          az containerapp show \
            --name $APP_NAME \
            --resource-group $RG_NAME \
            --query properties.configuration.ingress.fqdn \
            --output tsv
```

Setup Azure credentials secret:
```bash
az ad sp create-for-rbac \
  --name "github-actions-portfolio" \
  --role contributor \
  --scopes /subscriptions/{SUBSCRIPTION_ID}/resourceGroups/rg-llm-observatory-dev \
  --json-auth
# Paste output as AZURE_CREDENTIALS secret in GitHub repo settings
```

---

---

# PART 4: PROJECT 2 — MULTI-AGENT BPA (AZURE)

## What changes from base guide

| Component | Base Guide | Azure Version |
|-----------|-----------|---------------|
| LLM calls | OpenAI | Azure OpenAI |
| Task queue | Redis | Azure Service Bus |
| State storage | PostgreSQL | Azure Database for PostgreSQL Flex |
| Deployment | Docker Compose | Azure Container Apps |
| Auth | None | Entra ID |

---

## Azure Architecture

```
[Webhook / Schedule Trigger]
          ↓
[Supervisor Agent - Container App]
          ↓
[Azure Service Bus Queue]  ← distributes tasks to specialist agents
    ↓           ↓           ↓
[Research]  [Writer]  [CRM Agent]  ← each its own Container App
          ↓
[Azure PostgreSQL] (state + audit log)
[App Insights] (agent execution tracing)
```

---

## Step 1 — Replace Redis queue with Azure Service Bus

```bash
uv pip install azure-servicebus
```

Create Azure Service Bus:
```bash
az servicebus namespace create \
  --name sb-bpa-dev \
  --resource-group rg-multi-agent-dev \
  --location eastus2 \
  --sku Basic

az servicebus queue create \
  --name agent-tasks \
  --namespace-name sb-bpa-dev \
  --resource-group rg-multi-agent-dev
```

Create `storage/service_bus.py`:

```python
import os
import json
from azure.servicebus import ServiceBusClient, ServiceBusMessage

CONN_STR = os.getenv("AZURE_SERVICE_BUS_CONNECTION_STRING")
QUEUE_NAME = "agent-tasks"

def send_task(task: dict):
    with ServiceBusClient.from_connection_string(CONN_STR) as client:
        with client.get_queue_sender(QUEUE_NAME) as sender:
            msg = ServiceBusMessage(json.dumps(task))
            sender.send_messages(msg)

def receive_tasks(max_count: int = 5):
    tasks = []
    with ServiceBusClient.from_connection_string(CONN_STR) as client:
        with client.get_queue_receiver(QUEUE_NAME, max_wait_time=5) as receiver:
            for msg in receiver.receive_messages(max_message_count=max_count):
                tasks.append(json.loads(str(msg)))
                receiver.complete_message(msg)
    return tasks
```

---

## Step 2 — Add Entra ID auth to the trigger API

Update `api/main.py`:

```python
from fastapi import FastAPI, Depends
from shared.auth import get_current_user, require_role

app = FastAPI()

@app.post("/process-lead")
async def process_lead(
    lead: LeadInput,
    user=Depends(require_role("AI.User"))  # must have AI.User role in Entra ID
):
    # Log who triggered the workflow
    print(f"Workflow triggered by: {user['email']}")
    # ... rest of code
```

---

## Step 3 — Bicep for Multi-Agent BPA

Create `infra/bicep/main.bicep`:

```bicep
param envName string = 'dev'
param location string = resourceGroup().location

// Service Bus
resource serviceBus 'Microsoft.ServiceBus/namespaces@2022-10-01-preview' = {
  name: 'sb-bpa-${envName}'
  location: location
  sku: { name: 'Basic' }
}

resource sbQueue 'Microsoft.ServiceBus/namespaces/queues@2022-10-01-preview' = {
  parent: serviceBus
  name: 'agent-tasks'
  properties: { maxDeliveryCount: 3 }
}

// PostgreSQL Flexible Server
resource postgres 'Microsoft.DBforPostgreSQL/flexibleServers@2023-03-01-preview' = {
  name: 'psql-bpa-${envName}'
  location: location
  sku: { name: 'Standard_B1ms', tier: 'Burstable' }
  properties: {
    administratorLogin: 'pgadmin'
    administratorLoginPassword: 'REPLACE_WITH_KV_REF'  // use Key Vault ref in production
    version: '15'
    storage: { storageSizeGB: 32 }
    backup: { backupRetentionDays: 7 }
  }
}

// Container Apps Environment (reuse or create)
resource cae 'Microsoft.App/managedEnvironments@2023-05-01' = {
  name: 'cae-bpa-${envName}'
  location: location
  properties: {}
}

// Supervisor Agent
resource supervisorApp 'Microsoft.App/containerApps@2023-05-01' = {
  name: 'ca-supervisor-${envName}'
  location: location
  identity: { type: 'SystemAssigned' }
  properties: {
    managedEnvironmentId: cae.id
    configuration: {
      ingress: { external: true, targetPort: 8002 }
    }
    template: {
      containers: [{
        name: 'supervisor'
        image: 'acrportfoliodev.azurecr.io/bpa-supervisor:latest'
        resources: { cpu: json('1.0'), memory: '2Gi' }
        env: [
          { name: 'LLM_PROVIDER', value: 'azure' }
          { name: 'AZURE_SERVICE_BUS_CONNECTION_STRING', secretRef: 'sb-conn' }
        ]
      }]
      scale: { minReplicas: 1, maxReplicas: 3 }
    }
  }
}
```

---

---

# PART 5: PROJECT 3 — LLM FINE-TUNING PIPELINE (AZURE)

## What changes from base guide

| Component | Base Guide | Azure Version |
|-----------|-----------|---------------|
| Training compute | RunPod / local GPU | Azure Machine Learning Compute Clusters |
| Experiment tracking | Weights & Biases | AzureML Experiments + W&B (both) |
| Model storage | Local filesystem | Azure Blob Storage |
| Serving | vLLM local | Azure ML Online Endpoints |

---

## Azure Architecture

```
[Raw Data] → [Azure Blob Storage]
                    ↓
[AzureML Pipeline Job]
    ↓ data_prep step → ↓ training step (GPU cluster) → ↓ eval step
                    ↓
[AzureML Model Registry]
                    ↓
[AzureML Online Endpoint] (vLLM serving)
                    ↓
[Azure OpenAI] (for inference after deployment)
```

---

## Step 1 — Install AzureML SDK

```bash
uv pip install azure-ai-ml azure-identity
```

---

## Step 2 — Create AzureML Workspace

```bash
az ml workspace create \
  --name aml-finetune-dev \
  --resource-group rg-finetune-dev \
  --location eastus2

az ml compute create \
  --name gpu-cluster \
  --type AmlCompute \
  --size Standard_NC6s_v3 \  # 1x V100 GPU — good for 7B models
  --min-instances 0 \
  --max-instances 2 \
  --workspace-name aml-finetune-dev \
  --resource-group rg-finetune-dev
```

---

## Step 3 — AzureML Training Job

Create `training/azure_job.py`:

```python
from azure.ai.ml import MLClient, command, Input, Output
from azure.ai.ml.entities import Environment, BuildContext
from azure.identity import DefaultAzureCredential
import os

def submit_training_job():
    ml_client = MLClient(
        credential=DefaultAzureCredential(),
        subscription_id=os.getenv("AZURE_SUBSCRIPTION_ID"),
        resource_group_name="rg-finetune-dev",
        workspace_name="aml-finetune-dev"
    )

    # Define the training job
    job = command(
        code="./",                          # upload entire project directory
        command="python training/train.py \
                 --data_path ${{inputs.training_data}} \
                 --output_dir ${{outputs.model_output}}",
        inputs={
            "training_data": Input(type="uri_folder", path="azureml://datastores/workspaceblobstore/paths/training_data/")
        },
        outputs={
            "model_output": Output(type="uri_folder")
        },
        environment="azureml:AzureML-ACPT-pytorch-2.0-cuda11.7:latest",  # pre-built GPU env
        compute="gpu-cluster",
        experiment_name="llm-qlora-finetune",
        display_name="legal-domain-qlora-v1",
        instance_count=1
    )

    returned_job = ml_client.jobs.create_or_update(job)
    print(f"Job submitted: {returned_job.name}")
    print(f"Studio URL: {returned_job.studio_url}")
    return returned_job

if __name__ == "__main__":
    submit_training_job()
```

---

## Step 4 — Upload training data to Blob Storage

```bash
# Create storage account
az storage account create \
  --name stamlfinetune \
  --resource-group rg-finetune-dev \
  --location eastus2 \
  --sku Standard_LRS

# Upload training data
az storage blob upload-batch \
  --destination training-data \
  --source data_prep/processed \
  --account-name stamlfinetune
```

In code (`data_prep/upload.py`):

```python
from azure.storage.blob import BlobServiceClient
import os

def upload_training_data(local_dir: str, container: str = "training-data"):
    client = BlobServiceClient.from_connection_string(
        os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    )
    container_client = client.get_container_client(container)

    import pathlib
    for file in pathlib.Path(local_dir).glob("*.jsonl"):
        with open(file, "rb") as f:
            container_client.upload_blob(name=file.name, data=f, overwrite=True)
        print(f"Uploaded: {file.name}")
```

---

## Step 5 — Register and Deploy Model

```python
from azure.ai.ml import MLClient
from azure.ai.ml.entities import Model, ManagedOnlineEndpoint, ManagedOnlineDeployment
from azure.ai.ml.constants import AssetTypes
from azure.identity import DefaultAzureCredential

ml_client = MLClient(
    credential=DefaultAzureCredential(),
    subscription_id=os.getenv("AZURE_SUBSCRIPTION_ID"),
    resource_group_name="rg-finetune-dev",
    workspace_name="aml-finetune-dev"
)

# Register model
model = ml_client.models.create_or_update(Model(
    name="legal-qlora-phi2",
    path="azureml://jobs/{JOB_NAME}/outputs/model_output",
    type=AssetTypes.CUSTOM_MODEL,
    description="QLoRA fine-tuned Phi-2 on legal domain data"
))

# Create online endpoint
endpoint = ml_client.online_endpoints.begin_create_or_update(
    ManagedOnlineEndpoint(name="legal-llm-endpoint", auth_mode="key")
).result()

# Deploy model to endpoint
deployment = ml_client.online_deployments.begin_create_or_update(
    ManagedOnlineDeployment(
        name="legal-v1",
        endpoint_name="legal-llm-endpoint",
        model=model,
        instance_type="Standard_NC6s_v3",
        instance_count=1
    )
).result()

print(f"Endpoint: {endpoint.scoring_uri}")
```

---

---

# PART 6: PROJECT 4 — DOMAIN AI COPILOT (AZURE)

## What changes from base guide

| Component | Base Guide | Azure Version |
|-----------|-----------|---------------|
| Vector DB | Qdrant | Switchable via abstraction layer (VECTOR_DB env var) |
| Embeddings | OpenAI | Azure OpenAI (same model, Azure endpoint) |
| Auth | None | Entra ID |
| Deployment | Docker | Azure Container Apps |
| Secrets | .env | Azure Key Vault |

---

## Step 1 — Use the abstraction layer for ingestion

Update `ingestion/ingest.py` — replace direct Qdrant calls:

```python
import sys
sys.path.insert(0, "..")
from shared.vector_store import get_vector_store
from shared.llm_client import get_llm_client, get_model_name

store = get_vector_store()    # VECTOR_DB=azure_search or qdrant or ...
client = get_llm_client()

def embed_texts(texts: list) -> list:
    response = client.embeddings.create(
        model=get_model_name("embed"),
        input=texts
    )
    return [item.embedding for item in response.data]

def ingest_pdf(pdf_path: str, metadata: dict = None, collection: str = "domain-copilot"):
    store.create_collection(collection)
    # ... parse PDF, chunk, embed, then:
    store.upsert(
        collection_name=collection,
        ids=chunk_ids,
        vectors=embeddings,
        payloads=[{"text": chunk, "source": filename, **(metadata or {})}
                  for chunk in chunks]
    )
```

---

## Step 2 — Provision Azure AI Search (for enterprise demo)

```bash
az search service create \
  --name srch-copilot-dev \
  --resource-group rg-copilot-dev \
  --location eastus2 \
  --sku Basic

# Get admin key
az search admin-key show \
  --service-name srch-copilot-dev \
  --resource-group rg-copilot-dev
```

Add to `.env`:
```
VECTOR_DB=azure_search
AZURE_SEARCH_ENDPOINT=https://srch-copilot-dev.search.windows.net
AZURE_SEARCH_KEY=your_admin_key
```

Switch to local Qdrant:
```
VECTOR_DB=qdrant
QDRANT_URL=http://localhost:6333
```

---

## Step 3 — Container Apps Bicep

```bicep
param envName string = 'dev'
param location string = resourceGroup().location

resource cae 'Microsoft.App/managedEnvironments@2023-05-01' = {
  name: 'cae-copilot-${envName}'
  location: location
  properties: {}
}

resource copilotApp 'Microsoft.App/containerApps@2023-05-01' = {
  name: 'ca-copilot-${envName}'
  location: location
  identity: { type: 'SystemAssigned' }
  properties: {
    managedEnvironmentId: cae.id
    configuration: {
      ingress: { external: true, targetPort: 8000 }
      secrets: [
        { name: 'aoai-key', keyVaultUrl: 'https://kv-portfolio-dev.vault.azure.net/secrets/azure-openai-key', identity: 'system' }
        { name: 'search-key', keyVaultUrl: 'https://kv-portfolio-dev.vault.azure.net/secrets/azure-search-key', identity: 'system' }
      ]
    }
    template: {
      containers: [{
        name: 'copilot'
        image: 'acrportfoliodev.azurecr.io/domain-copilot:latest'
        resources: { cpu: json('1.0'), memory: '2Gi' }
        env: [
          { name: 'LLM_PROVIDER', value: 'azure' }
          { name: 'VECTOR_DB', value: 'azure_search' }
          { name: 'AZURE_OPENAI_KEY', secretRef: 'aoai-key' }
          { name: 'AZURE_SEARCH_KEY', secretRef: 'search-key' }
          { name: 'AZURE_TENANT_ID', value: 'your-tenant-id' }
          { name: 'AZURE_CLIENT_ID', value: 'your-client-id' }
        ]
      }]
      scale: { minReplicas: 1, maxReplicas: 10 }
    }
  }
}
```

---

---

# PART 7: PROJECT 5 — CODE REVIEW AGENT (AZURE)

## What changes from base guide

| Component | Base Guide | Azure Version |
|-----------|-----------|---------------|
| LLM calls | OpenAI | Azure OpenAI |
| Webhook server | Local FastAPI | Azure Container Apps |
| Background jobs | BackgroundTasks | Azure Service Bus |
| Auth | GitHub token only | GitHub token + Entra ID (admin endpoints) |

---

## Step 1 — Update agents to use Azure OpenAI

In `agents/security_agent.py` and `agents/logic_agent.py`:

```python
import sys
sys.path.insert(0, "..")
from shared.llm_client import get_llm_client, get_model_name

client = get_llm_client()

def security_review(filename, language, code):
    response = client.chat.completions.create(
        model=get_model_name("chat"),
        messages=[{"role": "user", "content": SECURITY_PROMPT.format(...)}],
        response_format={"type": "json_object"},
        temperature=0
    )
    # ... rest unchanged
```

---

## Step 2 — Bicep for Code Review Agent

```bicep
param envName string = 'dev'
param location string = resourceGroup().location

resource cae 'Microsoft.App/managedEnvironments@2023-05-01' = {
  name: 'cae-codereview-${envName}'
  location: location
  properties: {}
}

resource codeReviewApp 'Microsoft.App/containerApps@2023-05-01' = {
  name: 'ca-codereview-${envName}'
  location: location
  identity: { type: 'SystemAssigned' }
  properties: {
    managedEnvironmentId: cae.id
    configuration: {
      ingress: {
        external: true
        targetPort: 8003
        // GitHub webhooks come from external — must be externally accessible
      }
      secrets: [
        { name: 'github-token', keyVaultUrl: 'https://kv-portfolio-dev.vault.azure.net/secrets/github-token', identity: 'system' }
        { name: 'aoai-key', keyVaultUrl: 'https://kv-portfolio-dev.vault.azure.net/secrets/azure-openai-key', identity: 'system' }
      ]
    }
    template: {
      containers: [{
        name: 'code-review'
        image: 'acrportfoliodev.azurecr.io/code-review-agent:latest'
        resources: { cpu: json('1.0'), memory: '2Gi' }
        env: [
          { name: 'LLM_PROVIDER', value: 'azure' }
          { name: 'GITHUB_TOKEN', secretRef: 'github-token' }
          { name: 'AZURE_OPENAI_KEY', secretRef: 'aoai-key' }
        ]
      }]
      scale: { minReplicas: 1, maxReplicas: 5 }
    }
  }
}

output webhookUrl string = 'https://${codeReviewApp.properties.configuration.ingress.fqdn}/webhook'
// Set this URL as the webhook URL in your GitHub repo settings
```

---

---

# PART 8: PROJECT 6 — DATA COPILOT (AZURE)

## What changes from base guide

| Component | Base Guide | Azure Version |
|-----------|-----------|---------------|
| Database | DuckDB (local) | Azure Database for PostgreSQL Flex |
| LLM calls | OpenAI | Azure OpenAI |
| Cache | None | Azure Cache for Redis |
| Deployment | Streamlit local | Azure Container Apps |
| Auth | None | Entra ID |

---

## Step 1 — Provision Azure PostgreSQL

```bash
az postgres flexible-server create \
  --name psql-datacopilot-dev \
  --resource-group rg-datacopilot-dev \
  --location eastus2 \
  --sku-name Standard_B1ms \
  --tier Burstable \
  --admin-user pgadmin \
  --admin-password "ComplexPassword123!" \
  --yes

# Create database
az postgres flexible-server db create \
  --database-name sales_db \
  --server-name psql-datacopilot-dev \
  --resource-group rg-datacopilot-dev
```

---

## Step 2 — Provision Azure Cache for Redis

```bash
az redis create \
  --name redis-datacopilot-dev \
  --resource-group rg-datacopilot-dev \
  --location eastus2 \
  --sku Basic \
  --vm-size C0
```

---

## Step 3 — Add Redis query caching

Update `cache/redis_cache.py`:

```python
import os
import json
import hashlib
import redis

REDIS_URL = os.getenv("AZURE_REDIS_URL")  # from Azure Cache for Redis
REDIS_PASSWORD = os.getenv("AZURE_REDIS_PASSWORD")
CACHE_TTL = 3600  # 1 hour

def get_redis():
    return redis.StrictRedis(
        host=REDIS_URL,
        port=6380,           # Azure Redis uses SSL on 6380
        password=REDIS_PASSWORD,
        ssl=True,
        decode_responses=True
    )

def get_cached_result(question: str, schema_hash: str):
    key = hashlib.md5(f"{question}:{schema_hash}".encode()).hexdigest()
    r = get_redis()
    cached = r.get(key)
    return json.loads(cached) if cached else None

def cache_result(question: str, schema_hash: str, result: dict):
    key = hashlib.md5(f"{question}:{schema_hash}".encode()).hexdigest()
    r = get_redis()
    r.setex(key, CACHE_TTL, json.dumps(result))
```

---

## Step 4 — Update SQL executor to use Azure PostgreSQL

```python
import os
import sqlalchemy

def get_db_engine():
    db_mode = os.getenv("DB_MODE", "duckdb")   # "duckdb" (local) or "postgres" (azure)

    if db_mode == "postgres":
        host = os.getenv("AZURE_POSTGRES_HOST")
        password = os.getenv("AZURE_POSTGRES_PASSWORD")
        return sqlalchemy.create_engine(
            f"postgresql://pgadmin:{password}@{host}/sales_db?sslmode=require"
        )
    else:
        import duckdb
        return duckdb.connect("demo_data/sales.db", read_only=True)
```

---

---

# PART 9: PROJECT 7 — ENTERPRISE RAG (AZURE + AKS)

> This is the most complex deployment. Uses AKS for production-grade multi-tenant workloads.

## What changes from base guide

| Component | Base Guide | Azure Version |
|-----------|-----------|---------------|
| Vector DB | Qdrant (Docker) | Azure AI Search (primary) + Qdrant/others via abstraction |
| Document storage | Local filesystem | Azure Blob Storage |
| Auth | Simple email token | Entra ID + App Roles |
| Deployment | Docker Compose | AKS (Kubernetes) |
| Queue | Celery + Redis | Azure Service Bus |
| Database | PostgreSQL (Docker) | Azure PostgreSQL Flexible Server |

---

## Azure Architecture

```
[Client - Entra ID token] → [AKS Ingress (NGINX)]
                                    ↓
                         [FastAPI - Auth + Query API]
                         (validates Entra ID JWT)
                                    ↓
              ┌────────────────────────────────────┐
              ↓                                    ↓
[Azure AI Search]                       [Azure Blob Storage]
(vectors + metadata + RBAC filter)      (raw documents)
              ↓
[Azure OpenAI] (generation)
              ↓
[App Insights] (audit + monitoring)
              ↓
[Response with citations + access log]

Ingestion path:
[Azure Service Bus] → [Celery Workers on AKS] → [Parse → Embed → Index]
```

---

## Step 1 — Provision AKS Cluster

```bash
# Create AKS cluster
az aks create \
  --resource-group rg-enterprise-rag-dev \
  --name aks-rag-dev \
  --node-count 2 \
  --node-vm-size Standard_D4s_v3 \
  --enable-managed-identity \
  --attach-acr acrportfoliodev \
  --generate-ssh-keys \
  --location eastus2

# Get credentials
az aks get-credentials \
  --resource-group rg-enterprise-rag-dev \
  --name aks-rag-dev

# Verify
kubectl get nodes
```

---

## Step 2 — Kubernetes manifests

Create `infra/k8s/api-deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: rag-api
  namespace: rag-prod
spec:
  replicas: 2
  selector:
    matchLabels:
      app: rag-api
  template:
    metadata:
      labels:
        app: rag-api
    spec:
      containers:
        - name: rag-api
          image: acrportfoliodev.azurecr.io/enterprise-rag:latest
          ports:
            - containerPort: 8004
          env:
            - name: LLM_PROVIDER
              value: azure
            - name: VECTOR_DB
              value: azure_search
            - name: AZURE_TENANT_ID
              valueFrom:
                secretKeyRef:
                  name: azure-secrets
                  key: tenant-id
            - name: AZURE_CLIENT_ID
              valueFrom:
                secretKeyRef:
                  name: azure-secrets
                  key: client-id
            - name: AZURE_OPENAI_KEY
              valueFrom:
                secretKeyRef:
                  name: azure-secrets
                  key: openai-key
          resources:
            requests:
              memory: "1Gi"
              cpu: "500m"
            limits:
              memory: "2Gi"
              cpu: "1000m"
          livenessProbe:
            httpGet:
              path: /health
              port: 8004
            initialDelaySeconds: 30
            periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: rag-api-svc
  namespace: rag-prod
spec:
  selector:
    app: rag-api
  ports:
    - port: 80
      targetPort: 8004
  type: ClusterIP
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: rag-ingress
  namespace: rag-prod
  annotations:
    kubernetes.io/ingress.class: nginx
spec:
  rules:
    - host: rag-api.yourdomain.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: rag-api-svc
                port:
                  number: 80
```

Create `infra/k8s/worker-deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: rag-worker
  namespace: rag-prod
spec:
  replicas: 2
  selector:
    matchLabels:
      app: rag-worker
  template:
    metadata:
      labels:
        app: rag-worker
    spec:
      containers:
        - name: worker
          image: acrportfoliodev.azurecr.io/enterprise-rag:latest
          command: ["celery", "-A", "workers.celery_app", "worker", "--loglevel=info"]
          env:
            - name: VECTOR_DB
              value: azure_search
            - name: AZURE_SERVICE_BUS_CONNECTION_STRING
              valueFrom:
                secretKeyRef:
                  name: azure-secrets
                  key: service-bus-conn
          resources:
            requests:
              memory: "2Gi"
              cpu: "1000m"
```

Deploy:
```bash
kubectl create namespace rag-prod

# Create secrets
kubectl create secret generic azure-secrets \
  --from-literal=tenant-id="$AZURE_TENANT_ID" \
  --from-literal=client-id="$AZURE_CLIENT_ID" \
  --from-literal=openai-key="$AZURE_OPENAI_KEY" \
  --from-literal=service-bus-conn="$AZURE_SERVICE_BUS_CONNECTION_STRING" \
  --namespace rag-prod

kubectl apply -f infra/k8s/
kubectl get pods -n rag-prod   # verify all running
```

---

## Step 3 — Full Terraform for Enterprise RAG

Create `infra/terraform/main.tf`:

```hcl
terraform {
  required_providers {
    azurerm = { source = "hashicorp/azurerm", version = "~> 3.0" }
  }
  backend "azurerm" {
    resource_group_name  = "rg-tfstate"
    storage_account_name = "sttfstateportfolio"
    container_name       = "tfstate"
    key                  = "enterprise-rag.tfstate"
  }
}

provider "azurerm" { features {} }

variable "env"      { default = "dev" }
variable "location" { default = "eastus2" }
variable "rg_name"  { default = "rg-enterprise-rag-dev" }

data "azurerm_client_config" "current" {}

# AKS
resource "azurerm_kubernetes_cluster" "main" {
  name                = "aks-rag-${var.env}"
  resource_group_name = var.rg_name
  location            = var.location
  dns_prefix          = "aks-rag-${var.env}"

  default_node_pool {
    name       = "default"
    node_count = 2
    vm_size    = "Standard_D4s_v3"
  }

  identity { type = "SystemAssigned" }

  tags = { environment = var.env }
}

# Azure AI Search
resource "azurerm_search_service" "main" {
  name                = "srch-rag-${var.env}"
  resource_group_name = var.rg_name
  location            = var.location
  sku                 = "basic"
}

# PostgreSQL Flexible Server
resource "azurerm_postgresql_flexible_server" "main" {
  name                   = "psql-rag-${var.env}"
  resource_group_name    = var.rg_name
  location               = var.location
  version                = "15"
  administrator_login    = "pgadmin"
  administrator_password = var.postgres_password
  storage_mb             = 32768
  sku_name               = "B_Standard_B1ms"
  backup_retention_days  = 7
}

variable "postgres_password" {
  sensitive = true  # pass via TF_VAR_postgres_password env var
}

# Service Bus
resource "azurerm_servicebus_namespace" "main" {
  name                = "sb-rag-${var.env}"
  resource_group_name = var.rg_name
  location            = var.location
  sku                 = "Standard"
}

resource "azurerm_servicebus_queue" "ingestion" {
  name         = "document-ingestion"
  namespace_id = azurerm_servicebus_namespace.main.id
}

# Blob Storage
resource "azurerm_storage_account" "main" {
  name                     = "strag${var.env}docs"
  resource_group_name      = var.rg_name
  location                 = var.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
}

resource "azurerm_storage_container" "documents" {
  name                  = "documents"
  storage_account_name  = azurerm_storage_account.main.name
  container_access_type = "private"
}

# Key Vault
resource "azurerm_key_vault" "main" {
  name                = "kv-rag-${var.env}"
  resource_group_name = var.rg_name
  location            = var.location
  tenant_id           = data.azurerm_client_config.current.tenant_id
  sku_name            = "standard"
  enable_rbac_authorization = true
}

# Application Insights
resource "azurerm_application_insights" "main" {
  name                = "appi-rag-${var.env}"
  resource_group_name = var.rg_name
  location            = var.location
  workspace_id        = azurerm_log_analytics_workspace.main.id
  application_type    = "web"
}

resource "azurerm_log_analytics_workspace" "main" {
  name                = "law-rag-${var.env}"
  resource_group_name = var.rg_name
  location            = var.location
  sku                 = "PerGB2018"
}

# Outputs
output "aks_kube_config" {
  value     = azurerm_kubernetes_cluster.main.kube_config_raw
  sensitive = true
}
output "search_endpoint" {
  value = "https://${azurerm_search_service.main.name}.search.windows.net"
}
output "app_insights_connection_string" {
  value     = azurerm_application_insights.main.connection_string
  sensitive = true
}
```

```bash
# Initialize with remote state
terraform init
TF_VAR_postgres_password="YourPassword123!" terraform apply
```

---

---

# APPENDIX A: PROJECT-TO-AZURE-SERVICE MAPPING

| Project | Container Compute | Vector DB | Relational DB | Queue | Monitoring | IaC |
|---------|------------------|-----------|---------------|-------|-----------|-----|
| LLM Observatory | Container Apps | — | Cosmos DB | — | App Insights | Bicep |
| Multi-Agent BPA | Container Apps | — | PostgreSQL Flex | Service Bus | App Insights | Bicep |
| Fine-Tuning Pipeline | AzureML + AKS | — | Blob Storage | — | AzureML + W&B | Bicep |
| Domain Copilot | Container Apps | AI Search + switchable | PostgreSQL Flex | — | App Insights | Bicep |
| Code Review Agent | Container Apps | — | PostgreSQL Flex | Service Bus | App Insights | Bicep |
| Data Copilot | Container Apps | — | PostgreSQL Flex | — | App Insights | Bicep |
| Enterprise RAG | AKS | AI Search + switchable | PostgreSQL Flex | Service Bus | Azure Monitor | Terraform |

---

# APPENDIX B: LOCAL DEV → AZURE PROD MAPPING

When developing locally, use these equivalents:

| Azure Service | Local Equivalent | Switch via |
|--------------|-----------------|-----------|
| Azure OpenAI | OpenAI API | `LLM_PROVIDER=openai` |
| Azure AI Search | Qdrant (Docker) | `VECTOR_DB=qdrant` |
| PostgreSQL Flex | PostgreSQL (Docker) | `DB_MODE=local` |
| Azure Cache for Redis | Redis (Docker) | `REDIS_URL=localhost:6379` |
| Service Bus | Redis (as queue) | `QUEUE_MODE=redis` |
| Key Vault | `.env` file | `AZURE_KEY_VAULT_URL` not set → reads env |
| Blob Storage | Local filesystem | `STORAGE_MODE=local` |
| App Insights | Console logging | `APPLICATIONINSIGHTS_CONNECTION_STRING` not set → skip |

---

# APPENDIX C: AZURE COST ESTIMATES (DEV TIER)

Running all 7 projects in Azure dev/demo tier:

| Service | SKU | Monthly Cost (approx) |
|---------|-----|----------------------|
| Azure OpenAI (GPT-4o) | Pay-per-use | $10–50 (depends on usage) |
| Azure OpenAI (embeddings) | Pay-per-use | $1–5 |
| Azure AI Search | Basic | $75 |
| Container Apps (7 apps) | Consumption | $20–40 |
| AKS (2 nodes) | Standard_D4s_v3 | $280 |
| PostgreSQL Flex | B1ms (2 instances) | $30 |
| Cosmos DB | Serverless | $5–20 |
| Redis Cache | C0 Basic | $55 |
| Service Bus | Standard | $10 |
| AzureML Compute | NC6s_v3 (spot, when training) | $5–20 |
| Blob Storage | LRS | $2–5 |
| App Insights | Pay-per-use | $5–15 |
| **Total** | | **~$500–600/month** |

> **Cost reduction tips:**
> - Turn off AKS node pools when not demoing (`az aks scale --node-count 0`)
> - Use Container Apps scale-to-zero for idle services
> - Use spot instances for AzureML training (`--priority Spot`)
> - Share one Azure OpenAI instance across all projects
> - Use Basic SKUs everywhere — upgrade only for client demos

---

*Document version: 2.0 — Azure Integration — May 2026*
*Companion to: AI_Portfolio_Build_Guide.md*
