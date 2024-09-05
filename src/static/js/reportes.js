$(document).ready(function(){
    $("#myInput").on("keyup", function() {
      var value = $(this).val().toLowerCase();
      $("#myTable tr").filter(function() {
        $(this).toggle($(this).text().toLowerCase().indexOf(value) > -1)
      });
    });
  });


$(document).ready(()=>{
    $("#generar_form").on("submit",(e)=>{
        e.preventDefault();
        console.log("Generar ha sido clickeado...");
        var  spinner = '<div class="spinner-border" role="status"><span class="sr-only">loading...</span></div>';
        $("#myBTn").html(spinner);
        $("#myBTn" ).prop( "disabled", true );
        $.ajax({
            url:"/generar",
            type:"POST",
            data: $("#generar_form").serialize(),
            success: function(response) {
            //var s = '<button id="myBTn" class="btn btn-lg btn-primary btn-block" type="button"> Register </button>';
            $("#myBTn").text("Register");
            $("#myBTn" ).prop( "disabled", false );
            window.location.reload();
            //$( "#myForm" ).prop( "disabled", false );
            console.log(response);
        },
        error: function(error) {
            console.log(error);
            window.location.reload();
        }
        });
    });
})

$(document).ready(function(){
    $('[data-toggle="popover"]').popover();
});

function DownloadFile() {
    file = input2.files[0];
    var numFiles = file.length;
    console.log(file)
    fr = new FileReader();
    fr.readAsDataURL(file);
    var blob = new Blob([file], { type: "application/xlsx" });
    var objectURL = window.URL.createObjectURL(blob);
    console.log(objectURL);
    if (navigator.appVersion.toString().indexOf('.NET') > 0) {
        window.navigator.msSaveOrOpenBlob(blob, 'myFileName.xlsx');
    } else {
        var link = document.createElement('a');
        link.href = objectURL;
        link.download = "myFileName.xlsx";
        document.body.appendChild(link);
        link.click();
        link.remove();
    }
}

 function DownloadFiles2() {
    var files = input2.files;
    var numFiles = files.length;
  
    for (var i = 0; i < numFiles; i++) {
      var file = files[i];
      var fr = new FileReader();
      fr.readAsDataURL(file);
      var blob = new Blob([file], { type: "application/xlsx" });
      var objectURL = window.URL.createObjectURL(blob);
  
      if (navigator.appVersion.toString().indexOf('.NET') > 0) {
        window.navigator.msSaveOrOpenBlob(blob, file.name);
      } else {
        var link = document.createElement('a');
        link.href = objectURL;
        link.download = file.name;
        document.body.appendChild(link);
        link.click();
        link.remove();
    }
  }
}
