from django.conf.urls import url

from . import views

app_name = 'get'

urlpatterns = [
    url(r'^$', views.single_set, name='index'),
    url(r'configurations/$', views.configurations_list, name='configurations_list'),
    url(r'configurations/(?P<config_id>[0-9]+)', views.configurations_detail, name='configurations_detail'),
    url(r'json/delete-configuration/$', views.json_configurations_delete, name='json_delete_configurations'),
]
