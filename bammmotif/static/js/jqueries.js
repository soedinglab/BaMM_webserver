//$("#select_all").change(function(){  //"select all" change
//    $(".checkbox").prop('checked', $(this).prop("checked")); //change all ".checkbox" checked status
//});

//".checkbox" change
$('.checkbox').change(function(){
    //uncheck "select all", if one of the listed checkbox item is unchecked
    if(false == $(this).prop("checked")){ //if this item is unchecked
        $("#select_all").prop('checked', false); //change "select all" checked status to false
    }
    //check "select all" if all checkbox items are checked
    if ($('.checkbox:checked').length == $('.checkbox').length ){
        $("#select_all").prop('checked', true);
    }
});

$(document).ready( function() {

    $("#about-btn").click( function(event) {
        alert("You clicked the button using JQuery!");
    });
});


$("#checkAll").click(function(){
    $('input:checkbox').not(this).prop('checked', this.checked);
});