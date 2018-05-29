$(document).ready(function(){

	// https://stackoverflow.com/a/18537624/2272172
	$("#checkAll").change(function(){
	    $('input:checkbox').not(this).prop('checked', this.checked);
	});
});
