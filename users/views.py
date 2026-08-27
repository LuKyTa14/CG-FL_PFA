from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import LoginForm
from .models import UserRole, Role
from .forms import PerfilForm
from core.models import Sucursal


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('dashboard')
            else:
                messages.error(request, 'Incorrecto usuario o contraseña.')
        # Si no es válido, el form sigue su curso y se renderiza con los errores.
    else:
        form = LoginForm()

    return render(request, 'users/login.html', {'form': form})


@login_required
def logout_view(request): 
    logout(request)
    messages.success(request, 'Cierre de Sesión Exitoso.')
    return redirect('login')

# VER PERFIL
@login_required
def perfil_usuario(request):
    usuario = request.user
    
    # Traemos todas las sucursales de la base de datos
    sucursales = Sucursal.objects.all()
    
    rol = "Sin rol asignado"
    if hasattr(usuario, 'userrole_set') and usuario.userrole_set.exists():
        rol = usuario.userrole_set.first().role.role_name

    if request.method == 'POST':
        form = PerfilForm(request.POST, instance=usuario)
        if form.is_valid():
            form.save()
            messages.success(request, "Tus datos han sido actualizados correctamente.")
            return redirect('perfil')
    else:
        form = PerfilForm(instance=usuario)

    # Agregamos las sucursales al diccionario de contexto
    context = {
        'form': form,
        'usuario': usuario,
        'rol': rol,
        'sucursales': sucursales,
    }
    
    return render(request, 'users/perfil.html', context)