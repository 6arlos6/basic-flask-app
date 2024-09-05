
function alerttt(variable){
alert(variable);
};

require([
  "esri/config",
  "esri/Map",
  "esri/views/MapView",
  "esri/layers/FeatureLayer",
  "esri/PopupTemplate",
  "esri/popup/content/CustomContent",
  "esri/layers/GeoJSONLayer",
], (esriConfig, Map, MapView, FeatureLayer, PopupTemplate, CustomContent,GeoJSONLayer) => {
  esriConfig.apiKey = "AAPKa2dbdbde39d84cf8ac4acb0d8edb8598rsyTw6OM9nmHMPCUmUM2fxN8qMJnJHfEM9neqk8U0VA5GXxfWADmNWlTDH0Gq_j4";
  const map = new Map({
      basemap: "osm-light-gray",
  });
  const view = new MapView({
      container: "viewDiv",
      map: map,
      center: [-75.68323997743963, 5.261287383930011],
      zoom: 6,
      popup: {
          dockEnabled: true,
          dockOptions: {
              buttonEnabled: false,
              breakpoint: false,
          },
      },
      
  });

const featureLayer = new GeoJSONLayer({
    url: "/data"
});
const featureLayer_2=new GeoJSONLayer({
    url:"/mun"});

zoom=view.watch('zoom', zoomChanged);

function zoomChanged(newValue, oldValue, property, object){
      var number = newValue;
      document.getElementById("myText").innerHTML = number;
      if(number>=11){  
      map.add(featureLayer_2); 
      featureLayer_2.popupTemplate = template; 
      map.remove(featureLayer);
        }

        else{
      map.remove(featureLayer_2);
      featureLayer.popupTemplate = template;
      map.add(featureLayer);
        }
};

  let customContent = new CustomContent({
      outFields: ["*"],
      creator: (event) => {
          console.log("in custom content");
          // Call method to create chart with your own information.
          // Use event.graphic value to reference current feature.
          let canvas = createChart();
          //const div = document.getElementById("chart-div");
          let div = document.createElement("div");
          div.appendChild(canvas);
          // Return the div element containing the chart.
          return div;
      },
  });

  // Create the PopupTemplate and reference custom content element.
  const template = new PopupTemplate({
      outFields: ["*"],
      title: "Información Socioeconómica",
      content: [customContent],
  });

  featureLayer.popupTemplate = template;
  map.add(featureLayer);
  // Example here: https://tobiasahlin.com/blog/chartjs-charts-to-get-you-started/#2-line-chart
  let lineChart;

  function createChart() {
      let canvas = document.createElement("canvas");
      canvas.style.width = "100%";
      canvas.style.height = "100%";
      canvas.width = 416;
      canvas.height = 208;
      const ctx = canvas.getContext("2d");
      const config = {
                  type: 'bar',
                  data: {
                      labels: ["1", "2", "3", "4", "5", "6"],
                      datasets: [{
                        label: "Estrato",
                        data: [20, 40, 30, 35, 30, 20],
                        backgroundColor: ['yellow', 'aqua', 'pink', 'lightgreen', 'lightblue', 'gold'],
                        borderColor: ['red', 'blue', 'fuchsia', 'green', 'navy', 'black'],
                        borderWidth: 2,
                      }],
                  },
                  options: {
                      responsive: false,
                  },
                };
      console.log("creating chart");
      lineChart = new Chart(canvas, config);
      return canvas;
  }
});