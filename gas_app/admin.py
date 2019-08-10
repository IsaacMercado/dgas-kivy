from django.contrib import admin
from .models import Estacion, Combustible, Vehiculo, Cola


class CombustibleInline(admin.TabularInline):
    model = Combustible

@admin.register(Estacion)
class EstacionAdmin(admin.ModelAdmin):
    inlines = [CombustibleInline]


@admin.register(Combustible)
class CombustibleAdmin(admin.ModelAdmin):
    list_display = ('estacion', 'tipo_combustible')


@admin.register(Vehiculo)
class VehiculoAdmin(admin.ModelAdmin):
    list_display = ('placa',)
    search_fields = ['placa']

@admin.register(Cola)
class ColaAdmin(admin.ModelAdmin):
    list_display = ('vehiculo', 'cargado', 'cantidad', 'created_at', 'last_modified_at')
    search_fields = ['vehiculo__placa',]
