import { ComponentFixture, TestBed } from '@angular/core/testing';

import { Holdings } from './holdings';

describe('Holdings', () => {
  let component: Holdings;
  let fixture: ComponentFixture<Holdings>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Holdings],
    }).compileComponents();

    fixture = TestBed.createComponent(Holdings);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
