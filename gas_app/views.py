from gas_app.models import Estacion, Combustible, Vehiculo, Cola, Rebotado
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.authentication import TokenAuthentication

import json
from datetime import datetime, timedelta
import pytz


class ColaList(APIView):

    permission_classes = (IsAuthenticated,)
    authentication_classes = (TokenAuthentication,)

    def get(self, request):
        #print("Load GET")

        content = {'message': 'not action'}
        action = request.GET.get('action', '')

        if action and action == 'update':
            date_rq = request.GET.get('date', '')
            date = datetime.strptime(date_rq, "%Y-%m-%dT%H:%M:%S.%f").replace(tzinfo=pytz.UTC)

            # Change for serializer
            content = [{
                "placa": car.vehiculo.placa, 
                "created_at": car.created_at.strftime("%Y-%m-%dT%H:%M:%S.%f"), 
                "estacion": car.combustible.estacion.id } for car in Cola.objects.filter(created_at__gt=date)]

        elif action and action == 'stations':
            content = [[sta.id, sta.nombre] for sta in Estacion.objects.all()]

        return Response(json.dumps(content))

    def post(self, request):
        #print("Load POST")
        content = {'cargado': False}
        json_data = json.loads(request.body)

        for obj in json_data:
            car, ccar = Vehiculo.objects.get_or_create(placa=obj['pl'])
            station = Estacion.objects.get(id=obj['ie'])

            # Seleccion el ultimo combustible creado de la estacion
            #con = Combustible.objects.filter(estacion=es, tipo_combustible='91').last()
            con = Combustible.objects.filter(estacion=station).last()

            if obj['ir']:
                Rebotado.objects.create(combustible=con, vehiculo=car)
                #print(con, car)
            else:
                cdate = datetime.strptime(obj['ca'],"%Y-%m-%dT%H:%M:%S.%f")
                Cola.objects.create(combustible=con, vehiculo=car, cargado=True, created_at=cdate)
                #print(con, car, cdate)
        
        content['cargado'] = True
        return Response(json.dumps(content))