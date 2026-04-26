import { ComponentFixture, TestBed } from '@angular/core/testing';

import { DropdownComponent } from './dropdown.component';
import { provideZonelessChangeDetection } from '@angular/core';

describe('DropdownComponent', () => {
  let component: DropdownComponent;
  let fixture: ComponentFixture<DropdownComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [DropdownComponent],
      providers: [provideZonelessChangeDetection()],
    }).compileComponents();

    fixture = TestBed.createComponent(DropdownComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should bind label text and select name/id from inputs', () => {
    fixture.componentRef.setInput('label', 'My Label');
    fixture.componentRef.setInput('name', 'my-select');
    fixture.detectChanges();

    const label: HTMLLabelElement = fixture.nativeElement.querySelector('label');
    const select: HTMLSelectElement = fixture.nativeElement.querySelector('select');

    expect(label.textContent?.trim()).toBe('My Label');
    expect(label.htmlFor).toBe('my-select');
    expect(select.name).toBe('my-select');
    expect(select.id).toBe('my-select');
  });

  it('should render one option per item in data plus a default option', () => {
    const options: NodeListOf<HTMLOptionElement> = fixture.nativeElement.querySelectorAll('option');
    expect(options.length).toBe(component.data.length + 1);
    component.data.forEach((item, i) => expect(options[i + 1].value).toBe(item));
  });

  it('should apply stacked class when isStacked is true', () => {
    fixture.componentRef.setInput('isStacked', true);
    fixture.detectChanges();
    const container: HTMLElement = fixture.nativeElement.querySelector('.label-container');
    expect(container.classList).toContain('stacked');
  });

  it('should not apply stacked class when isStacked is false', () => {
    const container: HTMLElement = fixture.nativeElement.querySelector('.label-container');
    expect(container.classList).not.toContain('stacked');
  });

  it('should hide the label when showLabel is false', () => {
    const label: HTMLLabelElement = fixture.nativeElement.querySelector('label');
    expect(label.classList).toContain('visually-hidden');
  });

  it('should show the label when showLabel is true', () => {
    fixture.componentRef.setInput('showLabel', true);
    fixture.detectChanges();
    const label: HTMLLabelElement = fixture.nativeElement.querySelector('label');
    expect(label.classList).not.toContain('visually-hidden');
  });

  it('should emit selected value via selectionChanged on change', () => {
    // Set up data input
    const testData = [
      { label: 'Option 1', value: 'value1' },
      { label: 'Option 2', value: 'value2' },
    ];
    fixture.componentRef.setInput('data', testData);
    fixture.detectChanges();

    const emitted: string[] = [];
    component.selectionChanged.subscribe((v: string) => emitted.push(v));

    const select: HTMLSelectElement = fixture.nativeElement.querySelector('select');
    // Set value to the value property of Option 2
    select.value = 'value2';
    select.dispatchEvent(new Event('change'));

    expect(emitted).toEqual(['value2']);
  });
});
