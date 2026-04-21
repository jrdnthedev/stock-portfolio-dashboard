import { TestBed } from '@angular/core/testing';
import { provideZonelessChangeDetection } from '@angular/core';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting, HttpTestingController } from '@angular/common/http/testing';

import {
  ApiService,
  ApiResponse,
  Portfolio,
  Holding,
  PerformanceMetric,
  AllocationItem,
  PricePoint,
  LatestPrice,
  Fundamentals,
  Ticker,
  HoldingCreate,
  HoldingUpdate,
  HealthStatus,
} from './api.service';

const BASE_URL = 'http://localhost:8000';
const API_BASE = `${BASE_URL}/api/v1`;

describe('ApiService', () => {
  let service: ApiService;
  let httpController: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        provideZonelessChangeDetection(),
        provideHttpClient(),
        provideHttpClientTesting(),
      ],
    });
    service = TestBed.inject(ApiService);
    httpController = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpController.verify();
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });

  // ==================== Health ====================

  describe('getHealthStatus', () => {
    it('should GET the unversioned health endpoint', () => {
      const mockResponse: HealthStatus = {
        status: 'ok',
        version: '1.0.0',
        timestamp: '2026-04-21T00:00:00Z',
        services: { database: 'ok', redis: 'ok', kafka: 'ok' },
      };

      service.getHealthStatus().subscribe((res) => expect(res).toEqual(mockResponse));

      const req = httpController.expectOne(`${BASE_URL}/api/health`);
      expect(req.request.method).toBe('GET');
      req.flush(mockResponse);
    });
  });

  // ==================== Portfolio Endpoints ====================

  describe('getPortfolios', () => {
    it('should GET /portfolio and return a list of portfolios', () => {
      const mockPortfolio: Portfolio = {
        id: 'p1',
        name: 'My Portfolio',
        description: null,
        created_at: '2026-01-01T00:00:00Z',
        updated_at: '2026-01-01T00:00:00Z',
        total_value: 10000,
        total_cost: 8000,
        total_gain: 2000,
        total_gain_percent: 25,
      };
      const mockResponse: ApiResponse<Portfolio[]> = {
        status: 'success',
        message: 'ok',
        data: [mockPortfolio],
      };

      service.getPortfolios().subscribe((res) => expect(res).toEqual(mockResponse));

      const req = httpController.expectOne(`${API_BASE}/portfolio`);
      expect(req.request.method).toBe('GET');
      req.flush(mockResponse);
    });
  });

  describe('getPortfolio', () => {
    it('should GET /portfolio/:id for the given portfolio ID', () => {
      const mockResponse: ApiResponse<Portfolio> = {
        status: 'success',
        message: 'ok',
        data: {
          id: 'p1',
          name: 'My Portfolio',
          description: 'Test',
          created_at: '2026-01-01T00:00:00Z',
          updated_at: '2026-01-01T00:00:00Z',
          total_value: 5000,
          total_cost: 4000,
          total_gain: 1000,
          total_gain_percent: 25,
        },
      };

      service.getPortfolio('p1').subscribe((res) => expect(res).toEqual(mockResponse));

      const req = httpController.expectOne(`${API_BASE}/portfolio/p1`);
      expect(req.request.method).toBe('GET');
      req.flush(mockResponse);
    });
  });

  describe('getHoldings', () => {
    it('should GET /portfolio/:id/holdings for the given portfolio ID', () => {
      const mockResponse: ApiResponse<Holding[]> = {
        status: 'success',
        message: 'ok',
        data: [],
      };

      service.getHoldings('p1').subscribe((res) => expect(res).toEqual(mockResponse));

      const req = httpController.expectOne(`${API_BASE}/portfolio/p1/holdings`);
      expect(req.request.method).toBe('GET');
      req.flush(mockResponse);
    });
  });

  describe('getPerformance', () => {
    it('should GET /portfolio/:id/performance without query params when dates are omitted', () => {
      const mockResponse: ApiResponse<PerformanceMetric[]> = {
        status: 'success',
        message: 'ok',
        data: [],
      };

      service.getPerformance('p1').subscribe((res) => expect(res).toEqual(mockResponse));

      const req = httpController.expectOne(`${API_BASE}/portfolio/p1/performance`);
      expect(req.request.method).toBe('GET');
      expect(req.request.params.has('from')).toBe(false);
      expect(req.request.params.has('to')).toBe(false);
      req.flush(mockResponse);
    });

    it('should include "from" and "to" query params when dates are provided', () => {
      const mockResponse: ApiResponse<PerformanceMetric[]> = {
        status: 'success',
        message: 'ok',
        data: [],
      };

      service.getPerformance('p1', '2026-01-01', '2026-04-01').subscribe();

      const req = httpController.expectOne((r) => r.url === `${API_BASE}/portfolio/p1/performance`);
      expect(req.request.params.get('from')).toBe('2026-01-01');
      expect(req.request.params.get('to')).toBe('2026-04-01');
      req.flush(mockResponse);
    });

    it('should include only "from" param when only fromDate is provided', () => {
      service.getPerformance('p1', '2026-01-01').subscribe();

      const req = httpController.expectOne((r) => r.url === `${API_BASE}/portfolio/p1/performance`);
      expect(req.request.params.get('from')).toBe('2026-01-01');
      expect(req.request.params.has('to')).toBe(false);
      req.flush({ status: 'success', message: 'ok', data: [] });
    });
  });

  describe('getAllocation', () => {
    it('should GET /portfolio/:id/allocation', () => {
      const mockData: AllocationItem[] = [
        { ticker: 'AAPL', value: 5000, percentage: 50, sector: 'Technology' },
      ];
      const mockResponse: ApiResponse<AllocationItem[]> = {
        status: 'success',
        message: 'ok',
        data: mockData,
      };

      service.getAllocation('p1').subscribe((res) => expect(res).toEqual(mockResponse));

      const req = httpController.expectOne(`${API_BASE}/portfolio/p1/allocation`);
      expect(req.request.method).toBe('GET');
      req.flush(mockResponse);
    });
  });

  describe('createHolding', () => {
    it('should POST /portfolio/:id/holdings with the holding payload', () => {
      const holdingCreate: HoldingCreate = {
        ticker: 'AAPL',
        quantity: 10,
        average_cost: 150,
        purchased_at: '2026-01-01',
      };
      const mockResponse: ApiResponse<Holding> = {
        status: 'success',
        message: 'created',
        data: {} as Holding,
      };

      service
        .createHolding('p1', holdingCreate)
        .subscribe((res) => expect(res).toEqual(mockResponse));

      const req = httpController.expectOne(`${API_BASE}/portfolio/p1/holdings`);
      expect(req.request.method).toBe('POST');
      expect(req.request.body).toEqual(holdingCreate);
      req.flush(mockResponse);
    });
  });

  describe('updateHolding', () => {
    it('should PUT /portfolio/:id/holdings/:holdingId with the update payload', () => {
      const updates: HoldingUpdate = { quantity: 20 };
      const mockResponse: ApiResponse<Holding> = {
        status: 'success',
        message: 'updated',
        data: {} as Holding,
      };

      service
        .updateHolding('p1', 'h1', updates)
        .subscribe((res) => expect(res).toEqual(mockResponse));

      const req = httpController.expectOne(`${API_BASE}/portfolio/p1/holdings/h1`);
      expect(req.request.method).toBe('PUT');
      expect(req.request.body).toEqual(updates);
      req.flush(mockResponse);
    });
  });

  describe('deleteHolding', () => {
    it('should DELETE /portfolio/:id/holdings/:holdingId', () => {
      const mockResponse: ApiResponse<null> = {
        status: 'success',
        message: 'deleted',
        data: null,
      };

      service.deleteHolding('p1', 'h1').subscribe((res) => expect(res).toEqual(mockResponse));

      const req = httpController.expectOne(`${API_BASE}/portfolio/p1/holdings/h1`);
      expect(req.request.method).toBe('DELETE');
      req.flush(mockResponse);
    });
  });

  // ==================== Market Data Endpoints ====================

  describe('getHistoricalPrices', () => {
    it('should GET /market/prices/:ticker without query params when dates are omitted', () => {
      const mockResponse: ApiResponse<PricePoint[]> = {
        status: 'success',
        message: 'ok',
        data: [],
      };

      service.getHistoricalPrices('AAPL').subscribe((res) => expect(res).toEqual(mockResponse));

      const req = httpController.expectOne(`${API_BASE}/market/prices/AAPL`);
      expect(req.request.method).toBe('GET');
      expect(req.request.params.has('from')).toBe(false);
      expect(req.request.params.has('to')).toBe(false);
      req.flush(mockResponse);
    });

    it('should include "from" and "to" query params when dates are provided', () => {
      service.getHistoricalPrices('AAPL', '2026-01-01', '2026-04-01').subscribe();

      const req = httpController.expectOne((r) => r.url === `${API_BASE}/market/prices/AAPL`);
      expect(req.request.params.get('from')).toBe('2026-01-01');
      expect(req.request.params.get('to')).toBe('2026-04-01');
      req.flush({ status: 'success', message: 'ok', data: [] });
    });
  });

  describe('getLatestPrice', () => {
    it('should GET /market/prices/:ticker/latest', () => {
      const mockData: LatestPrice = {
        ticker: 'AAPL',
        price: 200,
        change: 2,
        change_percent: 1,
        volume: 1000000,
        timestamp: '2026-04-21T00:00:00Z',
      };
      const mockResponse: ApiResponse<LatestPrice> = {
        status: 'success',
        message: 'ok',
        data: mockData,
      };

      service.getLatestPrice('AAPL').subscribe((res) => expect(res).toEqual(mockResponse));

      const req = httpController.expectOne(`${API_BASE}/market/prices/AAPL/latest`);
      expect(req.request.method).toBe('GET');
      req.flush(mockResponse);
    });
  });

  describe('getFundamentals', () => {
    it('should GET /market/fundamentals/:ticker', () => {
      const mockData: Fundamentals = {
        ticker: 'AAPL',
        company_name: 'Apple Inc.',
        sector: 'Technology',
        industry: 'Consumer Electronics',
        market_cap: 3000000000000,
        pe_ratio: 28.5,
        dividend_yield: 0.5,
        eps: 6.1,
        revenue: 400000000000,
        profit_margin: 0.25,
      };
      const mockResponse: ApiResponse<Fundamentals> = {
        status: 'success',
        message: 'ok',
        data: mockData,
      };

      service.getFundamentals('AAPL').subscribe((res) => expect(res).toEqual(mockResponse));

      const req = httpController.expectOne(`${API_BASE}/market/fundamentals/AAPL`);
      expect(req.request.method).toBe('GET');
      req.flush(mockResponse);
    });
  });

  describe('getTickers', () => {
    it('should GET /market/tickers without query params when search is omitted', () => {
      const mockResponse: ApiResponse<Ticker[]> = {
        status: 'success',
        message: 'ok',
        data: [],
      };

      service.getTickers().subscribe((res) => expect(res).toEqual(mockResponse));

      const req = httpController.expectOne(`${API_BASE}/market/tickers`);
      expect(req.request.method).toBe('GET');
      expect(req.request.params.has('search')).toBe(false);
      req.flush(mockResponse);
    });

    it('should include "search" query param when a search term is provided', () => {
      const mockData: Ticker[] = [
        {
          symbol: 'AAPL',
          name: 'Apple Inc.',
          exchange: 'NASDAQ',
          sector: 'Technology',
          asset_class: 'Equity',
        },
      ];
      const mockResponse: ApiResponse<Ticker[]> = {
        status: 'success',
        message: 'ok',
        data: mockData,
      };

      service.getTickers('AAPL').subscribe((res) => expect(res).toEqual(mockResponse));

      const req = httpController.expectOne((r) => r.url === `${API_BASE}/market/tickers`);
      expect(req.request.params.get('search')).toBe('AAPL');
      req.flush(mockResponse);
    });
  });
});
