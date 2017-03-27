from django.conf.urls import url

from . import views

app_name = 'set'

urlpatterns = [
    url(r'^$', views.single_set, name='index'),
    url(r'chains/$', views.chain_list, name='chain_list'),
    url(r'chains/create/$', views.chain_create, name='chain_create'),
    url(r'chains/name/(?P<name>.+)', views.chain_detail, name='chain_detail'),
    url(r'configurations/$', views.configurations_list, name='configurations_list'),
    url(r'configurations/(?P<config_id>[0-9]+)', views.configurations_detail, name='configurations_detail'),
    url(r'json/delete-configuration/$', views.JsonConfigurationsDelete.as_view(), name='json_delete_configurations'),
    url(r'json/delete-chain/$', views.JsonSetChainDelete.as_view(), name='json_delete_chain'),
    url(r'json/delete-request/$', views.JsonSetRequestDelete.as_view(), name='json_delete_request'),
]
