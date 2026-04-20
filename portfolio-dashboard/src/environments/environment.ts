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
  mockToken:
    'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0LXVzZXIiLCJleHAiOjk5OTk5OTk5OTl9.mock-signature', // Mock token for development

  // Feature Flags
  enableLogging: true,
  enableDebugMode: true,

  // Cache settings
  cacheTimeout: 300000, // 5 minutes in milliseconds

  // WebSocket reconnection settings
  wsReconnectInterval: 5000, // 5 seconds
  wsMaxReconnectAttempts: 5,
};
