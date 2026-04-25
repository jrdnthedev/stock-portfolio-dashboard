import { CommonModule } from '@angular/common';
import { Component, Input, output } from '@angular/core';

@Component({
  selector: 'app-button',
  imports: [CommonModule],
  templateUrl: './button.component.html',
  styleUrl: './button.component.scss',
})
export class ButtonComponent {
  @Input() label = 'Button';
  @Input() variant: 'primary' | 'secondary' | 'tertiary' = 'primary';
  @Input() disabled = false;
  clicked = output<void>();

  onclick() {
    if (!this.disabled) {
      this.clicked.emit();
    }
  }
}
