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
    'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJkZW1vX3VzZXIiLCJleHAiOjE3NzkyNDA2MDAsImlhdCI6MTc3NjY0ODYwMCwidHlwZSI6ImFjY2VzcyJ9.CBgCowDmnKbwPBecDKEogEutcQGtt7sRmPzzgn7heLU', // Valid JWT token for demo_user (expires in 30 days)

  // Feature Flags
  enableLogging: true,
  enableDebugMode: true,

  // Cache settings
  cacheTimeout: 300000, // 5 minutes in milliseconds

  // WebSocket reconnection settings
  wsReconnectInterval: 5000, // 5 seconds
  wsMaxReconnectAttempts: 5,
};
