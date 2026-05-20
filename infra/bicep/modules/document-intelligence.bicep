param location string
param serviceName string
param sku string = 'S0'

resource docIntelligence 'Microsoft.CognitiveServices/accounts@2023-05-01' = {
  name: serviceName
  location: location
  kind: 'FormRecognizer'
  sku: {
    name: sku
  }
  properties: {
    publicNetworkAccess: 'Enabled'
    disableLocalAuth: false
  }
}

output endpoint string = docIntelligence.properties.endpoint
output name string = docIntelligence.name
