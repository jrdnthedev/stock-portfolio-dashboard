import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideZonelessChangeDetection } from '@angular/core';
import { provideAnimationsAsync } from '@angular/platform-browser/animations/async';
import { LineChartComponent } from './line-chart.component';

describe('LineChartComponent', () => {
  let component: LineChartComponent;
  let fixture: ComponentFixture<LineChartComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [LineChartComponent],
      providers: [provideZonelessChangeDetection(), provideAnimationsAsync()],
    }).compileComponents();

    fixture = TestBed.createComponent(LineChartComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should have options defined', () => {
    expect(component.options).toBeDefined();
  });

  it('should have three series for AAPL, MSFT and GOOGL', () => {
    const series = component.options['series'] as { name: string }[];
    expect(series.map((s) => s.name)).toEqual(['AAPL', 'MSFT', 'GOOGL']);
  });

  it('should have 12 data points per series', () => {
    const series = component.options['series'] as { data: number[] }[];
    series.forEach((s) => expect(s.data).toHaveLength(12));
  });

  it('should format tooltip with dollar values', () => {
    const formatter = (component.options['tooltip'] as { formatter: (params: unknown) => string })
      .formatter;
    const params = [
      { marker: '●', seriesName: 'AAPL', value: 218, axisValue: 'Apr' },
      { marker: '●', seriesName: 'MSFT', value: 405, axisValue: 'Apr' },
    ];
    const result = formatter(params) as string;
    expect(result).toContain('Apr');
    expect(result).toContain('AAPL');
    expect(result).toContain('$218');
  });

  it('should render the echarts host element', () => {
    const el: HTMLElement = fixture.nativeElement;
    expect(el.querySelector('[echarts]')).toBeTruthy();
  });
});
