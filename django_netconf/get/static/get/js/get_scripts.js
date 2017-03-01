function request_delete() {
    var request_id_array = [];
    $('.request_checkbox input:checked').each(function () {
        var request_id = $(this).attr('aria-label');
        request_id_array.push(request_id)
        var table_row = $(this).parent().parent();
        table_row.remove();
    })
    $.getJSON('/get/json/delete-chain-request/', { request_id_list: request_id_array }, function(json){

    })
    $('.pika').text(request_id_array);
}
