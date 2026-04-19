export const environment = {
  production: false,
  envName: 'development',

  // API Configuration
  apiUrl: 'http://localhost:8000',
  apiVersion: 'v1',

  // WebSocket Configuration
  wsUrl: 'ws://localhost:8000/ws',

  // Authentication
  tokenKey: 'jwt_token',
  refreshTokenKey: 'refresh_token',

  // Feature Flags
  enableLogging: true,
  enableDebugMode: true,

  // Cache settings
  cacheTimeout: 300000, // 5 minutes in milliseconds

  // WebSocket reconnection settings
  wsReconnectInterval: 5000, // 5 seconds
  wsMaxReconnectAttempts: 5,
};
