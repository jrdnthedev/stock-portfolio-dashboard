import { Component, inject } from '@angular/core';
import { DataTableComponent } from '../../shared/components/data-table/data-table.component';
import { StatCardComponent } from '../../shared/components/stat-card/stat-card.component';
import { LineChartComponent } from '../../shared/components/line-chart/line-chart.component';
import { PieChartComponent } from '../../shared/components/pie-chart/pie-chart.component';
import { ApiResponse, ApiService, Holding } from '../../core/services/api.service';
import { tap } from 'rxjs';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';

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
  imports: [DataTableComponent, StatCardComponent, LineChartComponent, PieChartComponent],
  templateUrl: './dashboard.component.html',
  styleUrl: './dashboard.component.scss',
})
export class DashboardComponent {
  private testId = '5e1a30de-d433-48f6-9974-c7cbd6da8ebe';
  private apiService = inject(ApiService);
  holdingsData!: ApiResponse<Holding[]>;

  constructor() {
    this.apiService
      .getHoldings(this.testId)
      .pipe(
        takeUntilDestroyed(),
        tap((data) => console.log(data))
      )
      .subscribe((data: ApiResponse<Holding[]>) => (this.holdingsData = data));
  }
}
