from django import forms
from .models import Producto, Sede, EstadoProducto, Ubicacion


class EntradaInventarioForm(forms.Form):
    """
    Formulario para registrar una entrada de stock a una sede específica.
    Centraliza toda la validación de la vista registrar_entrada.
    """

    producto = forms.ModelChoiceField(
        queryset=Producto.objects.filter(activo=True).select_related('categoria', 'marca'),
        empty_label="-- Selecciona un producto --",
        label="Producto",
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    sede = forms.ModelChoiceField(
        queryset=Sede.objects.all(),
        empty_label="-- Selecciona una sede --",
        label="Sede",
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    cantidad = forms.IntegerField(
        min_value=1,  # Django rechaza 0 o negativos automáticamente
        label="Cantidad",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
    )

    estado = forms.ModelChoiceField(
        queryset=EstadoProducto.objects.all(),
        empty_label="-- Selecciona un estado --",
        label="Estado del producto",
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    ubicacion = forms.ModelChoiceField(
        queryset=Ubicacion.objects.all(),
        required=False,  # Opcional, igual que en el modelo
        empty_label="-- Sin ubicación específica --",
        label="Ubicación",
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    observaciones = forms.CharField(
        required=False,
        label="Observaciones",
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Opcional: notas sobre esta entrada...'
        }),
    )