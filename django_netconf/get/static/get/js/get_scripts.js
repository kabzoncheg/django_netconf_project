function request_delete() {
    var request_id_array = [];
    $('.request_table_row input:checked').each(function () {
        var request_id = $(this).attr('aria-label');
        request_id_array.push(request_id);
    })
    var request_id_string = JSON.stringify(request_id_array);
    $.getJSON('/get/json/delete-chain-request/', { request_id_list: request_id_string }, function(json){
        for (var elt in json) {
            var single_request_status = json[elt];
            if (single_request_status == true) {
                $('.request_table_row[aria-label="'+elt+'"]').remove();
            }
        }
    })
}
