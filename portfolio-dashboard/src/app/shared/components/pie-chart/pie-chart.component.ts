import { Component } from '@angular/core';
import { PieChartModule } from '@swimlane/ngx-charts';
export interface RowItem {
  entries: [];
  value: { name: string };
}

@Component({
  selector: 'app-pie-chart',
  imports: [PieChartModule],
  templateUrl: './pie-chart.component.html',
  styleUrl: './pie-chart.component.scss',
})
export class PieChartComponent {
  single = [
    {
      name: 'Germany',
      value: 8940000,
    },
    {
      name: 'USA',
      value: 5000000,
    },
    {
      name: 'France',
      value: 7200000,
    },
    {
      name: 'UK',
      value: 6200000,
    },
  ];

  // options
  gradient = true;
  showLegend = true;
  showLabels = true;
  isDoughnut = false;
  legendPosition = 'below';

  onSelect(data: RowItem): void {
    console.log('Item clicked', JSON.parse(JSON.stringify(data)));
  }

  onActivate(data: RowItem): void {
    console.log('Activate', JSON.parse(JSON.stringify(data)));
  }

  onDeactivate(data: RowItem): void {
    console.log('Deactivate', JSON.parse(JSON.stringify(data)));
  }
}
