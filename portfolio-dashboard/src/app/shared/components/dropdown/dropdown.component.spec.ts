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

  it('should render one option per item in data', () => {
    const options: NodeListOf<HTMLOptionElement> = fixture.nativeElement.querySelectorAll('option');
    expect(options.length).toBe(component.data.length);
    component.data.forEach((item, i) => expect(options[i].value).toBe(item));
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

  it('should emit selected value via selectionChanged on change', () => {
    const emitted: string[] = [];
    component.selectionChanged.subscribe((v: string) => emitted.push(v));

    const select: HTMLSelectElement = fixture.nativeElement.querySelector('select');
    select.value = 'Option 2';
    select.dispatchEvent(new Event('change'));

    expect(emitted).toEqual(['Option 2']);
  });
});
