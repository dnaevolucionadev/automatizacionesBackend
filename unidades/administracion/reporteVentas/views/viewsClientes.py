from django.http import JsonResponse
from unidades.administracion.reporteVentas.models import Clientes
from unidades.administracion.reporteVentas.controllers import ctrCliente

# --------------------------------------------------------------------------------------------------
# * Función: insertProducts
# * Descripción: Inserta productos en la base de datos PostgreSQL.
#
# ! Parámetros:
#     - Recibe una lista (array) de cleintes. Cada cliente debe contener los siguientes campos:
#       { id, name, city, state_id, country_id, sale_order_count }
#     - Nota: Solo el campo "id" es obligatorio; los demás son opcionales.
#
# ? Condiciones para insertar un producto en la base de datos:
#     1. El cliente debe un id único.
#
# --------------------------------------------------------------------------------------------------
def insertClients(clients):
    clientesPSQL = Clientes.objects.all().values_list('idCliente', flat=True)
            
    newClientes = 0
    
    for cliente in clients:
        if cliente['id'] not in clientesPSQL:
            #Asignamos la distribución de la información en sus respectivas variables
            Clientes.objects.create(
                idCliente           = cliente['id'],
                nombre              = cliente['name'] if cliente['name']!=False else "",
                ciudad              = cliente['city'] if cliente['city']!=False else "",
                estado              = cliente['state_id'][1] if cliente['state_id']!=False else "",
                pais                = cliente['country_id'][1] if cliente['country_id']!=False else "",
                tipoCliente         = "Cartera" if cliente['sale_order_count']>=2 else "Cliente Nuevo",
                numTransacciones    = cliente['sale_order_count']
            )
            newClientes=newClientes+1
    
    return JsonResponse({
        'status'  : 'success',
        'message' : f'Los clientes son: {newClientes}'
    })
    

# --------------------------------------------------------------------------------------------------
# * Función: pullClientesOdoo
# * Descripción: Obtiene todos los clientes de Odoo y llama a la función de insertar datos
#
# ! Parámetros:
#     - request. Como se utiliza para URLS, recibe la información de la consulta
#
# ? Returns:
#     - Caso error:
#           Ocurre algún error en traer a los clientes de Odoo
#           La función insertClients retorna mensaje de error
#           Ocurre una excepción en la ejecución del código
#     - Caso success:
#           La función insertClients retorna mensaje success y envía mensaje con la cantidad de clientes agregados
# --------------------------------------------------------------------------------------------------
def pullClientesOdoo(request):
    try:
        print(0)
        #Trae todos los clientes de la base de datos
        clientesOdoo=ctrCliente.get_allClients()
        print(1)
        
        if clientesOdoo['status'] == 'success':
            print(2)
            response=insertClients(clientesOdoo['clientes'])
            if response['status'] == "success":
                print(3)
                return JsonResponse({
                    'status'  : 'success',
                    'message' : f'Se han agregado correctamente {response['message']} Clientes nuevos'
                })
            return JsonResponse({
                'status'  : 'error',
                'message' : response['message']
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























#? Consultas para crear a los nuevos cliente de odoo
def createClientesOdoo(request):
    try:
        #Traer todos los clientes de Odoo
        clientesOdoo=ctrCliente.get_newClients()
        
        if clientesOdoo['status'] == 'success':
            
            clientesPSQL = Clientes.objects.all().values_list('idCliente', flat=True)
            
            newClientes = 0
            
            for cliente in clientesOdoo['clientes']:
                
                if cliente['id'] not in clientesPSQL:
                    #Asignamos la distribución de la información en sus respectivas variables
                    Clientes.objects.create(
                        idCliente           = cliente['id'],
                        nombre              = cliente['name'] if cliente['name']!=False else "",
                        ciudad              = cliente['city'] if cliente['city']!=False else "",
                        estado              = cliente['state_id'][1] if cliente['state_id']!=False else "",
                        pais                = cliente['country_id'][1] if cliente['country_id']!=False else "",
                        tipoCliente         = "Cartera" if cliente['sale_order_count']>=2 else "Cliente Nuevo",
                        numTransacciones    = cliente['sale_order_count']
                    )
                    newClientes=newClientes+1
            
            return JsonResponse({
                'status'  : 'success',
                'message' : f'Los clientes nuevos son: {newClientes}'
            })
        else:
            return JsonResponse({
                'status'  : 'error',
                'message' : clientesOdoo['message']
            })
        
    except Exception as e:
        return JsonResponse({
            'status'  : 'error',
            'message' : f'Ha ocurrido un error al tratar de insertar los datos de los nuevos clientes: {e}'
        })

#? Consultas para actualizar a los clientes de odoo que se acualizaron un dia antes
def updateClientesOdoo(request):
    try:
        #Traer todos los clientes de Odoo
        clientesOdoo=ctrCliente.update_Clients()
        
        if clientesOdoo['status'] == 'success':
            newClientes = 0
            
            for cliente in clientesOdoo['clientes']:
                try:
                    clienteAct = Clientes.objects.get(idCliente=cliente['id'])
                    
                    clienteAct.nombre              = cliente['name'] if cliente['name']!=False else ""
                    clienteAct.ciudad              = cliente['city'] if cliente['city']!=False else ""
                    clienteAct.estado              = cliente['state_id'][1] if cliente['state_id']!=False else ""
                    clienteAct.pais                = cliente['country_id'][1] if cliente['country_id']!=False else ""
                    clienteAct.tipoCliente         = "Cartera" if cliente['sale_order_count']>=2 else "Cliente Nuevo"
                    clienteAct.numTransacciones    = cliente['sale_order_count']
                    
                    clienteAct.save()
                    newClientes=newClientes+1
                except:
                    pass
            
            return JsonResponse({
                'status'  : 'success',
                'message' : f'Los clientes son: {newClientes}'
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
    
def deleteClientesPSQL(request):
    return None











#? Consulta para crear clientes desde el excel compact
def createClientesExcel(request):
    try:
        clientesPSQL = Clientes.objects.all().values_list('idCliente', flat=True)
        #Traer todos los clientes de Odoo
        clientesOdoo=ctrCliente.pullClientsExcel(clientesPSQL)
        
        if clientesOdoo['status'] == 'success':
            
            newClientes=0
            
            for cliente in clientesOdoo['clientes']:
                #Asignamos la distribución de la información en sus respectivas variables
                Clientes.objects.create(
                    idCliente           = cliente['id'],
                    nombre              = cliente['name'] if cliente['name']!=False else "",
                    ciudad              = cliente['city'] if cliente['city']!=False else "",
                    estado              = cliente['state_id'][1] if cliente['state_id']!=False else "",
                    pais                = cliente['country_id'][1] if cliente['country_id']!=False else "",
                    tipoCliente         = "Cartera" if cliente['sale_order_count']>=2 else "Cliente Nuevo",
                    numTransacciones    = cliente['sale_order_count']
                )
                newClientes=newClientes+1

            
            return JsonResponse({
                'status'  : 'success',
                'message' : f'Los clientes nuevos son: {newClientes}'
            })
        else:
            return JsonResponse({
                'status'  : 'error',
                'message' : clientesOdoo['message']
            })
        
    except Exception as e:
        return JsonResponse({
            'status'  : 'error',
            'message' : f'Ha ocurrido un error al tratar de insertar los datos de los nuevos clientes: {e}'
        })