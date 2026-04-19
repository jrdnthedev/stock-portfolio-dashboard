export const environment = {
  production: true,
  envName: 'production',

  // API Configuration
  apiUrl: 'https://your-production-api.com',
  apiVersion: 'v1',

  // WebSocket Configuration
  wsUrl: 'wss://your-production-api.com/ws',

  // Authentication
  tokenKey: 'jwt_token',
  refreshTokenKey: 'refresh_token',

  // Feature Flags
  enableLogging: false,
  enableDebugMode: false,

  // Cache settings
  cacheTimeout: 300000, // 5 minutes in milliseconds

  // WebSocket reconnection settings
  wsReconnectInterval: 5000, // 5 seconds
  wsMaxReconnectAttempts: 5,
};
