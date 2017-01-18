from django.conf.urls import url

from . import views

app_name = 'devices'

urlpatterns = [
    url(r'^$', views.device_list_view, name='index'),
    url(r'^search/(?P<match_context>.+)/(?P<match_value>.+)/$', views.device_list_search_universal, name='search'),
    url(r'^json/update/$', views.json_device_update, name='json_device_update'),
]
