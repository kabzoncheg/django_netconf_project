from django.conf.urls import url

from . import views

app_name = 'get'

urlpatterns = [
    url(r'^$', views.single_get, name='index'),
    url(r'chains/$', views.chain_list, name='chain_list'),
    url(r'chains/create/$', views.chain_create, name='chain_create'),
    url(r'chains/(?P<name>.+)', views.chain_detail, name='chain_detail'),
]
