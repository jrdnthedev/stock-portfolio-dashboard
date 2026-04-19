import { ComponentFixture, TestBed } from '@angular/core/testing';

import { TickerDetails } from './ticker-details';

describe('TickerDetails', () => {
  let component: TickerDetails;
  let fixture: ComponentFixture<TickerDetails>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [TickerDetails],
    }).compileComponents();

    fixture = TestBed.createComponent(TickerDetails);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
