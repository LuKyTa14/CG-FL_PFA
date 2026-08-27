"""
URL configuration for GC_Fl project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', RedirectView.as_view(url='login/', permanent=False), name='index'),
    path('admin/', admin.site.urls),

    # RUTAS DE RECUPERACION DE CONTRASEÑA
    path('reset_password/', auth_views.PasswordResetView.as_view( template_name="users/password_reset_form.html"), name="reset_password"),
    path('reset_password_sent/', auth_views.PasswordResetDoneView.as_view(template_name="users/password_reset_done.html"), name="password_reset_done"),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name="users/password_reset_confirm.html"), name="password_reset_confirm"),
    path('reset_password_complete/', auth_views.PasswordResetCompleteView.as_view(template_name="users/password_reset_complete.html"), name="password_reset_complete"),

    # APLICACIONES (INCLUDES)
    path('', include('users.urls')), 
    path('', include('core.urls')),
    path('clientes/', include('clientes.urls', namespace='clientes')),
    path('proveedores/', include('proveedores.urls', namespace='proveedores')),
    path('inventario/', include('inventario.urls', namespace='inventario')),
    path('compras/', include('compras.urls', namespace='compras')),
    path('ventas/', include('ventas.urls', namespace='ventas')),
    path('contabilidad/', include('contabilidad.urls', namespace='contabilidad')),
]
