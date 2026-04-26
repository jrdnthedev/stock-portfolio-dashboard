import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideZonelessChangeDetection } from '@angular/core';

import { DataTableComponent, TableColumn } from './data-table.component';

interface TestRow {
  id: number;
  name: string;
  [key: string]: string | number | null;
}

const ROWS: TestRow[] = [
  { id: 1, name: 'Alice' },
  { id: 2, name: 'Bob' },
];

const COLUMNS: TableColumn<TestRow>[] = [
  { key: 'id', label: 'ID', type: 'number' },
  { key: 'name', label: 'Full Name', type: 'string' },
];

describe('DataTableComponent', () => {
  let component: DataTableComponent<TestRow>;
  let fixture: ComponentFixture<DataTableComponent<TestRow>>;

  function setInputs(opts: {
    data?: TestRow[];
    columns?: TableColumn<TestRow>[];
    selectable?: boolean;
  }) {
    if (opts.data !== undefined) fixture.componentRef.setInput('data', opts.data);
    if (opts.columns !== undefined) fixture.componentRef.setInput('columns', opts.columns);
    if (opts.selectable !== undefined) fixture.componentRef.setInput('selectable', opts.selectable);
    fixture.detectChanges();
  }

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [DataTableComponent],
      providers: [provideZonelessChangeDetection()],
    }).compileComponents();

    fixture = TestBed.createComponent(DataTableComponent) as unknown as ComponentFixture<
      DataTableComponent<TestRow>
    >;
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  // ==================== headers getter ====================

  describe('headers', () => {
    it('should return an empty array when no data and no columns are provided', () => {
      expect(component.headers).toEqual([]);
    });

    it('should return column keys when columns input is provided', () => {
      setInputs({ columns: COLUMNS, data: ROWS });
      expect(component.headers).toEqual(['id', 'name']);
    });

    it('should auto-generate keys from the first data row when no columns are provided', () => {
      setInputs({ data: ROWS });
      expect(component.headers).toEqual(['id', 'name']);
    });

    it('should prefer columns over auto-generated keys when both are set', () => {
      const subset: TableColumn<TestRow>[] = [{ key: 'name', label: 'Name', type: 'string' }];
      setInputs({ columns: subset, data: ROWS });
      expect(component.headers).toEqual(['name']);
    });
  });

  // ==================== getHeaderLabel ====================

  describe('getHeaderLabel', () => {
    it('should return the column label for a known key', () => {
      setInputs({ columns: COLUMNS });
      expect(component.getHeaderLabel('name')).toBe('Full Name');
    });

    it('should fall back to the key itself when the column is not found', () => {
      setInputs({ columns: COLUMNS });
      expect(component.getHeaderLabel('unknown')).toBe('unknown');
    });
  });

  // ==================== getRawValue ====================

  describe('getRawValue', () => {
    it('should return the value for the specified key on a row', () => {
      expect(component.getRawValue(ROWS[0], 'name')).toBe('Alice');
      expect(component.getRawValue(ROWS[1], 'id')).toBe(2);
    });
  });

  // ==================== isRowSelected ====================

  describe('isRowSelected', () => {
    it('should return false for all rows initially', () => {
      setInputs({ data: ROWS });
      expect(component.isRowSelected(ROWS[0])).toBe(false);
      expect(component.isRowSelected(ROWS[1])).toBe(false);
    });

    it('should return true after a row is toggled on', () => {
      setInputs({ data: ROWS });
      component.toggleRow(ROWS[0]);
      expect(component.isRowSelected(ROWS[0])).toBe(true);
    });

    it('should return false after a selected row is toggled off', () => {
      setInputs({ data: ROWS });
      component.toggleRow(ROWS[0]);
      component.toggleRow(ROWS[0]);
      expect(component.isRowSelected(ROWS[0])).toBe(false);
    });
  });

  // ==================== isAllSelected ====================

  describe('isAllSelected', () => {
    it('should return false when data is empty', () => {
      setInputs({ data: [] });
      expect(component.isAllSelected()).toBe(false);
    });

    it('should return false when only some rows are selected', () => {
      setInputs({ data: ROWS });
      component.toggleRow(ROWS[0]);
      expect(component.isAllSelected()).toBe(false);
    });

    it('should return true when all rows are selected', () => {
      setInputs({ data: ROWS });
      component.toggleRow(ROWS[0]);
      component.toggleRow(ROWS[1]);
      expect(component.isAllSelected()).toBe(true);
    });
  });

  // ==================== toggleRow ====================

  describe('toggleRow', () => {
    it('should add a row to the selection', () => {
      setInputs({ data: ROWS });
      component.toggleRow(ROWS[0]);
      expect(component.isRowSelected(ROWS[0])).toBe(true);
    });

    it('should remove a row from the selection when already selected', () => {
      setInputs({ data: ROWS });
      component.toggleRow(ROWS[0]);
      component.toggleRow(ROWS[0]);
      expect(component.isRowSelected(ROWS[0])).toBe(false);
    });

    it('should emit selectionChange with the updated selection', () => {
      setInputs({ data: ROWS });
      let emitted: Set<TestRow> | undefined;
      const sub = component.selectionChange.subscribe((s) => (emitted = s));

      component.toggleRow(ROWS[0]);
      expect(emitted).toBeDefined();
      expect(emitted!.has(ROWS[0])).toBe(true);
      expect(emitted!.size).toBe(1);

      component.toggleRow(ROWS[0]);
      expect(emitted!.size).toBe(0);

      sub.unsubscribe();
    });
  });

  // ==================== toggleAll ====================

  describe('toggleAll', () => {
    it('should select all rows when none are selected', () => {
      setInputs({ data: ROWS });
      component.toggleAll();
      expect(component.isAllSelected()).toBe(true);
    });

    it('should deselect all rows when all are already selected', () => {
      setInputs({ data: ROWS });
      component.toggleAll();
      component.toggleAll();
      expect(component.isAllSelected()).toBe(false);
      ROWS.forEach((row) => expect(component.isRowSelected(row)).toBe(false));
    });

    it('should emit selectionChange with all rows when selecting all', () => {
      setInputs({ data: ROWS });
      let emitted: Set<TestRow> | undefined;
      const sub = component.selectionChange.subscribe((s) => (emitted = s));

      component.toggleAll();
      expect(emitted!.size).toBe(ROWS.length);
      ROWS.forEach((row) => expect(emitted!.has(row)).toBe(true));

      sub.unsubscribe();
    });

    it('should emit selectionChange with an empty set when deselecting all', () => {
      setInputs({ data: ROWS });
      component.toggleAll();

      let emitted: Set<TestRow> | undefined;
      const sub = component.selectionChange.subscribe((s) => (emitted = s));

      component.toggleAll();
      expect(emitted!.size).toBe(0);

      sub.unsubscribe();
    });
  });

  // ==================== Template ====================

  describe('template', () => {
    it('should render a <th> for each column label', () => {
      setInputs({ data: ROWS, columns: COLUMNS });
      const ths: NodeListOf<HTMLTableCellElement> =
        fixture.nativeElement.querySelectorAll('thead th');
      const labels = Array.from(ths).map((th) => th.textContent?.trim());
      expect(labels).toContain('ID ▲');
      expect(labels).toContain('Full Name ▲');
    });

    it('should render a <tr> for each data row', () => {
      setInputs({ data: ROWS, columns: COLUMNS });
      const rows: NodeListOf<HTMLTableRowElement> =
        fixture.nativeElement.querySelectorAll('tbody tr');
      expect(rows.length).toBe(ROWS.length);
    });

    it('should render cell values correctly', () => {
      setInputs({ data: ROWS, columns: COLUMNS });
      const cells: NodeListOf<HTMLTableCellElement> =
        fixture.nativeElement.querySelectorAll('tbody td');
      const values = Array.from(cells).map((td) => td.textContent?.trim());
      expect(values).toContain('Alice');
      expect(values).toContain('Bob');
      expect(values).toContain('1');
      expect(values).toContain('2');
    });

    it('should render an empty table body when data is empty', () => {
      setInputs({ data: [], columns: COLUMNS });
      const rows: NodeListOf<HTMLTableRowElement> =
        fixture.nativeElement.querySelectorAll('tbody tr');
      expect(rows.length).toBe(0);
    });

    it('should not render checkboxes when selectable is false (default)', () => {
      setInputs({ data: ROWS, columns: COLUMNS });
      const checkboxes: NodeListOf<HTMLInputElement> =
        fixture.nativeElement.querySelectorAll('input[type="checkbox"]');
      expect(checkboxes.length).toBe(0);
    });

    it('should render a "select all" checkbox and one per row when selectable is true', () => {
      setInputs({ data: ROWS, columns: COLUMNS, selectable: true });
      const checkboxes: NodeListOf<HTMLInputElement> =
        fixture.nativeElement.querySelectorAll('input[type="checkbox"]');
      // 1 select-all + 1 per row
      expect(checkboxes.length).toBe(ROWS.length + 1);
    });

    it('should check the "select all" checkbox when all rows are selected', () => {
      setInputs({ data: ROWS, columns: COLUMNS, selectable: true });
      component.toggleAll();
      fixture.detectChanges();
      const selectAll: HTMLInputElement =
        fixture.nativeElement.querySelector('#select-all-checkbox');
      expect(selectAll.checked).toBe(true);
    });

    it('should check the row checkbox when the row is selected', () => {
      setInputs({ data: ROWS, columns: COLUMNS, selectable: true });
      component.toggleRow(ROWS[0]);
      fixture.detectChanges();
      const rowCheckbox: HTMLInputElement = fixture.nativeElement.querySelector('#row-checkbox-0');
      expect(rowCheckbox.checked).toBe(true);
    });

    it('should call toggleAll when the "select all" checkbox changes', () => {
      setInputs({ data: ROWS, columns: COLUMNS, selectable: true });
      vi.spyOn(component, 'toggleAll');
      const selectAll: HTMLInputElement =
        fixture.nativeElement.querySelector('#select-all-checkbox');
      selectAll.dispatchEvent(new Event('change'));
      expect(component.toggleAll).toHaveBeenCalled();
    });

    it('should call toggleRow when a row checkbox changes', () => {
      setInputs({ data: ROWS, columns: COLUMNS, selectable: true });
      vi.spyOn(component, 'toggleRow');
      const rowCheckbox: HTMLInputElement = fixture.nativeElement.querySelector('#row-checkbox-0');
      rowCheckbox.dispatchEvent(new Event('change'));
      expect(component.toggleRow).toHaveBeenCalledWith(ROWS[0]);
    });

    it('should set data-label attribute on each cell matching the column label', () => {
      setInputs({ data: ROWS, columns: COLUMNS });
      const firstRowCells: NodeListOf<HTMLTableCellElement> =
        fixture.nativeElement.querySelectorAll('tbody tr:first-child td');
      const labels = Array.from(firstRowCells).map((td) => td.getAttribute('data-label'));
      expect(labels).toContain('ID');
      expect(labels).toContain('Full Name');
    });
  });
});
