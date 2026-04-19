import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

// Response interfaces
export interface ApiResponse<T> {
  status: string;
  message: string;
  data: T;
}

export interface Portfolio {
  id: string;
  name: string;
  description: string | null;
  created_at: string;
  updated_at: string;
  total_value: number;
  total_cost: number;
  total_gain: number;
  total_gain_percent: number;
}

export interface Holding {
  id: string;
  portfolio_id: string;
  ticker: {
    symbol: string;
    name: string;
  };
  quantity: number;
  average_cost: number;
  current_price: number;
  total_cost: number;
  total_value: number;
  gain: number;
  gain_percent: number;
  purchased_at: string;
  updated_at: string;
}

export interface PerformanceMetric {
  date: string;
  value: number;
  gain: number;
  gain_percent: number;
}

export interface AllocationItem {
  ticker: string;
  value: number;
  percentage: number;
  sector: string;
}

export interface PricePoint {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface LatestPrice {
  ticker: string;
  price: number;
  change: number;
  change_percent: number;
  volume: number;
  timestamp: string;
}

export interface Fundamentals {
  ticker: string;
  company_name: string;
  sector: string;
  industry: string;
  market_cap: number;
  pe_ratio: number | null;
  dividend_yield: number | null;
  eps: number | null;
  revenue: number | null;
  profit_margin: number | null;
}

export interface Ticker {
  symbol: string;
  name: string;
  exchange: string;
  sector: string;
  asset_class: string;
}

export interface HoldingCreate {
  ticker: string;
  quantity: number;
  average_cost: number;
  purchased_at?: string;
}

export interface HoldingUpdate {
  quantity?: number;
  average_cost?: number;
}

export interface HealthStatus {
  status: string;
  version: string;
  timestamp: string;
  services: {
    database: string;
    redis: string;
    kafka: string;
  };
}

@Injectable({
  providedIn: 'root',
})
export class ApiService {
  private readonly baseUrl: string;
  private readonly apiVersion: string;

  constructor(private http: HttpClient) {
    this.baseUrl = environment.apiUrl;
    this.apiVersion = environment.apiVersion;
  }

  // Helper method to build API URLs
  private buildUrl(endpoint: string): string {
    return `${this.baseUrl}/api/${this.apiVersion}${endpoint}`;
  }

  // Health endpoint (not versioned)
  getHealthStatus(): Observable<HealthStatus> {
    return this.http.get<HealthStatus>(`${this.baseUrl}/api/health`);
  }

  // ==================== Portfolio Endpoints ====================

  /**
   * Get all portfolios for the authenticated user
   */
  getPortfolios(): Observable<ApiResponse<Portfolio[]>> {
    return this.http.get<ApiResponse<Portfolio[]>>(this.buildUrl('/portfolio'));
  }

  /**
   * Get a specific portfolio by ID
   */
  getPortfolio(id: string): Observable<ApiResponse<Portfolio>> {
    return this.http.get<ApiResponse<Portfolio>>(this.buildUrl(`/portfolio/${id}`));
  }

  /**
   * Get all holdings for a portfolio
   */
  getHoldings(portfolioId: string): Observable<ApiResponse<Holding[]>> {
    return this.http.get<ApiResponse<Holding[]>>(
      this.buildUrl(`/portfolio/${portfolioId}/holdings`)
    );
  }

  /**
   * Get portfolio performance metrics
   */
  getPerformance(
    portfolioId: string,
    fromDate?: string,
    toDate?: string
  ): Observable<ApiResponse<PerformanceMetric[]>> {
    let params = new HttpParams();
    if (fromDate) {
      params = params.set('from', fromDate);
    }
    if (toDate) {
      params = params.set('to', toDate);
    }

    return this.http.get<ApiResponse<PerformanceMetric[]>>(
      this.buildUrl(`/portfolio/${portfolioId}/performance`),
      { params }
    );
  }

  /**
   * Get portfolio allocation breakdown
   */
  getAllocation(portfolioId: string): Observable<ApiResponse<AllocationItem[]>> {
    return this.http.get<ApiResponse<AllocationItem[]>>(
      this.buildUrl(`/portfolio/${portfolioId}/allocation`)
    );
  }

  /**
   * Create a new holding in a portfolio
   */
  createHolding(portfolioId: string, holding: HoldingCreate): Observable<ApiResponse<Holding>> {
    return this.http.post<ApiResponse<Holding>>(
      this.buildUrl(`/portfolio/${portfolioId}/holdings`),
      holding
    );
  }

  /**
   * Update an existing holding
   */
  updateHolding(
    portfolioId: string,
    holdingId: string,
    updates: HoldingUpdate
  ): Observable<ApiResponse<Holding>> {
    return this.http.put<ApiResponse<Holding>>(
      this.buildUrl(`/portfolio/${portfolioId}/holdings/${holdingId}`),
      updates
    );
  }

  /**
   * Delete a holding from a portfolio
   */
  deleteHolding(portfolioId: string, holdingId: string): Observable<ApiResponse<null>> {
    return this.http.delete<ApiResponse<null>>(
      this.buildUrl(`/portfolio/${portfolioId}/holdings/${holdingId}`)
    );
  }

  // ==================== Market Data Endpoints ====================

  /**
   * Get historical price data for a ticker
   */
  getHistoricalPrices(
    ticker: string,
    fromDate?: string,
    toDate?: string
  ): Observable<ApiResponse<PricePoint[]>> {
    let params = new HttpParams();
    if (fromDate) {
      params = params.set('from', fromDate);
    }
    if (toDate) {
      params = params.set('to', toDate);
    }

    return this.http.get<ApiResponse<PricePoint[]>>(this.buildUrl(`/market/prices/${ticker}`), {
      params,
    });
  }

  /**
   * Get latest price for a ticker
   */
  getLatestPrice(ticker: string): Observable<ApiResponse<LatestPrice>> {
    return this.http.get<ApiResponse<LatestPrice>>(
      this.buildUrl(`/market/prices/${ticker}/latest`)
    );
  }

  /**
   * Get fundamental data for a ticker
   */
  getFundamentals(ticker: string): Observable<ApiResponse<Fundamentals>> {
    return this.http.get<ApiResponse<Fundamentals>>(
      this.buildUrl(`/market/fundamentals/${ticker}`)
    );
  }

  /**
   * Search for tickers
   */
  getTickers(search?: string): Observable<ApiResponse<Ticker[]>> {
    let params = new HttpParams();
    if (search) {
      params = params.set('search', search);
    }

    return this.http.get<ApiResponse<Ticker[]>>(this.buildUrl('/market/tickers'), {
      params,
    });
  }
}
