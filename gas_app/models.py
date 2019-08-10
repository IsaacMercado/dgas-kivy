from django.db import models

COMBUSTIBLE_TIPO_CHOICES = (
	('91','91'), 
	('95','95'), 
	('Gasoil','Gasoil')
	)
MUNICIPIOS_CHOICES = (
	('Libertador','Libertador'), 
	('Campo Elias','Campo Elias'), 
	('Sucre','Sucre'), 
	('Santos Marquina','Santos Marquina')
	)

class Estacion(models.Model):
    nombre = models.CharField(max_length=100, blank=True, null=True)
    municipio = models.CharField(max_length=20, choices=MUNICIPIOS_CHOICES, default='Libertador')

    class Meta:
        ordering = ('nombre',)

    def __str__(self):
        return ('%s') % (self.nombre,)


class Combustible(models.Model):
    estacion = models.ForeignKey(Estacion, on_delete=models.CASCADE)
    tipo_combustible = models.CharField(max_length=10, choices=COMBUSTIBLE_TIPO_CHOICES)
    
    def __str__(self):
        return str(self.estacion.nombre)


class Vehiculo(models.Model):
    placa = models.CharField(max_length=7, primary_key=True, help_text='Sin espacio en blanco y letras en mayusculas')

    def __str__(self):
        return self.placa


class Cola(models.Model):
    combustible = models.ForeignKey(Combustible, on_delete=models.CASCADE, related_name='colas')
    vehiculo = models.ForeignKey(Vehiculo, on_delete=models.CASCADE)
    cantidad = models.FloatField(default=0)
    cargado = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    last_modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-last_modified_at',)
        unique_together = ('vehiculo', 'combustible',)

    def __str__(self):
        return str(self.vehiculo.placa)


class Rebotado(models.Model):
    combustible = models.ForeignKey(Combustible, on_delete=models.CASCADE, related_name='rebotados')
    vehiculo = models.ForeignKey(Vehiculo, on_delete=models.CASCADE)