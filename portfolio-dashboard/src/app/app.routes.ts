import { Routes } from '@angular/router';

export const routes: Routes = [
  {
    path: '',
    loadComponent: () => import('./features/dashboard/dashboard').then((m) => m.DashboardComponent),
    title: 'Dashboard',
  },
  {
    path: 'holdings',
    loadComponent: () => import('./features/holdings/holdings').then((m) => m.HoldingsComponent),
    title: 'Holdings',
  },
  {
    path: 'ticker-detail',
    loadComponent: () =>
      import('./features/ticker-details/ticker-details').then((m) => m.TickerDetailsComponent),
    title: 'Ticker Detail',
  },
];
