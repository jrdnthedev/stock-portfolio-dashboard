import { Component, signal } from '@angular/core';
import { DataTableComponent } from '../../shared/components/data-table/data-table.component';
import { StatCardComponent } from '../../shared/components/stat-card/stat-card.component';
import { LineChartComponent } from '../../shared/components/line-chart/line-chart.component';
import { PieChartComponent } from '../../shared/components/pie-chart/pie-chart.component';
import { ApiResponse, ApiService, Holding } from '../../core/services/api.service';
import { map, tap } from 'rxjs';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { CurrencyPipe } from '@angular/common';

export interface HoldingTableRow {
  'Avg Cost': string | null;
  Price: string | null;
  symbol: string;
  'Total Cost': string | null;
  'Mkt Value': string | null;
  Qty: number;
}

@Component({
  selector: 'app-dashboard',
  imports: [DataTableComponent, StatCardComponent, LineChartComponent, PieChartComponent],
  providers: [CurrencyPipe],
  templateUrl: './dashboard.component.html',
  styleUrl: './dashboard.component.scss',
})
export class DashboardComponent {
  private testId = '5e1a30de-d433-48f6-9974-c7cbd6da8ebe';
  holdingsData: Holding[] = [];
  tableData = signal<HoldingTableRow[]>([]);

  constructor(
    private apiService: ApiService,
    private currencyPipe: CurrencyPipe
  ) {
    this.apiService
      .getHoldings(this.testId)
      .pipe(
        takeUntilDestroyed(),
        map((response: ApiResponse<Holding[]>) => {
          this.holdingsData = response.data;
          return response.data.map((holding: Holding) => ({
            symbol: holding.ticker.symbol,
            Qty: holding.quantity,
            'Avg Cost': this.currencyPipe.transform(
              holding.avg_cost_basis,
              'USD',
              'symbol',
              '1.2-2'
            ),
            Price: this.currencyPipe.transform(holding.current_price, 'USD', 'symbol', '1.2-2'),
            'Total Cost': this.currencyPipe.transform(holding.total_cost, 'USD', 'symbol', '1.2-2'),
            'Mkt Value': this.currencyPipe.transform(holding.total_value, 'USD', 'symbol', '1.2-2'),
          }));
        }),
        tap((tableData: HoldingTableRow[]) => console.log(tableData))
      )
      .subscribe((tableData: HoldingTableRow[]) => {
        this.tableData.set(tableData);
      });
  }
}
