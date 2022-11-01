jQuery(document).ready(function($) {
    $(".clickable-row").click(function() {
        $.ajax({
            type: 'GET',
            url: '/mapa_json/'+$(this).data("href"),
            success: function (data) {
              console.log("foi...")
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
    $(".clickable-row-sum").click(function() {
        $.ajax({
            type: 'GET',
            url: '/summary_json/'+$(this).data("href"),
            success: function (data) {
              console.log("foi...")
              console.log(data)
              var element = document.getElementById("arq");
              element.innerHTML = data['arq']
              var element = document.getElementById("desc_arq");
              element.innerHTML = data['desc_arq']
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