import { NgClass } from '@angular/common';
import { Component, input, output, signal } from '@angular/core';

export interface TableColumn<T> {
  key: keyof T & string;
  label: string;
  type: 'string' | 'number' | 'currency' | 'percent';
  formatter?: (value: T[keyof T], row: T) => T[keyof T];
}

@Component({
  selector: 'app-data-table',
  imports: [NgClass],
  templateUrl: './data-table.component.html',
  styleUrl: './data-table.component.scss',
})
export class DataTableComponent<T extends Record<string, string | number | null>> {
  data = input<T[]>([]);
  columns = input<TableColumn<T>[]>([]);
  selectable = input(false);
  selectionChange = output<Set<T>>();

  // Internal state for selected rows
  private _selectedRows = signal<Set<T>>(new Set());

  get headers(): (keyof T & string)[] {
    // If columns are provided, use them; otherwise auto-generate from data
    if (this.columns() && this.columns().length > 0) {
      return this.columns().map((col: TableColumn<T>) => col.key);
    }
    if (this.data() && this.data().length > 0) {
      return Object.keys(this.data()[0] as object) as (keyof T & string)[];
    }
    return [];
  }

  getHeaderLabel(key: string): string {
    const column = this.columns().find((col: TableColumn<T>) => col.key === key);
    return column ? column.label : key;
  }

  getRawValue(row: T, key: string): T[keyof T] {
    return row[key as keyof T];
  }

  getFormattedValue(row: T, key: string): T | T[keyof T] {
    const column = this.columns().find((col: TableColumn<T>) => col.key === key);
    const value = this.getRawValue(row, key);
    if (column && column.formatter) {
      return column.formatter(value, row);
    }
    return value;
  }

  // Check if a specific row is selected
  isRowSelected(row: T): boolean {
    return this._selectedRows().has(row);
  }

  // Check if all rows are selected
  isAllSelected(): boolean {
    return this.data().length > 0 && this._selectedRows().size === this.data().length;
  }

  // Toggle individual row selection
  toggleRow(row: T): void {
    const newSelection = new Set(this._selectedRows());

    if (newSelection.has(row)) {
      newSelection.delete(row);
    } else {
      newSelection.add(row);
    }

    this._selectedRows.set(newSelection);
    this.selectionChange.emit(newSelection);
  }

  // Toggle all rows selection
  toggleAll(): void {
    const newSelection = this.isAllSelected()
      ? new Set<T>() // Deselect all
      : new Set(this.data()); // Select all

    this._selectedRows.set(newSelection);
    this.selectionChange.emit(newSelection);
  }

  sortColumn: string | null = null;
  sortDirection: 'asc' | 'desc' = 'asc';

  sortCol(columnKey: string): void {
    if (this.sortColumn === columnKey) {
      // Toggle direction
      this.sortDirection = this.sortDirection === 'asc' ? 'desc' : 'asc';
    } else {
      this.sortColumn = columnKey;
      this.sortDirection = 'asc';
    }
    const direction = this.sortDirection === 'asc' ? 1 : -1;
    this.data().sort((a: T, b: T) => {
      const aValue = this.getRawValue(a, columnKey);
      const bValue = this.getRawValue(b, columnKey);
      if (aValue == null && bValue == null) return 0;
      if (aValue == null) return -1 * direction;
      if (bValue == null) return 1 * direction;
      if (typeof aValue === 'number' && typeof bValue === 'number') {
        return (aValue - bValue) * direction;
      }
      return String(aValue).localeCompare(String(bValue)) * direction;
    });
  }
}
