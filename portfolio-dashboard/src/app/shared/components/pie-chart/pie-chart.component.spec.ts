import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideZonelessChangeDetection } from '@angular/core';
import { provideAnimationsAsync } from '@angular/platform-browser/animations/async';

import { CoolTheme, PieChartComponent } from './pie-chart.component';

describe('PieChartComponent', () => {
  let component: PieChartComponent;
  let fixture: ComponentFixture<PieChartComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [PieChartComponent],
      providers: [provideZonelessChangeDetection(), provideAnimationsAsync()],
    }).compileComponents();

    fixture = TestBed.createComponent(PieChartComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should have options defined', () => {
    expect(component.options).toBeDefined();
  });

  it('should expose coolTheme equal to CoolTheme constant', () => {
    expect(component.coolTheme).toBe(CoolTheme);
  });

  it('should have theme unset by default', () => {
    expect(component.theme).toBeUndefined();
  });

  it('should have a single pie series named Portfolio', () => {
    const series = component.options['series'] as { name: string; type: string }[];
    expect(series).toHaveLength(1);
    expect(series[0].name).toBe('Portfolio');
    expect(series[0].type).toBe('pie');
  });

  it('should have three data slices for AAPL, MSFT and GOOGL', () => {
    const series = component.options['series'] as { data: { name: string }[] }[];
    expect(series[0].data.map((d) => d.name)).toEqual(['AAPL', 'MSFT', 'GOOGL']);
  });

  it('should render the echarts host element', () => {
    const el: HTMLElement = fixture.nativeElement;
    expect(el.querySelector('[echarts]')).toBeTruthy();
  });
});
