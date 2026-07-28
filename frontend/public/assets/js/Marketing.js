var randomizeArray = function (arg) {
  var array = arg.slice();
  var currentIndex = array.length, temporaryValue, randomIndex;
  
  while (0 !== currentIndex) {

    randomIndex = Math.floor(Math.random() * currentIndex);
    currentIndex -= 1;

    temporaryValue = array[currentIndex];
    array[currentIndex] = array[randomIndex];
    array[randomIndex] = temporaryValue;
  }

  return array;
}
// data for the sparklines that appear below header area
var sparklineData = [47, 45, 54, 48, 56, 44, 65, 31, 37, 39, 62, 51, 35, 41, 35, 27, 33, 53, 61, 27, 54, 43, 19, 46,];

// spark1
function spark1() {
var spark1 = {
    chart: {
      id: 'sparkline1',
      group: 'sparklines',
      type: 'area',
      height:60,
      sparkline: {
        enabled: true
      },
    },
    stroke: {
      curve: 'straight',
      width: 2,
    },
    fill: {
      opacity: 1,
    },
    series: [{
      name: 'Revenue',
      data: randomizeArray(sparklineData)
    }],
    labels: [...Array(24).keys()].map(n => `2018-09-0${n+1}`),
    xaxis: {
      type: 'datetime',
    },
    yaxis: {
      min: 0
    },
		tooltip: {
		  enabled: false,
		},
    colors: ["rgb(" + myVarVal + ")"],
  }
new ApexCharts(document.querySelector("#spark1"), spark1).render();
}
// spark1

// spark2
var spark2 = {
  chart: {
    id: 'sparkline2',
    group: 'sparklines',
    type: 'area',
    height:60,
    sparkline: {
      enabled: true
    },
  },
  stroke: {
    curve: 'straight',
    width: 2,
  },
  fill: {
    opacity: 1,
  },
  series: [{
    name: 'Marketig Spend',
    data: randomizeArray(sparklineData)
  }],
  labels: [...Array(24).keys()].map(n => `2018-09-0${n+1}`),
  xaxis: {
    type: 'datetime',
  },
  yaxis: {
    min: 0
  },
  tooltip: {
    enabled: false,
  },
  colors: ["#e9ac04"],
}
new ApexCharts(document.querySelector("#spark2"), spark2).render();
// spark2

// spark3
var spark3 = {
  chart: {
    id: 'sparkline3',
    group: 'sparklines',
    type: 'area',
    height:60,
    sparkline: {
      enabled: true
    },
  },
  stroke: {
    curve: 'straight',
    width: 2,
  },
  fill: {
    opacity: 1,
  },
  series: [{
    name: 'Profits',
    data: randomizeArray(sparklineData)
  }],
  labels: [...Array(24).keys()].map(n => `2018-09-0${n+1}`),
  xaxis: {
    type: 'datetime',
  },
  yaxis: {
    min: 0
  },
  tooltip: {
    enabled: false,
  },
  colors: ["#2dc3fc"],
}
new ApexCharts(document.querySelector("#spark3"), spark3).render();
// spark3

// spark4
var spark4 = {
  chart: {
    id: 'sparkline4',
    group: 'sparklines',
    type: 'area',
    height:60,
    sparkline: {
      enabled: true
    },
  },
  stroke: {
    curve: 'straight',
    width: 2,
  },
  fill: {
    opacity: 1,
  },
  series: [{
    name: 'Investment',
    data: randomizeArray(sparklineData)
  }],
  labels: [...Array(24).keys()].map(n => `2018-09-0${n+1}`),
  xaxis: {
    type: 'datetime',
  },
  yaxis: {
    min: 0
  },
  tooltip: {
    enabled: false,
  },
  colors: ["#ff5c77"],
}
new ApexCharts(document.querySelector("#spark4"), spark4).render();
// spark4

