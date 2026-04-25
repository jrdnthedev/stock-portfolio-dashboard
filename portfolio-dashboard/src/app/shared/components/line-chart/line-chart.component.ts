import { Component } from '@angular/core';
import { NgxEchartsDirective, provideEchartsCore } from 'ngx-echarts';
import * as echarts from 'echarts/core';
import { CanvasRenderer } from 'echarts/renderers';
import { EChartsCoreOption } from 'echarts/core';

interface TooltipParam {
  marker: string;
  seriesName: string;
  value: number;
  axisValue: string;
}
import {
  TitleComponent,
  TooltipComponent,
  GridComponent,
  LegendComponent,
} from 'echarts/components';
import { LineChart } from 'echarts/charts';

echarts.use([
  CanvasRenderer,
  TitleComponent,
  TooltipComponent,
  GridComponent,
  LegendComponent,
  LineChart,
]);

@Component({
  selector: 'app-line-chart',
  imports: [NgxEchartsDirective],
  providers: [provideEchartsCore({ echarts })],
  templateUrl: './line-chart.component.html',
  styleUrl: './line-chart.component.scss',
})
export class LineChartComponent {
  options: EChartsCoreOption = {
    title: {
      text: 'Portfolio Performance',
      subtext: 'Last 12 months (mock data)',
      left: 'center',
    },
    tooltip: {
      trigger: 'axis',
      formatter: (params: TooltipParam | TooltipParam[]) => {
        const list = Array.isArray(params) ? params : [params];
        const lines = list.map((p) => `${p.marker}${p.seriesName}: $${p.value.toLocaleString()}`);
        return `${list[0].axisValue}<br/>${lines.join('<br/>')}`;
      },
    },
    legend: {
      bottom: 0,
      data: ['AAPL', 'MSFT', 'GOOGL'],
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '10%',
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: ['May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar', 'Apr'],
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        formatter: '${value}',
      },
    },
    series: [
      {
        name: 'AAPL',
        type: 'line',
        smooth: true,
        data: [162, 171, 178, 175, 169, 185, 191, 195, 188, 202, 210, 218],
        itemStyle: { color: '#5470c6' },
      },
      {
        name: 'MSFT',
        type: 'line',
        smooth: true,
        data: [310, 318, 325, 320, 335, 350, 362, 375, 368, 382, 390, 405],
        itemStyle: { color: '#91cc75' },
      },
      {
        name: 'GOOGL',
        type: 'line',
        smooth: true,
        data: [125, 130, 128, 135, 140, 138, 145, 150, 148, 155, 160, 168],
        itemStyle: { color: '#fac858' },
      },
    ],
  };
}
