from django import forms
from .models import Venta, DetalleVenta

class VentaForm(forms.ModelForm):
    class Meta:
        model = Venta
        fields = ['cliente', 'sucursal', 'metodo_pago', 'observaciones']
        widgets = {
            'observaciones': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Opcional...'}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Hacemos que el cliente no sea obligatorio en el formulario visual (Consumidor Final)
        self.fields['cliente'].required = False

class DetalleVentaForm(forms.ModelForm):
    class Meta:
        model = DetalleVenta
        fields = ['producto', 'cantidad']
        widgets = {
            'cantidad': forms.NumberInput(attrs={'min': '1', 'value': '1'}),
        }