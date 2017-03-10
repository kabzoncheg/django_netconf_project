from django.conf.urls import url

from . import views

app_name = 'get'

urlpatterns = [
    url(r'^$', views.single_set, name='index'),
    url(r'configurations/$', views.configurations_list, name='configurations_list'),
]
