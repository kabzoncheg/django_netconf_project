from django.conf.urls import url, include
from django.contrib import admin
from django.contrib.auth import views
from django.views.generic import RedirectView


urlpatterns = [
    url(r'^$', RedirectView.as_view(url='devices')),
    url(r'^admin/', admin.site.urls),
    url(r'^devices/', include('devices.urls')),
    url(r'^get/', include('get.urls', namespace='get')),
    url(r'^set/', include('set.urls', namespace='set')),
    url(r'^login/$', views.login, name='login'),
    url(r'^logout/$', views.logout, name='logout'),
]
