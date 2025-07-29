from django.http import JsonResponse
from unidades.administracion.reporteVentas.controllers import ctrCaducidades
from unidades.administracion.reporteVentas.models import Productos, Caducidades
from datetime import datetime

# Create your views here.
#? Consultas para conexión con Odoo
def pullCaducidadesOdoo(request):
    try:
        productsPSQL = Productos.objects.all().values_list('id', flat=True)
        
        #Traer todos los clientes de Odoo
        clientesOdoo=ctrCaducidades.get_allCaducidades()
        
        if clientesOdoo['status'] == 'success':
            newCaducidad=0
            for caducidad in clientesOdoo['caducidades']:
                if caducidad['product_id'][0] in productsPSQL:
                    try:
                        fecha = datetime.strptime(caducidad['name'], "%d-%m-%Y")
                        Caducidades.objects.create(
                            fechaCaducidad = fecha,
                            cantidad = caducidad['product_qty'],
                            productoId_id = caducidad['product_id'][0]
                        )
                        newCaducidad=newCaducidad+1
                    except:
                        pass
                else:
                    pass
                    
            return JsonResponse({
                'status'  : 'success',
                'message' : f'Se registraron {newCaducidad}, nuevas caducidades'
            })
        else:
            return JsonResponse({
                'status'  : 'error',
                'message' : clientesOdoo['message']
            })
        
    except Exception as e:
        return JsonResponse({
            'status'  : 'error',
            'message' : f'Ha ocurrido un error al tratar de insertar los datos: {e}'
        })