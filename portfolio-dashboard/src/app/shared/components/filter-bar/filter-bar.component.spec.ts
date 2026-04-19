import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideZonelessChangeDetection } from '@angular/core';
import { FilterBarComponent } from './filter-bar.component';

describe('FilterBarComponent', () => {
  let component: FilterBarComponent;
  let fixture: ComponentFixture<FilterBarComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [FilterBarComponent],
      providers: [provideZonelessChangeDetection()],
    }).compileComponents();

    fixture = TestBed.createComponent(FilterBarComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
