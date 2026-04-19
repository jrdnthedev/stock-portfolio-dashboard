import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideZonelessChangeDetection } from '@angular/core';

import { TickerDetailsComponent } from './ticker-details.component';

describe('TickerDetailsComponent', () => {
  let component: TickerDetailsComponent;
  let fixture: ComponentFixture<TickerDetailsComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [TickerDetailsComponent],
      providers: [provideZonelessChangeDetection()],
    }).compileComponents();

    fixture = TestBed.createComponent(TickerDetailsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
