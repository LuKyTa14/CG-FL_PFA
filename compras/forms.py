from django import forms
from .models import Compra, DetalleCompra

class CompraForm(forms.ModelForm):
    class Meta:
        model = Compra
        fields = ['proveedor', 'sucursal', 'observaciones']
        widgets = {
            'observaciones': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Ej: Remito N° 0001-00004512'}),
        }

class DetalleCompraForm(forms.ModelForm):
    class Meta:
        model = DetalleCompra
        fields = ['producto', 'cantidad', 'precio_costo']
        widgets = {
            'cantidad': forms.NumberInput(attrs={'min': '1', 'value': '1'}),
            'precio_costo': forms.NumberInput(attrs={'step': '0.01'}),
        }