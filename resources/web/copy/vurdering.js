$(function () {
  console.log("Document is ready");
  
  var vurdering = ["Meget dårlig", "Ganske dårlig", "Noe dårlig", "Hverken bra eller dårlig", "Noe bra", "Ganske bra", "Meget bra"];
  var semesterkoder = { 'H': 'høsten', 'V': 'våren' };
  var title_prefix = 'Generell vurdering fra ';
  var avg_score = {
    'V2009': 4.40,
    'H2009': 4.40,
    'V2010': 4.22,
    'H2010': 4.15,
    'V2011': 4.32,
    'H2011': 4.08,
    'V2012': 4.36,
    'H2012': 4.26,
    'V2013': 4.19,
    'H2013': 4.36,
    'V2014': 4.21,
    'H2014': 4.20,
    'V2015': 4.23,
    'H2015': 4.30,
    'V2016': 4.41,
    'H2016': 4.19,
    'V2017': 4.48,
    'H2017': 4.66,
    'V2018': 4.14,
    'H2018': 4.42,
    'V2019': 4.43,
    'H2019': 4.41,
    'V2020': 4.48,
    'H2020': 4.48,
    'V2021': 4.49,
    'H2021': 4.58,
    'V2022': 4.40,
    'H2022': 4.36,
    'V2023': 4.56,
    'H2023': 4.83,
    'V2024': 4.20
  };

  if (document.body.lang && document.body.lang === "en") {
      title_prefix = 'General rating since ';
      vurdering = ["Exceptionally bad", "Very bad", "Somewhat bad", "Neither good nor bad", "Somewhat good", "Very good", "Exceptionally good"];
      semesterkoder = { 'H': 'autumn', 'V': 'spring' };
  }

  var colorCycle = Highcharts.getOptions().colors;
  var courseColorMap = {};
  var currentColorIndex = 0;

  var courseRanges = {};

  $('.fui_vurdering').each(function (i, div) {
      var _this = $(this);
      var emnekode = _this.data('emnekode');
      var emnedata = $("#emnedata").html();  // Retrieve the embedded data here
      var seriesData = [];
      var allSemesters = new Set();  // Using a set to track unique semesters
      var avg_vurdering = [];

      var avgSeries = {
          name: 'Gjennomsnitt på Ifi',
          data: [],
          dashStyle: 'dot',
          marker: {
              enabled: false
          },
          color: 'black',
          visible: false
      };

      console.log("Processing emnekode:", emnekode);
      
      if (emnekode === "AVERAGE_SCORE") {
          emnedata = [];
          for (var key in avg_score) {
              emnedata.push([key, avg_score[key]]);
              allSemesters.add(key);
          }
          avgSeries.data = $.map(emnedata, function (value) {
              return value[1];
          });
          avgSeries.visible = true;
          seriesData.push(avgSeries);
      } else {
          if (!emnedata) {
              console.log('Ingen data for emnekode "' + emnekode + '"');
              return;
          }

          emnedata = JSON.parse(emnedata);
          var courseSeries = {};
          var courseData = {};

          $.each(emnedata, function (index, value) {
              var semester = value[0];
              var score = value[1];
              var course = value[2];

              console.log('Processing data point:', { semester, score, course });

              if (!courseSeries[course]) {
                  courseSeries[course] = {
                      name: course,
                      data: new Array([...allSemesters].length).fill(null),
                      color: courseColorMap[course] || (courseColorMap[course] = colorCycle[currentColorIndex++ % colorCycle.length])
                  };
                  courseData[course] = [];
              }

              courseData[course].push(semester);

              if (!allSemesters.has(semester)) {
                  allSemesters.add(semester);
              }

              if (!courseRanges[course]) {
                  courseRanges[course] = [];
              }
              courseRanges[course].push(semester);
          });

          allSemesters = [...allSemesters];

          console.log("All semesters:", allSemesters);

          $.each(emnedata, function (index, value) {
              var semester = value[0];
              var score = value[1];
              var course = value[2];

              var semesterIndex = allSemesters.indexOf(semester);
              courseSeries[course].data[semesterIndex] = score;

              avg_vurdering[semesterIndex] = avg_score[semester];
          });

          $.each(courseSeries, function (key, series) {
              seriesData.push(series);
          });

          allSemesters.forEach(function (semester, index) {
              if (avg_vurdering[index] === undefined) {
                  avg_vurdering[index] = avg_score[semester] || null;
              }
          });

          avgSeries.data = avg_vurdering;
          seriesData.push(avgSeries);
      }

      allSemesters.sort(function (a, b) {
          var yearA = parseInt(a.substring(1));
          var yearB = parseInt(b.substring(1));
          var termA = a.charAt(0);
          var termB = b.charAt(0);

          if (yearA === yearB) {
              return termA.localeCompare(termB);
          }
          return yearA - yearB;
      });

      var title = '';
      var semesterString = semesterkoder[('' + allSemesters[0]).substring(0, 1)];
      var divElement = $('<div />');

      if (semesterString) {
          title = title_prefix + semesterString + ' ' + allSemesters[0].substring(1);
          _this.html('<h2>' + title + '</h2>');
      }

      _this.append(divElement);
      var chart = divElement.highcharts({
          title: null,
          xAxis: {
              categories: allSemesters,
              labels: {
                  step: 1
              },
              crosshair: true
          },
          yAxis: {
              allowDecimals: false,
              min: 1,
              max: 7,
              title: null,
              opposite: false,
              tickInterval: 1,
              labels: {
                  formatter: function () {
                      return vurdering[this.value - 1];
                  }
              },
              plotLines: [{
                  value: 0,
                  width: 1,
                  color: '#808080'
              }]
          },
          tooltip: {
              enabled: false
          },
          legend: {
              layout: 'vertical',
              enabled: emnekode !== 'AVERAGE_SCORE'
          },
          credits: {
              enabled: false
          },
          exporting: {
              enabled: false
          },
          plotOptions: {
              series: {
                  animation: false,
                  events: {
                      legendItemClick: function (event) {
                          var series = this;
                          event.preventDefault();

                          series.setVisible(!series.visible, false);
                          updateSeriesVisibility();
                          return false;
                      }
                  }
              }
          },
          series: seriesData
      }).highcharts();

      function updateSeriesVisibility() {
          console.log("Updating series visibility...");

          var visibleCount = 0;
          var avgSeriesObj;

          chart.series.forEach(function (series) {
              if (series.userOptions.name !== 'Gjennomsnitt på Ifi') {
                  visibleCount += series.visible ? 1 : 0;
              } else {
                  avgSeriesObj = series;
              }
          });

          console.log("Number of visible series:", visibleCount);

          if (visibleCount === 0) {
              avgSeriesObj.setVisible(false, false);
          }

          adjustAxisExtremes();
      }

      function adjustAxisExtremes() {
        console.log("Adjusting axis extremes...");
    
        var currentSemesters = [];
    
        chart.series.forEach(function (series) {
            if (series.visible) {
                currentSemesters = currentSemesters.concat(courseRanges[series.name] || []);
            }
        });
    
        currentSemesters = Array.from(new Set(currentSemesters));
    
        console.log("Current visible semesters:", currentSemesters);
    
        currentSemesters.sort(function (a, b) {
            var yearA = parseInt(a.substring(1));
            var yearB = parseInt(b.substring(1));
            var termA = a.charAt(0);
            var termB = b.charAt(0);
    
            if (yearA === yearB) {
                return termA.localeCompare(termB);
            }
            return yearA - yearB;
        });
    
        var firstVisible = currentSemesters.length > 0 ? currentSemesters[0] : null;
        var lastVisible = currentSemesters.length > 0 ? currentSemesters[currentSemesters.length - 1] : null;
    
        console.log("First visible semester:", firstVisible);
        console.log("Last visible semester:", lastVisible);
    
        if (firstVisible !== null && lastVisible !== null) {
            var minIndex = allSemesters.indexOf(firstVisible);
            var maxIndex = allSemesters.indexOf(lastVisible);
    
            if (minIndex !== -1 && maxIndex !== -1) {
                var visibleDataPoints = maxIndex - minIndex + 1;
    
                if (visibleDataPoints <= 4) {
                    var centerIndex = Math.floor((minIndex + maxIndex) / 2);
                    var bufferPoints = Math.ceil(5 / 2); // Adjust this as needed
    
                    var newMin = Math.max(centerIndex - bufferPoints, 0);
                    var newMax = Math.min(centerIndex + bufferPoints, allSemesters.length - 1);
    
                    console.log("New centered extremes:", { min: newMin, max: newMax });
    
                    chart.xAxis[0].setExtremes(newMin, newMax, true);
                } else {
                    console.log("Setting default extremes:", { min: minIndex, max: maxIndex });
    
                    chart.xAxis[0].setExtremes(minIndex, maxIndex, true);
                }
            }
        } else {
            chart.xAxis[0].setExtremes(null, null, true);
        }
    
        chart.redraw();
    }
    
    // Trigger the function initially
    adjustAxisExtremes();
            
    updateSeriesVisibility();
  });
});
