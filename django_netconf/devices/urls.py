from django.conf.urls import url

from . import views

app_name = 'devices'

urlpatterns = [
    url(r'^$', views.DeviceListView.as_view(), name='index'),
    url(r'^search/vrf_name/(?P<vrf_name>.+)/$', views.device_list_search_vrf_view, name='search_vrf'),
]