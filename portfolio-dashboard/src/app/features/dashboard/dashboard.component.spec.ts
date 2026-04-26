import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideZonelessChangeDetection } from '@angular/core';
import { provideAnimationsAsync } from '@angular/platform-browser/animations/async';
import { describe, it, beforeEach, expect, vi } from 'vitest';
import { of, throwError } from 'rxjs';

import { DashboardComponent } from './dashboard.component';
import { ApiService } from '../../core/services/api.service';
import { DateRange } from '../../shared/components/date-range/date-range.component';

const mockPortfolioResponse = {
  status: 'ok',
  message: '',
  data: {
    id: 'portfolio-1',
    name: 'Test Portfolio',
    description: null,
    created_at: '2023-01-01',
    updated_at: '2023-01-01',
    total_value: 10000,
    total_cost: 8000,
    total_gain: 2000,
    total_gain_percent: 25,
  },
};

const mockHolding = {
  id: '1',
  portfolio_id: 'portfolio-1',
  ticker: { symbol: 'AAPL', name: 'Apple Inc.' },
  quantity: 10,
  avg_cost_basis: 100,
  current_price: 150,
  total_cost: 1000,
  total_value: 1500,
  gain: 500,
  gain_percent: 50,
  purchased_at: '2023-01-01',
  updated_at: '2023-01-01',
};

const mockHoldingsResponse = { status: 'ok', message: '', data: [mockHolding] };
const mockPerformanceResponse = { status: 'ok', message: '', data: [] };
const mockAllocationResponse = {
  status: 'ok',
  message: '',
  data: [{ ticker: 'AAPL', value: 1500, percentage: 100, sector: 'Technology' }],
};

describe('DashboardComponent', () => {
  let component: DashboardComponent;
  let fixture: ComponentFixture<DashboardComponent>;
  let apiServiceSpy: {
    getPortfolio: ReturnType<typeof vi.fn>;
    getHoldings: ReturnType<typeof vi.fn>;
    getPerformance: ReturnType<typeof vi.fn>;
    getAllocation: ReturnType<typeof vi.fn>;
  };

  beforeEach(async () => {
    apiServiceSpy = {
      getPortfolio: vi.fn().mockReturnValue(of(mockPortfolioResponse)),
      getHoldings: vi.fn().mockReturnValue(of(mockHoldingsResponse)),
      getPerformance: vi.fn().mockReturnValue(of(mockPerformanceResponse)),
      getAllocation: vi.fn().mockReturnValue(of(mockAllocationResponse)),
    };

    await TestBed.configureTestingModule({
      imports: [DashboardComponent],
      providers: [
        provideZonelessChangeDetection(),
        provideAnimationsAsync(),
        { provide: ApiService, useValue: apiServiceSpy },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(DashboardComponent);
    component = fixture.componentInstance;
  });

  it('should create', () => {
    fixture.detectChanges();
    expect(component).toBeTruthy();
  });

  it('should call loadDashboardData on init', () => {
    const spy = vi.spyOn(component, 'loadDashboardData');
    fixture.detectChanges();
    expect(spy).toHaveBeenCalledOnce();
  });

  describe('loadDashboardData', () => {
    it('should set all signals from API responses on success', () => {
      fixture.detectChanges();

      expect(component.tableData()).toHaveLength(1);
      expect(component.tableData()[0]).toMatchObject({
        symbol: 'AAPL',
        Qty: 10,
        'Avg Cost': '$100.00',
        Price: '$150.00',
        'Mkt Value': '$1,500.00',
        'PBL $': '$500.00',
        'PBL %': '50.00%',
      });
      expect(component.sectorAllocation()).toEqual([{ name: 'AAPL', value: 1500 }]);
      expect(component.totalValue()).toBe('$10,000.00');
      expect(component.totalGain()).toBe('$2,000.00');
      expect(component.positions()).toBe('1');
      expect(component.topPerformer()).toEqual({ symbol: 'AAPL', gain: '+50.00%' });
    });

    it('should set topPerformer to null and positions to "0" when holdings are empty', () => {
      apiServiceSpy.getHoldings.mockReturnValue(of({ status: 'ok', message: '', data: [] }));
      fixture.detectChanges();

      expect(component.tableData()).toEqual([]);
      expect(component.positions()).toBe('0');
      expect(component.topPerformer()).toBeNull();
    });

    it('should select the holding with the highest gain_percent as topPerformer', () => {
      apiServiceSpy.getHoldings.mockReturnValue(
        of({
          status: 'ok',
          message: '',
          data: [
            { ...mockHolding, ticker: { symbol: 'AAPL', name: 'Apple' }, gain_percent: 20 },
            { ...mockHolding, ticker: { symbol: 'MSFT', name: 'Microsoft' }, gain_percent: 40 },
          ],
        })
      );
      fixture.detectChanges();

      expect(component.topPerformer()?.symbol).toBe('MSFT');
    });

    it('should fall back to empty/null defaults when an API call errors', () => {
      apiServiceSpy.getPortfolio.mockReturnValue(throwError(() => new Error('Network error')));
      fixture.detectChanges();

      expect(component.tableData()).toEqual([]);
      expect(component.sectorAllocation()).toEqual([]);
      expect(component.totalValue()).toBeNull();
      expect(component.totalGain()).toBeNull();
      expect(component.positions()).toBe('0');
      expect(component.topPerformer()).toBeNull();
    });
  });

  describe('event handlers', () => {
    beforeEach(() => fixture.detectChanges());

    it('should handle onSectorChange without throwing', () => {
      expect(() => component.onSectorChange('Technology')).not.toThrow();
    });

    it('should handle onDailyChange without throwing', () => {
      expect(() => component.onDailyChange('gainers')).not.toThrow();
    });

    it('should handle onDateRangeChange without throwing', () => {
      const range: DateRange = { startDate: '2023-01-01', endDate: '2023-12-31' };
      expect(() => component.onDateRangeChange(range)).not.toThrow();
    });

    it('should handle onSave without throwing', () => {
      expect(() => component.onSave()).not.toThrow();
    });

    it('should handle onReset without throwing', () => {
      expect(() => component.onReset()).not.toThrow();
    });
  });
});
