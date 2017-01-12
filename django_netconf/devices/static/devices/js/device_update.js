function device_update(ip_addr) {
    $.getJSON("/devices/json/update/", { ip_address: ip_addr}, function(json){
        alert('Was request successfull? ' + json['status'] + json['ip_address']
        +' at time: '+ json['last_checked_time'])
    })
}