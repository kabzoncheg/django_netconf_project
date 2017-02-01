from django.conf.urls import url

from . import views

app_name = 'devices'

urlpatterns = [
    url(r'^$', views.device_list, name='index'),
    url(r'^detail/(?P<ip_address>.+)/$', views.device_detail, name='detail'),
    url(r'^instances/(?P<ip_address>.+)/$', views.device_instances, name='instances'),
    url(r'^rib/(?P<ip_address>.+)/$', views.device_rib, name='rib'),
    url(r'^arp/(?P<ip_address>.+)/$', views.device_arp, name='arp'),
    url(r'^routes/(?P<ip_address>.+)/$', views.device_routes, name='routes'),
    url(r'^interfaces/(?P<ip_address>.+)/$', views.device_interfaces, name='interfaces'),
    url(r'^sub-interfaces/(?P<ip_address>.+)/$', views.device_sub_interfaces, name='sub_interfaces'),
    url(r'^search/(?P<match_context>.+)/(?P<match_value>.+)/$', views.device_list_search_universal, name='search'),
    url(r'^json/update/$', views.json_device_update, name='json_device_update'),
]
