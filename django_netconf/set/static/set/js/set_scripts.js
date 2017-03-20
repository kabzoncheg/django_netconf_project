function configuration_delete() {
    var config_id_array = [];
    $('.chain_table_row input:checked').each(function () {
        var config_id = $(this).attr('aria-label');
        config_id_array.push(config_id);
    })
    var config_id_string = JSON.stringify(config_id_array);
    $.getJSON('/set/json/delete-configuration/', { config_id_list: config_id_string }, function(json){
        for (var elt in json) {
            var single_request_status = json[elt];
            if (single_request_status == true) {
                $('.chain_table_row[aria-label="'+elt+'"]').remove();
            }
        }
    })
}

function chain_delete() {
    var chain_id_array = [];
    $('.chain_table_row input:checked').each(function () {
        var chain_id = $(this).attr('aria-label');
        chain_id_array.push(chain_id);
    })
    var chain_id_string = JSON.stringify(chain_id_array);
    $.getJSON('/get/json/delete-chain/', { chain_id_list: chain_id_string }, function(json){
        for (var elt in json) {
            var single_request_status = json[elt];
            if (single_request_status == true) {
                $('.chain_table_row[aria-label="'+elt+'"]').remove();
            }
        }
    })
}