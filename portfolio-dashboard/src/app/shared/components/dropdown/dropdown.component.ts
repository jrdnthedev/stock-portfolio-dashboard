import { CommonModule } from '@angular/common';
import { Component, Input, output } from '@angular/core';

@Component({
  selector: 'app-dropdown',
  imports: [CommonModule],
  templateUrl: './dropdown.component.html',
  styleUrl: './dropdown.component.scss',
})
export class DropdownComponent {
  data: string[] = ['Option 1', 'Option 2', 'Option 3'];
  @Input() name = 'test';
  @Input() label = 'Select an option';
  @Input() isStacked = false;
  @Input() showLabel = false;
  selectionChanged = output<string>();

  onSelectionChange(event: Event) {
    const selectElement = event.target as HTMLSelectElement;
    const selectedValue = selectElement.value;
    this.selectionChanged.emit(selectedValue);
  }
}
