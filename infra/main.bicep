// Bootstrap in the existing group. CD owns active revisions after initial creation.
param prefix string = 'sdd-3b-g8'
param location string = resourceGroup().location
param swaLocation string = location
param sqlLocation string = location
param existingWorkspaceCustomerId string = ''
param sqlAdminLogin string
@secure()
param sqlAdminPassword string
param bootstrapApps array = ['pantry', 'catalog']
param pantryImage string = 'mcr.microsoft.com/k8se/quickstart:latest'
param catalogImage string = 'mcr.microsoft.com/k8se/quickstart:latest'

resource workspace 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: '${prefix}-logs'
  location: location
  properties: {
    sku: { name: 'PerGB2018' }
    retentionInDays: 30
  }
}

resource environment 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: '${prefix}-env'
  location: location
  properties: {
    peerAuthentication: { mtls: { enabled: false } }
    peerTrafficConfiguration: { encryption: { enabled: false } }
    workloadProfiles: [
      { name: 'Consumption', workloadProfileType: 'Consumption' }
    ]
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: empty(existingWorkspaceCustomerId) ? workspace.properties.customerId : existingWorkspaceCustomerId
        sharedKey: workspace.listKeys().primarySharedKey
      }
    }
  }
}

resource apps 'Microsoft.App/containerApps@2024-03-01' = [for service in bootstrapApps: {
  name: '${prefix}-${service}'
  location: location
  properties: {
    environmentId: environment.id
    workloadProfileName: 'Consumption'
    configuration: {
      activeRevisionsMode: 'Single'
      ingress: { external: true, targetPort: 80, transport: 'auto' }
    }
    template: {
      containers: [
        {
          name: '${prefix}-${service}'
          image: service == 'pantry' ? pantryImage : catalogImage
          resources: { cpu: json('0.25'), memory: '0.5Gi' }
        }
      ]
      scale: { minReplicas: 0, maxReplicas: 1 }
    }
  }
}]

resource server 'Microsoft.Sql/servers@2023-08-01' = {
  name: '${prefix}-sql'
  location: sqlLocation
  properties: {
    administratorLogin: sqlAdminLogin
    administratorLoginPassword: sqlAdminPassword
    minimalTlsVersion: '1.2'
    version: '12.0'
    publicNetworkAccess: 'Enabled'
  }
}
resource firewall 'Microsoft.Sql/servers/firewallRules@2023-08-01' = {
  parent: server
  name: 'AllowAzureServices'
  properties: { startIpAddress: '0.0.0.0', endIpAddress: '0.0.0.0' }
}
resource databases 'Microsoft.Sql/servers/databases@2023-08-01' = [for service in ['pantry', 'catalog']: {
  parent: server
  name: '${prefix}-${service}-db'
  location: sqlLocation
  sku: { name: 'GP_S_Gen5', tier: 'GeneralPurpose', family: 'Gen5', capacity: 1 }
  properties: {
    minCapacity: json('0.5')
    autoPauseDelay: 15
    maxSizeBytes: 2147483648
    requestedBackupStorageRedundancy: 'Local'
  }
}]
// Preserve the deployed site's content delivery and authentication settings after bootstrap.
@onlyIfNotExists()
resource frontend 'Microsoft.Web/staticSites@2025-03-01' = {
  name: '${prefix}-ui'
  location: swaLocation
  sku: { name: 'Free', tier: 'Free' }
  properties: {
    provider: 'None'
  }
}
