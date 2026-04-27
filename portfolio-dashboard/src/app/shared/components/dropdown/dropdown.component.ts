import { NgClass } from '@angular/common';
import { Component, Input, output } from '@angular/core';

@Component({
  selector: 'app-dropdown',
  imports: [NgClass],
  templateUrl: './dropdown.component.html',
  styleUrl: './dropdown.component.scss',
})
export class DropdownComponent {
  @Input() data: { label: string; value: string }[] = [];
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
