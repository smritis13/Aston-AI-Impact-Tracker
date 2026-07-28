
/*  sales overview chart */
function earnings() {
    var options = {
        series: [{
        name: 'Total Profit',
        type: 'column',
        data: [23, 11, 22, 27, 13, 22, 37, 21, 44, 22, 30,11,]
      }, {
        name: 'Total Orders',
        type: 'bar',
        data: [44, 55, 41, 67, 22, 43, 21, 41, 56, 27, 43, 44,]
      }, {
        name: 'Total Sales',
        type: 'line',
        data: [30, 25, 36, 30, 45, 35, 64, 52, 59, 36, 39, 40,]
      }],
        chart: {
         toolbar: {
          show: false,
      },
        height: 323,
        type: 'line',
        stacked: false,
      },
      stroke: {
        width: [0, 0, 1],
        curve: 'smooth'
      },
      plotOptions: {
        bar: {
          columnWidth: '35%'
        }
      },
      colors: [ "rgba(" + myVarVal + ", 0.95)", "rgba(" + myVarVal + ", 0.4)",  '#e9ac04'],
      fill: {
        opacity: [0.85, 0.25, 1],
        gradient: {
          inverseColors: false,
          shade: 'light',
          type: "vertical",
          opacityFrom: 0.65,
          opacityTo: 0.15,
          stops: [0, 100, 100, 100]
        }
      },
      
      labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
      markers: {
        size: 0
      },
      xaxis: {
        type: 'month',
      },
      yaxis: {
        title: {
          text: 'Points',
        },
        min: 0
      },
      tooltip: {
        shared: true,
        intersect: false,
        y: {
          formatter: function (y) {
            if (typeof y !== "undefined") {
              return y.toFixed(0) + " points";
            }
            return y;
      
          }
        }
      },
      legend: {
        show: true,
      },
      };

      var chart = new ApexCharts(document.querySelector("#earnings"), options);
      chart.render();
}

var spark2 = {
    chart: {
        type: 'bar',
        height: 80,
        width: 150,
        sparkline: {
            enabled: true
        },
        dropShadow: {
            enabled: false,
            enabledOnSeries: undefined,
            top: 0,
            left: 0,
            blur: 0,
            color: '#000',
            opacity: 0
        }
    },
    grid: {
        show: false,
        xaxis: {
            lines: {
                show: false
            }
        },
        yaxis: {
            lines: {
                show: false
            }
        },
    },
    stroke: {
        show: true,
        curve: 'smooth',
        colors: undefined,
        width: 0.3,
        dashArray: 0,
    },
    fill: {
        gradient: {
            enabled: false
        }
    },
    series: [{
        name: 'Value',
        data: [0, 21, 54, 38, 56, 24, 65, 53, 67, 21, 54, 38]
    }],
    yaxis: {
        min: 0,
        show: false
    },
    xaxis: {
        show: false,
        axisTicks: {
            show: false
        },
        axisBorder: {
            show: false
        }
    },
    yaxis: {
        axisBorder: {
            show: false
        },
    },
    colors: ['#f56f4b'],

}
document.getElementById('analytics-visitors').innerHTML = '';
var spark2 = new ApexCharts(document.querySelector("#analytics-visitors"), spark2);
spark2.render();