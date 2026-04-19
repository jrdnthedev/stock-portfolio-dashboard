import { Component } from '@angular/core';
import { DataTableComponent } from '../../shared/components/data-table/data-table.component';
import { StatCardComponent } from '../../shared/components/stat-card/stat-card.component';
import { LineChartComponent } from '../../shared/components/line-chart/line-chart.component';

export interface TickerData {
  symbol: string;
  name: string;
  price: number;
  change: number;
  changePercent: number;
  volume: number;
  marketCap: string;
}

@Component({
  selector: 'app-dashboard',
  imports: [DataTableComponent, StatCardComponent, LineChartComponent],
  templateUrl: './dashboard.component.html',
  styleUrl: './dashboard.component.scss',
})
export class DashboardComponent {
  mockTickers: TickerData[] = [
    {
      symbol: 'AAPL',
      name: 'Apple Inc.',
      price: 178.25,
      change: 2.45,
      changePercent: 1.39,
      volume: 52847300,
      marketCap: '$2.85T',
    },
    {
      symbol: 'MSFT',
      name: 'Microsoft Corporation',
      price: 412.8,
      change: -1.2,
      changePercent: -0.29,
      volume: 24351200,
      marketCap: '$3.07T',
    },
    {
      symbol: 'GOOGL',
      name: 'Alphabet Inc.',
      price: 142.65,
      change: 3.15,
      changePercent: 2.26,
      volume: 28945600,
      marketCap: '$1.78T',
    },
    {
      symbol: 'TSLA',
      name: 'Tesla, Inc.',
      price: 238.45,
      change: -5.8,
      changePercent: -2.37,
      volume: 98234500,
      marketCap: '$757B',
    },
    {
      symbol: 'NVDA',
      name: 'NVIDIA Corporation',
      price: 785.3,
      change: 12.5,
      changePercent: 1.62,
      volume: 45678900,
      marketCap: '$1.94T',
    },
  ];
}
