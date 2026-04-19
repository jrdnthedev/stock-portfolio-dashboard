import { Routes } from '@angular/router';

export const routes: Routes = [
  {
    path: '',
    loadComponent: () =>
      import('./features/dashboard/dashboard.component').then((m) => m.DashboardComponent),
    title: 'Dashboard',
  },
  {
    path: 'holdings',
    loadComponent: () =>
      import('./features/holdings/holdings.component').then((m) => m.HoldingsComponent),
    title: 'Holdings',
  },
  {
    path: 'ticker-detail',
    loadComponent: () =>
      import('./features/ticker-details/ticker-details.component').then(
        (m) => m.TickerDetailsComponent
      ),
    title: 'Ticker Detail',
  },
];
