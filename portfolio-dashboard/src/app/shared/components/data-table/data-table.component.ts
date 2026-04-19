import { Component, input, output, signal } from '@angular/core';

export interface TableColumn {
  key: string;
  label: string;
}

@Component({
  selector: 'app-data-table',
  imports: [],
  templateUrl: './data-table.component.html',
  styleUrl: './data-table.component.scss',
})
export class DataTableComponent<T> {
  data = input<T[]>([]);
  columns = input<TableColumn[]>([]);
  selectable = input(false);
  selectionChange = output<Set<T>>();

  // Internal state for selected rows
  private _selectedRows = signal<Set<T>>(new Set());

  get headers(): string[] {
    // If columns are provided, use them; otherwise auto-generate from data
    if (this.columns() && this.columns().length > 0) {
      return this.columns().map((col: TableColumn) => col.key);
    }

    if (this.data() && this.data().length > 0) {
      return Object.keys(this.data()[0] as object);
    }
    return [];
  }

  getHeaderLabel(key: string): string {
    const column = this.columns().find((col: TableColumn) => col.key === key);
    return column ? column.label : key;
  }

  getValue(row: T, key: string): T[keyof T] {
    return row[key as keyof T];
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
}
