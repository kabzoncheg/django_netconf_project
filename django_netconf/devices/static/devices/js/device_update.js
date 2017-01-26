function device_update(element) {
    var ip_address = element.attr('aria-label');
    var parent = $('.well[aria-label="'+ip_address+'"]');
    var children = parent.children('.device_description_container')
    var old_content = children.html();
    children.html(function () {
        return ""+
                '<div class="progress progress-striped active">' +
                    '<div class="progress-bar" style="width: 100%"></div>' +
                '</div>';
    })
    $.getJSON('/devices/json/update/', { ip_address: ip_address}, function(json){
        if (json['status'] == true){
            children.html(function(){
                var last_checked_status = 'DOWN';
                if (json['last_checked_status'] == true){
                    last_checked_status = 'UP';
                }
                return ""+
                    '<p><b>Description: </b>'+json['description']+'</p>' +
                    '<p><b>Hostname: </b>'+json['hostname']+'</p>' +
                    '<p><b>Model: </b>'+json['model']+'</p>' +
                    '<p><b>UP time: </b>'+json['up_time']+'</p>' +
                    '<p><b>Updated at: </b>'+Date(json['last_checked_time'])+'</p>' +
                    '<p><b>Status: </b>'+last_checked_status+'</p>';
            })
        } else {
            children.html(old_content);
            alert('Can not update device with IP address: ' + ip_address)
        }
    })
}

function device_update_detail(element) {
    var ip_address = element.attr('aria-label');
    var content = $('.content_detail');
    var old_content = content.html();
    content.html(function () {
        return ""+
                '<div class="progress progress-striped active">' +
                    '<div class="progress-bar" style="width: 100%"></div>' +
                '</div>';
    })
    $.getJSON('/devices/json/update/', { ip_address: ip_address}, function(json){
    if (json['status'] == true){
        content.html(function(){
            var last_checked_status = 'DOWN';
            if (json['last_checked_status'] == true){
                last_checked_status = 'UP';
            }
            return ""+
                '<p><b>Description: </b>'+json['description']+'</p>' +
                '<p><b>Hostname: </b>'+json['hostname']+'</p>' +
                '<p><b>FQDN: </b>'+json['fqdn']+'</p>' +
                '<p><b>Model: </b>'+json['model']+'</p>' +
                '<p><b>Has 2 Routing Engines: </b>'+json['two_re']+'</p>' +
                '<p><b>Software version: </b>'+json['version']+'</p>' +
                '<p><b>Serial number: </b>'+json['serialnumber']+'</p>' +
                '<p><b>UP time: </b>'+json['up_time']+'</p>' +
                '<p><b>Updated at: </b>'+Date(json['last_checked_time'])+'</p>' +
                '<p><b>Status: </b>'+last_checked_status+'</p>';
        })
    } else {
        content.html(old_content);
        alert('Can not update device with IP address: ' + ip_address)
    }
    })

}