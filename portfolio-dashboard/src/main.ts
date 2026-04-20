import { bootstrapApplication } from '@angular/platform-browser';
import { appConfig } from './app/app.config';
import { AppComponent } from './app/app';
import { environment } from './environments/environment';

// Set mock token in development
if (!environment.production && environment.mockToken) {
  localStorage.setItem(environment.tokenKey, environment.mockToken);
  console.log('🔐 Mock token set for development');
}

bootstrapApplication(AppComponent, appConfig).catch((err) => console.error(err));
