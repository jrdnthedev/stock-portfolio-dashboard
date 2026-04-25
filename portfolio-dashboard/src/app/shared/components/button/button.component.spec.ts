import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideZonelessChangeDetection } from '@angular/core';

import { ButtonComponent } from './button.component';

describe('ButtonComponent', () => {
  let component: ButtonComponent;
  let fixture: ComponentFixture<ButtonComponent>;
  let button: HTMLButtonElement;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ButtonComponent],
      providers: [provideZonelessChangeDetection()],
    }).compileComponents();

    fixture = TestBed.createComponent(ButtonComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
    button = fixture.nativeElement.querySelector('button');
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should render the label text', () => {
    fixture.componentRef.setInput('label', 'Save');
    fixture.detectChanges();
    expect(button.textContent?.trim()).toBe('Save');
  });

  it('should apply the variant as a CSS class', () => {
    fixture.componentRef.setInput('variant', 'secondary');
    fixture.detectChanges();
    expect(button.classList).toContain('secondary');
  });

  it('should disable the button when disabled is true', () => {
    fixture.componentRef.setInput('disabled', true);
    fixture.detectChanges();
    expect(button.disabled).toBe(true);
  });

  it('should emit clicked when the button is clicked and not disabled', () => {
    const emitted: void[] = [];
    component.clicked.subscribe(() => emitted.push());
    button.click();
    expect(emitted.length).toBe(1);
  });

  it('should not emit clicked when disabled', () => {
    const emitted: void[] = [];
    component.clicked.subscribe(() => emitted.push());
    fixture.componentRef.setInput('disabled', true);
    fixture.detectChanges();
    button.click();
    expect(emitted.length).toBe(0);
  });
});
