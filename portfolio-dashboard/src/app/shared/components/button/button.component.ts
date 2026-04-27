import { NgClass } from '@angular/common';
import { Component, Input, output } from '@angular/core';
import { Subject, throttleTime } from 'rxjs';

@Component({
  selector: 'app-button',
  imports: [NgClass],
  templateUrl: './button.component.html',
  styleUrl: './button.component.scss',
})
export class ButtonComponent {
  @Input() label = 'Button';
  @Input() variant: 'primary' | 'secondary' | 'tertiary' = 'primary';
  @Input() disabled = false;
  private submitClick = new Subject<void>();
  clicked = output<void>();

  constructor() {
    this.submitClick.pipe(throttleTime(2000)).subscribe(() => this.clicked.emit());
  }
  onclick() {
    if (!this.disabled) {
      this.submitClick.next();
    }
  }
}
