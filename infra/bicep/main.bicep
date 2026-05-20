targetScope = 'resourceGroup'

param location string = resourceGroup().location
param appName string = 'docint'
param environment string = 'dev'
param acrImageTag string = 'latest'
param docIntelligenceSku string = 'F0'

@secure()
param postgresAdminPassword string

var suffix = '${appName}-${environment}'
var acrName = take(replace('${suffix}acr', '-', ''), 50)
var logAnalyticsSharedKey = listKeys(resourceId('Microsoft.OperationalInsights/workspaces', '${suffix}-law'), '2020-08-01').primarySharedKey
var commonEnv = [
  {
    name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
    value: appInsights.outputs.connectionString
  }
  {
    name: 'DOCINT_DATABASE_BACKEND'
    value: 'postgres'
  }
  {
    name: 'DOCINT_DATABASE_URL'
    value: 'postgresql+psycopg://observatoryadmin:${postgresAdminPassword}@${postgres.outputs.fqdn}:5432/docint'
  }
  {
    name: 'AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT'
    value: docIntelligence.outputs.endpoint
  }
  {
    name: 'AZURE_BLOB_STORAGE_CONNECTION_STRING'
    value: blobStorage.outputs.connectionString
  }
  {
    name: 'AZURE_BLOB_CONTAINER_NAME'
    value: blobStorage.outputs.containerName
  }
  {
    name: 'ENABLE_LOCAL_OCR'
    value: 'false'
  }
]

module acr 'modules/acr.bicep' = {
  name: 'acr'
  params: {
    location: location
    acrName: acrName
  }
}

module appInsights 'modules/appinsights.bicep' = {
  name: 'appinsights'
  params: {
    location: location
    appInsightsName: '${suffix}-ai'
    workspaceName: '${suffix}-law'
  }
}

module postgres 'modules/postgres.bicep' = {
  name: 'postgres'
  params: {
    location: location
    serverName: '${suffix}-pg'
    adminPassword: postgresAdminPassword
  }
}

module blobStorage 'modules/blob-storage.bicep' = {
  name: 'blob-storage'
  params: {
    location: location
    storageAccountName: take(replace('${suffix}blob', '-', ''), 24)
    containerName: 'documents'
  }
}

module docIntelligence 'modules/document-intelligence.bicep' = {
  name: 'document-intelligence'
  params: {
    location: location
    serviceName: take(replace('${suffix}-docint', '-', ''), 63)
    sku: docIntelligenceSku
  }
}

module acaEnv 'modules/aca-environment.bicep' = {
  name: 'aca-env'
  params: {
    location: location
    environmentName: '${suffix}-env'
    logAnalyticsWorkspaceId: appInsights.outputs.workspaceId
    logAnalyticsSharedKey: logAnalyticsSharedKey
  }
}

module api 'modules/aca-app.bicep' = {
  name: 'api'
  params: {
    location: location
    appName: '${suffix}-api'
    environmentId: acaEnv.outputs.id
    imageName: '${acr.outputs.loginServer}/docint-workbench:${acrImageTag}'
    containerPort: 8005
    command: [
      'uvicorn'
      'docint_workbench.api:app'
      '--host'
      '0.0.0.0'
      '--port'
      '8005'
    ]
    env: commonEnv
  }
}

module dashboard 'modules/aca-app.bicep' = {
  name: 'dashboard'
  params: {
    location: location
    appName: '${suffix}-dashboard'
    environmentId: acaEnv.outputs.id
    imageName: '${acr.outputs.loginServer}/docint-workbench:${acrImageTag}'
    containerPort: 8512
    command: [
      'streamlit'
      'run'
      'dashboard/app.py'
      '--server.address'
      '0.0.0.0'
      '--server.port'
      '8512'
    ]
    env: commonEnv
  }
}

module queueWorker 'modules/aca-app.bicep' = {
  name: 'queue-worker'
  params: {
    location: location
    appName: '${suffix}-queue-worker'
    environmentId: acaEnv.outputs.id
    imageName: '${acr.outputs.loginServer}/docint-workbench:${acrImageTag}'
    containerPort: 0
    minReplicas: 0
    maxReplicas: 1
    command: [
      'python'
      'scripts/run_queue_worker.py'
      '--continuous'
    ]
    env: commonEnv
  }
}

module keyvault 'modules/keyvault.bicep' = {
  name: 'keyvault'
  params: {
    location: location
    keyVaultName: '${suffix}-kv'
    managedIdentityPrincipalId: api.outputs.principalId
  }
}

output apiUrl string = 'https://${api.outputs.fqdn}'
output dashboardUrl string = 'https://${dashboard.outputs.fqdn}'
output storageAccountName string = blobStorage.outputs.accountName
output documentIntelligenceEndpoint string = docIntelligence.outputs.endpoint
output keyVaultUri string = keyvault.outputs.uri
