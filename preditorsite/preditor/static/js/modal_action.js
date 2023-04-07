jQuery(document).ready(function($) {
    $(".clickable-row").click(function() {
        $.ajax({
            type: 'GET',
            url: '/mapa_json/'+$(this).data("href"),
            success: function (data) {
              console.log("foi...")
              limpar_gif()
              console.log(data)
              var element = document.getElementById("mapa");
              element.innerHTML = data['my_map_modal']
              var tipo = document.getElementById("tipo_map");
              tipo.innerHTML = data['tipo']
            },
            error: function (err) {
                console.log("não foi...")
                console.log(err);
              },
          });
    });

});

jQuery(document).ready(function($) {
    $(".clickable-row-mara-geral").click(function() {
        $.ajax({
            type: 'GET',
            url: '/mapa_json_geral/'+$(this).data("href"),
            success: function (data) {
              console.log("foi...")
              limpar_gif()
              console.log(data)
              var element = document.getElementById("mapa");
              element.innerHTML = data['my_map_modal']
              var tipo = document.getElementById("tipo_map");
              tipo.innerHTML = data['tipo']
            },
            error: function (err) {
                console.log("não foi...")
                console.log(err);
              },
          });
    });

});

jQuery(document).ready(function($) {
    $(".clickable-testeindice").click(function() {
        $.ajax({
            type: 'GET',
            url: '/mapateste_json/'+$(this).data("href"),
            success: function (data) {
              console.log("foi...")
              limpar_gif()
              console.log(data)
              var element = document.getElementById("mapa");
              element.innerHTML = data['my_map_modal']
              var tipo = document.getElementById("erro");
              tipo.innerHTML = data['erro']
            },
            error: function (err) {
                console.log("não foi...")
                console.log(err);
              },
          });
    });

});

jQuery(document).ready(function($) {
    $(".clickable-row-dados").click(function() {
    var $pieChart = $("#pie-chart");
    var $pieTestChart = $("#pietest-chart");
    var $pieTrainChart = $("#pietrain-chart");
        $.ajax({
            type: 'GET',
            url: '/dados_json/'+$(this).data("href"),
            success: function (data) {
              console.log("foi...")
              limpar_gif()
              console.log(data)
              var element = document.getElementById("modelo");
              element.innerHTML = data['modelo']
              var element = document.getElementById("desc_modelo");
              element.innerHTML = data['desc_modelo']

              //chart
              var ctx = $pieChart[0].getContext("2d");
                var myChart = new Chart(ctx, {
                  type: "pie",
                  data: {
                    labels: data.pie_total_class,
                    datasets: [
                      {
                        label: "Vars",
                        data: data.pie_total_data,
                        backgroundColor: [
                        '#00FF00', '#DAA520', '#F4A460', '#7B68EE', '#FF00FF', '#800000', '#FF0000', '#FFFF00'
                        ],
                      }
                    ],
                  },
                  options: {
                      responsive: true,
                      legend: {
                        position: 'top',
                      },
                      title: {
                        display: true,
                        text: 'Total de dados'
                      }
                  }
                });

                //chart
              var ctx = $pieTestChart[0].getContext("2d");
                var myChartTest = new Chart(ctx, {
                  type: "pie",
                  data: {
                    labels: data.pie_test_class,
                    datasets: [
                      {
                        label: "Vars",
                        data: data.pie_test_data,
                        backgroundColor: [
                        '#00FF00', '#DAA520', '#F4A460', '#7B68EE', '#FF00FF', '#800000', '#FF0000', '#FFFF00'
                        ],
                      }
                    ],
                  },
                  options: {
                      responsive: true,
                      legend: {
                        position: 'top',
                      },
                      title: {
                        display: true,
                        text: 'Dados de Testes'
                      },
                  }
                });

                 //chart
              var ctx = $pieTrainChart[0].getContext("2d");
                var myChartTest = new Chart(ctx, {
                  type: "pie",
                  data: {
                    labels: data.pie_y_class,
                    datasets: [
                      {
                        label: "Vars",
                        data: data.pie_y_data,
                        backgroundColor: [
                        '#00FF00', '#DAA520', '#F4A460', '#7B68EE', '#FF00FF', '#800000', '#FF0000', '#FFFF00'
                        ],
                      }
                    ],
                  },
                  options: {
                      responsive: true,
                      legend: {
                        position: 'top',
                      },
                      title: {
                        display: true,
                        text: 'Dados de Treinamento'
                      }
                  }
                });
            },
            error: function (err) {
                console.log("não foi...")
                console.log(err);
              },
          });
    });

});

jQuery(document).ready(function($) {
    $(".clickable-row-sum").click(function() {
        var $barChart = $("#bar-chart");
        $.ajax({
            type: 'GET',
            url: '/summary_json/'+$(this).data("href"),
            success: function (data) {
              console.log("foi...")
              limpar_gif()
              console.log(data)
              var element = document.getElementById("arq");
              element.innerHTML = data['arq']
              var element = document.getElementById("desc_arq");
              element.innerHTML = data['desc_arq']

              //chart
              var ctx = $barChart[0].getContext("2d");
                var myChart = new Chart(ctx, {
                  type: "horizontalBar",
                  data: {
                    labels: data.vars,
                    datasets: [
                      {
                        label: "Vars",
                        data: data.imp,
                        backgroundColor: "rgba(116,96,238,0.6)",
                      }
                    ],
                  },
                  options: {
                      responsive: true,
                      legend: {
                        position: 'top',
                      },
                      title: {
                        display: true,
                        text: 'Importância das Variáveis'
                      }
                  }
                });
              //var tipo = document.getElementById("tipo_map");
              //tipo.innerHTML = data['tipo']
            },
            error: function (err) {
                console.log("não foi...")
                console.log(err);
              },
          });
    });

});

jQuery(document).ready(function($) {
    $(".clickable-row-cm").click(function() {
         $.ajax({
            type: 'GET',
            url: '/url_image/'+$(this).data("href"),
            async: false,
            crossDomain: 'true',
            success: function (data, status) {
              console.log("foi...")
              limpar_gif()
              /* PUT THIS INSIDE AJAX SUCCESS */
              const parent = document.getElementById("ibagem");
              const child = document.getElementById("image_id");
              parent.removeChild(child);
              var img = $('<img id="image_id">');
              img.attr('src', data.url);
              img.appendTo('#ibagem');
              },
            error: function (err) {
                console.log("não foi...")
                console.log(err);
              },
          });
    });
});


function getMesagem(mesagem, tipo){
  const Toast = Swal.mixin({
    toast: true,
    position: 'top-end',
    showConfirmButton: false,
    timer: 3000,
    timerProgressBar: true,
    didOpen: (toast) => {
      toast.addEventListener('mouseenter', Swal.stopTimer)
      toast.addEventListener('mouseleave', Swal.resumeTimer)
    }
  })
  
  Toast.fire({
    icon: tipo,
    title: mesagem
  })
}

function fecharmodel(){
  edicao =true;
}

function mostra_oculta(){
  var x = document.getElementById("pan_carrega");
  if (x.style.display === "none") {
      x.style.display = "block";
  } else {
      x.style.display = "none";
  }

}

function limpar() {
	console.log("foi...")
	var element = document.getElementById("mapa");
    element.innerHTML = "Aguarde..."
}

function limpar_gif() {
	console.log("foi...")
	var element = document.getElementById("gif");
    element.innerHTML = ""
}