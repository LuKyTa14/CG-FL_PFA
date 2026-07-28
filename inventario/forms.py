from django import forms
from .models import Producto

class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        # El stock vive en la tabla Inventario
        fields = ['codigo', 'marca', 'nombre', 'categoria', 'precio_costo', 'precio_venta', 'activo']