// visitors
function visitors() {
  'use strict'

setTimeout(()=>{
  var options = {
    series: [{
      name: 'New Visitors',
      data: [44, 42, 57, 86, 58, 55, 70, 43, 23, 54, 77, 34],
      },{
      name: 'Returning Visitors',
      data: [-34, -22, -37, -56, -21, -35, -60, -34, -56, -78, -89,-53],
    }],
    chart: {
      stacked: true,
      type: 'bar',
      height: 322,
      toolbar: {
        show: false
      }
    },
    grid: {
        borderColor: '#f2f6f7',
      },
    colors: ["rgba(" + myVarVal + ", 0.95)", ,"#e9ac04"],
    plotOptions: {
      bar: {
        borderRadius: 0,
        borderRadiusOnAllStackedSeries: true,
        colors: {
          ranges: [{
          from: -100,
          to: -46,
          color: '#e9ac04'
          }, {
          from: -45,
          to: 0,
          color: '#e9ac04'
          }]
        },
        columnWidth: '28%',
      }
    },
    dataLabels: {
      enabled: false,
    },
    legend: {
      show: false,
      position: 'top',
      fontFamily:"Mulish",
      markers: {
        width: 10	,
        height: 10,
      }
    },
    yaxis: {
      title: {
        text: 'Growth',
          style: {
            color: '	#adb5be',
            fontSize: '14px',
            fontFamily: 'Mulish',
            fontWeight: 600,
            cssClass: 'apexcharts-yaxis-label',
          },
        },
    },
    xaxis: {
      type: 'month',
      categories: ['Jan','Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'sep', 'oct', 'nov', 'dec'],
      axisBorder: {
            show: true,
            color: 'rgba(119, 119, 142, 0.05)',
            offsetX: 0,
            offsetY: 0,
          },
          axisTicks: {
            show: true,
            borderType: 'solid',
            color: 'rgba(119, 119, 142, 0.05)',
            width: 6,
            offsetX: 0,
            offsetY: 0
          },
      labels: {
        rotate: -90
      }
    }
  };
  document.getElementById('visitors').innerHTML = ''
  var chart = new ApexCharts(document.querySelector("#visitors"), options);
  chart.render();
}, 300);
}
// visitors

// sparkline-1
function sparkline1() {
  var crm1 = {
      chart: {
          type: 'line',
          height: 28,
          width: 100,
          sparkline: {
              enabled: true
          }
      },
      stroke: {
          show: true,
          curve: 'smooth',
          lineCap: 'butt',
          colors: undefined,
          width: 2,
          dashArray: 0,
      },
      series: [{
          name: 'Value',
          data: [20, 14, 15, 10, 23, 20, 22, 9, 12]
      }],
      yaxis: {
          min: 0,
          show: false,
          axisBorder: {
              show: false
          },
      },
      xaxis: {
          show: false,
          axisBorder: {
              show: false
          },
      },
      tooltip: {
          enabled: false,
      },
      colors: ["rgb(" + myVarVal + ")"],

  }
  document.getElementById('sparkline-1').innerHTML = '';
  var crm1 = new ApexCharts(document.querySelector("#sparkline-1"), crm1);
  crm1.render();
}

var crm1 = {
  chart: {
      type: 'line',
      height: 28,
      width: 100,
      sparkline: {
          enabled: true
      }
  },
  stroke: {
      show: true,
      curve: 'smooth',
      lineCap: 'butt',
      colors: undefined,
      width: 2,
      dashArray: 0,
  },
  series: [{
      name: 'Value',
      data: [20, 14, 15, 10, 23, 20, 22, 9, 12]
  }],
  yaxis: {
      min: 0,
      show: false,
      axisBorder: {
          show: false
      },
  },
  xaxis: {
      show: false,
      axisBorder: {
          show: false
      },
  },
  tooltip: {
      enabled: false,
  },
  colors: ["#e9ac04"],

}
document.getElementById('sparkline-2').innerHTML = '';
var crm1 = new ApexCharts(document.querySelector("#sparkline-2"), crm1);
crm1.render();


var crm1 = {
  chart: {
      type: 'line',
      height: 28,
      width: 100,
      sparkline: {
          enabled: true
      }
  },
  stroke: {
      show: true,
      curve: 'smooth',
      lineCap: 'butt',
      colors: undefined,
      width: 2,
      dashArray: 0,
  },
  series: [{
      name: 'Value',
      data: [20, 14, 15, 10, 23, 20, 22, 9, 12]
  }],
  yaxis: {
      min: 0,
      show: false,
      axisBorder: {
          show: false
      },
  },
  xaxis: {
      show: false,
      axisBorder: {
          show: false
      },
  },
  tooltip: {
      enabled: false,
  },
  colors: ["#2dc3fc"],

}
document.getElementById('sparkline-3').innerHTML = '';
var crm1 = new ApexCharts(document.querySelector("#sparkline-3"), crm1);
crm1.render();


var crm1 = {
  chart: {
      type: 'line',
      height: 28,
      width: 100,
      sparkline: {
          enabled: true
      }
  },
  stroke: {
      show: true,
      curve: 'smooth',
      lineCap: 'butt',
      colors: undefined,
      width: 2,
      dashArray: 0,
  },
  series: [{
      name: 'Value',
      data: [20, 14, 15, 10, 23, 20, 22, 9, 12]
  }],
  yaxis: {
      min: 0,
      show: false,
      axisBorder: {
          show: false
      },
  },
  xaxis: {
      show: false,
      axisBorder: {
          show: false
      },
  },
  tooltip: {
      enabled: false,
  },
  colors: ["#ff5c77"],

}
document.getElementById('sparkline-4').innerHTML = '';
var crm1 = new ApexCharts(document.querySelector("#sparkline-4"), crm1);
crm1.render();


var crm1 = {
  chart: {
      type: 'line',
      height: 28,
      width: 100,
      sparkline: {
          enabled: true
      }
  },
  stroke: {
      show: true,
      curve: 'smooth',
      lineCap: 'butt',
      colors: undefined,
      width: 2,
      dashArray: 0,
  },
  series: [{
      name: 'Value',
      data: [20, 14, 15, 10, 23, 20, 22, 9, 12]
  }],
  yaxis: {
      min: 0,
      show: false,
      axisBorder: {
          show: false
      },
  },
  xaxis: {
      show: false,
      axisBorder: {
          show: false
      },
  },
  tooltip: {
      enabled: false,
  },
  colors: ["#28c76f"],

}
document.getElementById('sparkline-5').innerHTML = '';
var crm1 = new ApexCharts(document.querySelector("#sparkline-5"), crm1);
crm1.render();