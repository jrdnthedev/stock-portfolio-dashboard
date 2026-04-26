import { Component, DestroyRef, inject, OnInit, signal } from '@angular/core';
import { DataTableComponent } from '../../shared/components/data-table/data-table.component';
import { StatCardComponent } from '../../shared/components/stat-card/stat-card.component';
import { LineChartComponent } from '../../shared/components/line-chart/line-chart.component';
import { PieChartComponent } from '../../shared/components/pie-chart/pie-chart.component';
import { AllocationItem, ApiResponse, ApiService, Holding } from '../../core/services/api.service';
import { catchError, forkJoin, map, of } from 'rxjs';
import { CurrencyPipe, PercentPipe } from '@angular/common';
import { DropdownComponent } from '../../shared/components/dropdown/dropdown.component';
import {
  DateRange,
  DateRangeComponent,
} from '../../shared/components/date-range/date-range.component';
import { ButtonComponent } from '../../shared/components/button/button.component';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';

export interface HoldingTableRow {
  'Avg Cost': string | null;
  Price: string | null;
  symbol: string;
  'PBL $': string | null;
  'PBL %': string | null;
  'Mkt Value': string | null;
  Qty: number;
}

export interface PieChartOptions {
  name: string;
  value: number;
}

@Component({
  selector: 'app-dashboard',
  imports: [
    DataTableComponent,
    StatCardComponent,
    LineChartComponent,
    PieChartComponent,
    DropdownComponent,
    DateRangeComponent,
    ButtonComponent,
  ],
  providers: [CurrencyPipe, PercentPipe],
  templateUrl: './dashboard.component.html',
  styleUrl: './dashboard.component.scss',
})
export class DashboardComponent implements OnInit {
  private readonly destroyRef = inject(DestroyRef);
  private testId = '5e1a30de-d433-48f6-9974-c7cbd6da8ebe';
  readonly tableData = signal<HoldingTableRow[]>([]);
  readonly isFilterStacked = false;
  readonly sectorAllocation = signal<PieChartOptions[]>([]);
  readonly totalValue = signal<string | null>('');
  readonly totalGain = signal<string | null>('');
  readonly positions = signal<string | null>('');
  readonly topPerformer = signal<{ symbol: string; gain: string } | null>(null);

  constructor(
    private apiService: ApiService,
    private currencyPipe: CurrencyPipe,
    private percentPipe: PercentPipe
  ) {}

  ngOnInit(): void {
    this.loadDashboardData();
  }

  loadDashboardData() {
    forkJoin({
      portfolio: this.apiService.getPortfolio(this.testId),
      holdings: this.apiService.getHoldings(this.testId).pipe(
        map((response: ApiResponse<Holding[]>) => {
          const raw = response.data;
          const top = raw.length
            ? raw.reduce((best, h) => (h.gain_percent > best.gain_percent ? h : best))
            : null;
          const tableRows = raw.map((holding: Holding) => ({
            symbol: holding.ticker.symbol,
            Qty: holding.quantity,
            'Avg Cost': this.currencyPipe.transform(
              holding.avg_cost_basis,
              'USD',
              'symbol',
              '1.2-2'
            ),
            Price: this.currencyPipe.transform(holding.current_price, 'USD', 'symbol', '1.2-2'),
            'Mkt Value': this.currencyPipe.transform(holding.total_value, 'USD', 'symbol', '1.2-2'),
            'PBL $': this.currencyPipe.transform(holding.gain, 'USD', 'symbol', '1.2-2'),
            'PBL %': this.percentPipe.transform(holding.gain_percent / 100, '1.2-2'),
          }));
          return { tableRows, top };
        })
      ),
      performance: this.apiService.getPerformance(this.testId, '2023-01-01', '2023-12-31'),
      allocation: this.apiService.getAllocation(this.testId).pipe(
        map((response: ApiResponse<AllocationItem[]>) => {
          return response.data.map((item: AllocationItem) => ({
            name: item.ticker,
            value: item.value,
          }));
        })
      ),
    })
      .pipe(
        catchError((error) => {
          console.error('Error loading dashboard data:', error);
          return of({
            portfolio: { data: { total_value: null, total_gain: null } },
            holdings: { tableRows: [], top: null },
            performance: null,
            allocation: [],
          });
        }),
        takeUntilDestroyed(this.destroyRef)
      )
      .subscribe(({ holdings, allocation, portfolio }) => {
        this.tableData.set(holdings.tableRows);
        this.sectorAllocation.set(allocation);
        this.totalValue.set(
          this.currencyPipe.transform(portfolio.data.total_value, 'USD', 'symbol', '1.2-2')
        );
        this.totalGain.set(
          this.currencyPipe.transform(portfolio.data.total_gain, 'USD', 'symbol', '1.2-2')
        );
        this.positions.set(holdings.tableRows.length.toString());
        this.topPerformer.set(
          holdings.top
            ? {
                symbol: holdings.top.ticker.symbol,
                gain: `+${this.percentPipe.transform(holdings.top.gain_percent / 100, '1.2-2')}`,
              }
            : null
        );
      });
  }
  onSectorChange(selectedSector: string) {
    console.log(`Selected sector: ${selectedSector}`);
    // Implement filtering logic based on the selected sector
  }

  onDailyChange(selectedDaily: string) {
    console.log(`Selected daily change: ${selectedDaily}`);
    // Implement filtering logic based on the selected daily change
  }

  onDateRangeChange(selectedDateRange: DateRange) {
    console.log(`Selected date range: ${JSON.stringify(selectedDateRange)}`);
    // Implement filtering logic based on the selected date range
  }
  onSave() {
    console.log('Save button clicked');
    // Implement save functionality, e.g., save current filters or settings
  }

  onReset() {
    console.log('Reset button clicked');
    // Implement reset functionality, e.g., reset filters or settings to default
  }
}
