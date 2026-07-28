 //avgsales//
  function index1() {
    var options = {
      series: [70],
      chart: {
      height: 260,
      type: 'radialBar',
    },
    colors: ["rgba(" + myVarVal + ", 0.95)",   "rgba(" + myVarVal + ", 0.15)",],
    plotOptions: {
      radialBar: {
        hollow: {
          size: '47%',
        }
      },
    },
    labels: ['Active users'],
    };
  var chart2 = new ApexCharts(document.querySelector("#avgsales"), options);
  chart2.render();
  
  }
   //avgsales//

// Statistics Chart//
function balance() {
    var options = {
        series: [{
            name: 'Income',
            data: [90, 95, 108, 92, 106, 92, 89, 93, 103, 88, 93, 108,88, 99, 100, 129, 92, 108, 97, 105, 108,83,94, 100,],
		}, {
			name: 'Expances',
			data: [100, 108, 128, 140, 110, 125, 105, 118, 120, 145, 105, 125,100, 128, 128, 140, 120, 140, 128, 128, 140, 148, 125, 129,]
		}],
        chart: {
            type: 'area',
            height: 324
        },
        grid: {
            borderColor: 'rgba(167, 180, 201 ,0.2)',
        },
		colors: [ "rgba(" + myVarVal + ", 0.95)",  "rgba(" + myVarVal + ", 0.5)"],
		markers: {
			size: [0,0],
			strokeColors: '#fff',
			strokeWidth: [0, 0],
			strokeOpacity: 0,
		},
		stroke: {
			curve: 'smooth',
			width: 1,
			dashArray: [0, 4]
		},
		// fill: {
		// 	type: ['gradient','gradient'],
		// 	gradient: {
		// 		shade: 'light',
		// 		type: "vertical",
		// 		opacityFrom: [0.6, 0.5],
		// 		opacityTo: [0.2, 0.1],
		// 		stops: [0, 100]
		// 	}
		// },
        dataLabels: {
            enabled: false,
        },
        legend: {
            show: false,
			position: 'top',
            labels: {
                colors: '#74767c',
            },
        },
        yaxis: {
            labels: {
                formatter: function (y) {
                    return y.toFixed(0) + "";
                }
            },
            labels: {
                style: {
                    colors: "#8c9097",
                    fontSize: '11px',
                    fontWeight: 600,
                    cssClass: 'apexcharts-xaxis-label',
                },
            }
        },
        xaxis: {
            type: 'month',
            categories: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'sep', 'oct', 'nov', 'dec','Jan', 'Feb', 'Mar', 'Apr', 'May','Jun', 'Jul', 'Aug', 'sep','oct', 'nov', 'dec'],
            axisBorder: {
                show: true,
                color: 'rgba(167, 180, 201 ,0.2)',
                offsetX: 0,
                offsetY: 0,
            },
            axisTicks: {
                show: true,
                borderType: 'solid',
                color: 'rgba(167, 180, 201 ,0.2)',
                width: 6,
                offsetX: 0,
                offsetY: 0
            },
            labels: {
                rotate: -90,
                style: {
                    colors: "#8c9097",
                    fontSize: '11px',
                    fontWeight: 600,
                    cssClass: 'apexcharts-xaxis-label',
                },
            }
        }
    };
    document.getElementById('balance').innerHTML = '';
    var chart1 = new ApexCharts(document.querySelector("#balance"), options);
    chart1.render();
}
   //Statistics Chart//

   // Active-timeline  scroll //
   var myHeaderCart = document.getElementById('activiti-timeline');
   new SimpleBar(myHeaderCart, { autoHide: true });
   // Active-timeline  scroll //

   // projectAnalysis  //
   function projectAnalysis() {
    var options = {
        series: [{
            name: 'Online',
            type: 'column',
            data: [20, 29, 37, 35, 44, 43, 50]
        }, {
            name: 'Offline',
            type: 'bar',
            data: [10, 15, 17, 15, 12, 20, 28],
        }
        ],
        chart: {
            toolbar: {
                show: false
            },
            height: 310,
            type: 'line',
            stacked: false,
            fontFamily: 'Poppins, Arial, sans-serif',
        },
        grid: {
            borderColor: '#f5f4f4',
            strokeDashArray: 2
        },
        dataLabels: {
            enabled: false
        },
        title: {
            text: undefined,
        },
        xaxis: {
            categories: ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'],
        },
        yaxis: [
            {
                show: true,
                axisTicks: {
                    show: true,
                },
                axisBorder: {
                    show: false,
                    color: '#4eb6d0'
                },
                labels: {
                    style: {
                        colors: '#4eb6d0',
                    }
                },
                title: {
                    text: undefined,
                },
                tooltip: {
                    enabled: true
                }
            },
            {
                seriesName: 'Online',
                opposite: true,
                axisTicks: {
                    show: true,
                },
                axisBorder: {
                    show: false,
                },
                labels: {
                    style: {
                        colors: '#00E396',
                    }
                },
                title: {
                    text: undefined,
                },
            },
        ],
        tooltip: {
            enabled: true,
        },
        legend: {
            show: false,
        },
        stroke: {
            width: [0, 0, 0],
            curve: 'smooth',
            dashArray: [0, 0, 0],
        },
        plotOptions: {
            bar: {
                columnWidth: "40%",
                borderRadius: 1
            }
        },
        colors: ["rgb(" + myVarVal + ")",  "rgba(233, 172, 4, 0.4)"]
    };
    document.querySelector("#projectAnalysis").innerHTML = " ";
    var chart1 = new ApexCharts(document.querySelector("#projectAnalysis"), options);
    chart1.render();
}

  // projectAnalysis  //