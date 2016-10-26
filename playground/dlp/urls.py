from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'home/',views.home, name='home'),

    url(r'login/', views.userlogin, name='login'),
    url(r'logout/', views.userlogout, name='logout'),

    url(r'register/(?P<invite>[-\w]+)', views.register, name='register'),
    url(r'register/', views.register, name='register'),

    url(r'cms/', views.content_mgmt, name='content_mgmt'),

    url(r'manage/', views.manage, name='manage'),

    url(r'module/(?P<storage>[-\w]+)', views.module, name='module'),
    url(r'module/', views.module, name='module'),

    url(r'message/(?P<message_id>[-\w]+)', views.message, name='message'),
    url(r'message/', views.message, name='message'),

    url(r'profile/', views.profile, name='profile'),

]