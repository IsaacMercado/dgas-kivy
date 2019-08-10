from rest_framework import serializers
from gas_app.models import Estacion, Combustible, Vehiculo, Cola, Rebotado

class ColaSynSerializer(serializers.ModelSerializer):
	class Meta:
		model = Cola
		fields = (
			'combustible', 
			'vehiculo', 
			'cargado', 
			'created_at', 
			'last_modified_at'
			)