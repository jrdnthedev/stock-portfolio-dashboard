import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideZonelessChangeDetection } from '@angular/core';

import { DateRange, DateRangeComponent } from './date-range.component';

describe('DateRangeComponent', () => {
  let component: DateRangeComponent;
  let fixture: ComponentFixture<DateRangeComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [DateRangeComponent],
      providers: [provideZonelessChangeDetection()],
    }).compileComponents();

    fixture = TestBed.createComponent(DateRangeComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should seed form controls from startDate and endDate inputs', () => {
    fixture.componentRef.setInput('startDate', '2024-01-01');
    fixture.componentRef.setInput('endDate', '2024-01-31');
    component.ngOnInit();

    expect(component.form.controls.startDate.value).toBe('2024-01-01');
    expect(component.form.controls.endDate.value).toBe('2024-01-31');
  });

  it('should apply stacked class when isStacked is true', () => {
    fixture.componentRef.setInput('isStacked', true);
    fixture.detectChanges();
    const container: HTMLElement = fixture.nativeElement.querySelector('.date-range-container');
    expect(container.classList).toContain('stacked');
  });

  it('should show labels when showLabel is true', () => {
    fixture.componentRef.setInput('showLabel', true);
    fixture.detectChanges();
    const labels = fixture.nativeElement.querySelectorAll('label');
    expect(labels.length).toBe(2);
  });

  it('should hide labels when showLabel is false', () => {
    const labels = fixture.nativeElement.querySelectorAll('label');
    expect(labels.length).toBe(0);
  });

  it('should emit rangeChanged with valid dates', () => {
    const emitted: DateRange[] = [];
    component.rangeChanged.subscribe((v: DateRange) => emitted.push(v));

    component.form.setValue({ startDate: '2024-01-01', endDate: '2024-01-31' });

    expect(emitted).toEqual([{ startDate: '2024-01-01', endDate: '2024-01-31' }]);
  });

  it('should not emit rangeChanged when end date is before start date', () => {
    const emitted: DateRange[] = [];
    component.rangeChanged.subscribe((v: DateRange) => emitted.push(v));

    component.form.setValue({ startDate: '2024-01-31', endDate: '2024-01-01' });

    expect(emitted.length).toBe(0);
  });

  it('should show error message when end date is before start date', () => {
    component.form.setValue({ startDate: '2024-01-31', endDate: '2024-01-01' });
    fixture.detectChanges();
    const error: HTMLElement = fixture.nativeElement.querySelector('.error');
    expect(error).toBeTruthy();
    expect(error.textContent?.trim()).toBe('End date must be on or after start date.');
  });

  it('should not show error message with valid dates', () => {
    component.form.setValue({ startDate: '2024-01-01', endDate: '2024-01-31' });
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('.error')).toBeNull();
  });

  it('should not emit rangeChanged when a field is empty', () => {
    const emitted: DateRange[] = [];
    component.rangeChanged.subscribe((v: DateRange) => emitted.push(v));

    component.form.controls.startDate.setValue('2024-01-01');

    expect(emitted.length).toBe(0);
  });
});
