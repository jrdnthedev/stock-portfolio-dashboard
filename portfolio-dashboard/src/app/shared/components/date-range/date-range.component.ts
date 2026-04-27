import { Component, Input, OnInit, output } from '@angular/core';
import {
  AbstractControl,
  FormControl,
  FormGroup,
  ReactiveFormsModule,
  ValidationErrors,
  Validators,
} from '@angular/forms';

export interface DateRange {
  startDate: string;
  endDate: string;
}

function endAfterStart(control: AbstractControl): ValidationErrors | null {
  const group = control as FormGroup;
  const start = group.get('startDate')?.value as string;
  const end = group.get('endDate')?.value as string;
  return start && end && end < start ? { endBeforeStart: true } : null;
}

@Component({
  selector: 'app-date-range',
  imports: [ReactiveFormsModule],
  templateUrl: './date-range.component.html',
  styleUrl: './date-range.component.scss',
})
export class DateRangeComponent implements OnInit {
  @Input() startDate = '';
  @Input() endDate = '';
  @Input() isStacked = false;
  @Input() showLabel = false;

  rangeChanged = output<DateRange>();

  form = new FormGroup(
    {
      startDate: new FormControl('', { nonNullable: true, validators: Validators.required }),
      endDate: new FormControl('', { nonNullable: true, validators: Validators.required }),
    },
    { validators: endAfterStart }
  );

  ngOnInit(): void {
    if (this.startDate) this.form.controls.startDate.setValue(this.startDate);
    if (this.endDate) this.form.controls.endDate.setValue(this.endDate);

    this.form.valueChanges.subscribe(() => {
      if (this.form.valid) {
        this.rangeChanged.emit({
          startDate: this.form.controls.startDate.value,
          endDate: this.form.controls.endDate.value,
        });
      }
    });
  }
}
