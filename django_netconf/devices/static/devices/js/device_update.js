function device_update(id) {
    $.getJSON("/update/", { ip_address: id})
}
$('device_update_btn').click(function(){device_update(this.id)})