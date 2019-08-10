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
        print("Load GET")

        content = [{'message': 'Hello, World! GET'}]
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
        print("Load POST")
        content = [{'message': 'Hello, World! POST'}]
        json_data = json.loads(request.body)
        #print(json_data)
        # Create view
        return Response(json.dumps(content))