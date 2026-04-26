import { Component, DestroyRef, inject, OnInit, signal } from '@angular/core';
import {
  DataTableComponent,
  TableColumn,
} from '../../shared/components/data-table/data-table.component';
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
  avg_cost: number;
  price: number;
  symbol: string;
  pbl_dollar: number | null;
  pbl_percent: number | null;
  mkt_value: number | null;
  qty: number;
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
  readonly totalValue = signal<number | null>(null);
  readonly totalGain = signal<number | null>(null);
  readonly positions = signal<number | null>(null);
  readonly topPerformer = signal<{ symbol: string; gain: number } | null>(null);
  readonly columns: TableColumn<HoldingTableRow>[] = [
    { key: 'symbol', label: 'Symbol', type: 'string' },
    { key: 'qty', label: 'Qty', type: 'number' },
    {
      key: 'avg_cost',
      label: 'Avg Cost',
      type: 'currency',
      formatter: (value: string | number | null) => this.currencyPipe.transform(value, 'USD') || '',
    },
    {
      key: 'price',
      label: 'Price',
      type: 'currency',
      formatter: (value: string | number | null) => this.currencyPipe.transform(value, 'USD') || '',
    },
    {
      key: 'mkt_value',
      label: 'Mkt Value',
      type: 'currency',
      formatter: (value: string | number | null) => this.currencyPipe.transform(value, 'USD') || '',
    },
    {
      key: 'pbl_dollar',
      label: 'PBL $',
      type: 'currency',
      formatter: (value: string | number | null) => this.currencyPipe.transform(value, 'USD') || '',
    },
    {
      key: 'pbl_percent',
      label: 'PBL %',
      type: 'percent',
      formatter: (value: string | number | null) =>
        this.percentPipe.transform((value as number) / 100) || '',
    },
  ];

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
            qty: holding.quantity,
            avg_cost: holding.avg_cost_basis,
            price: holding.current_price,
            mkt_value: holding.total_value,
            pbl_dollar: holding.gain,
            pbl_percent: holding.gain_percent,
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
        this.totalValue.set(portfolio.data.total_value);
        this.totalGain.set(portfolio.data.total_gain);
        this.positions.set(holdings.tableRows.length);
        this.topPerformer.set(
          holdings.top
            ? {
                symbol: holdings.top.ticker.symbol,
                gain: holdings.top.gain_percent,
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
