import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideZonelessChangeDetection } from '@angular/core';

import { DataTableComponent } from './data-table.component';

interface TestData {
  id: number;
  name: string;
}

describe('DataTableComponent', () => {
  let component: DataTableComponent<TestData>;
  let fixture: ComponentFixture<DataTableComponent<TestData>>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [DataTableComponent],
      providers: [provideZonelessChangeDetection()],
    }).compileComponents();

    fixture = TestBed.createComponent(DataTableComponent) as ComponentFixture<
      DataTableComponent<TestData>
    >;
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
