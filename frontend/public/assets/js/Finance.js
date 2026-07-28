 //applicantStats//
var options = {
	chart: {
		height: 330,
		type: "line",
		stacked: false,
        fontFamily: 'poppins, sans-serif',
	},
	dataLabels: {
		enabled: false
	},
	colors: ['000', '#F9F871'],
	series: [{
		name: 'Revenue',
		type: 'column',
		data: [106, 100, 130, 132, 114, 112, 225, 128, 87, 100, 253, 167],
	}, {
		name: "Expense",
		type: "column",
		data: [92, 75, 123, 111, 196, 122, 159, 102, 138, 136, 62, 240]
	}],
	stroke: {
		width: [0, 0,],
		  curve: 'smooth'
	},
	plotOptions: {
		bar: {
			columnWidth: '25%',
		}
	},
	markers: {
		size: [0, 0, 3],
		colors: undefined,
		strokeColors: "#000",
		strokeOpacity: 0.6,
		strokeDashArray: 0,
		fillOpacity: 1,
		discrete: [],
		shape: "circle",
		radius: [0, 0, 2],
		offsetX: 0,
		offsetY: 0,
		onClick: undefined,
		onDblClick: undefined,
		showNullDataPoints: true,
		hover: {
			size: undefined,
			sizeOffset: 3
		}
	},
	fill: {
		opacity: [1, 1]
	},
	grid: {
		borderColor: '#f2f6f7',
	},
	legend: {
		show: true,
		position: 'top',
		fontWeight: 500,
		fontSize: 13,
		markers: {
			width: 10,
			height: 10,
			shape: 'square',
			radius: 5,
		}
	},
	yaxis: {
		min: 0,
		forceNiceScale: true,
		title: {
			style: {
				color: '#adb5be',
				fontSize: '14px',
				fontFamily: 'poppins, sans-serif',
				fontWeight: 600,
				cssClass: 'apexcharts-yaxis-label',
			},
		},
		labels: {
			formatter: function (y) {
				return y.toFixed(0) + "";
			}
		}
	},
	toolbar:{
		show: false,
	},
	xaxis: {
		type: 'month',
		categories: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
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
	},
	tooltip: {
		enabled: true,
		shared: false,
		intersect: true,
		x: {
			show: false
		}
	},
};
var chart1 = new ApexCharts(document.querySelector("#applicantStats"), options);
chart1.render();
function applicantStats() {
	chart1.updateOptions({
		colors: ["rgb(" + myVarVal + ")", "#e9ac04"],
	})
}
 //applicantStats//

 //Budgetoverview//
 function Budgetoverview() {
    var options = {
      series: [80],
      chart: {
      height: 260,
      type: 'radialBar',
    },
    colors: ["rgba(" + myVarVal + ", 0.95)",   "rgba(" + myVarVal + ", 0.15)",],
    plotOptions: {
      radialBar: {
        hollow: {
          size: '68%',
        }
      },
    },
    labels: ['Active users'],
    };
  var chart2 = new ApexCharts(document.querySelector("#Budgetoverview"), options);
  chart2.render();
  
  }
   //Budgetoverview//
   
 //Budgetoverview//
    var options = {
      series: [75],
      chart: {
      height: 260,
      type: 'radialBar',
    },
    colors: ["#e9ac04"],
    plotOptions: {
      radialBar: {
        hollow: {
          size: '68%',
        }
      },
    },
    labels: ['Active users'],
    };
  var chart2 = new ApexCharts(document.querySelector("#Budgetexpense"), options);
  chart2.render();
   //Budgetoverview//