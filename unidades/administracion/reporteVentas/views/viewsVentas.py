from django.http import JsonResponse
from unidades.administracion.reporteVentas.models import Ventas
from unidades.administracion.reporteVentas.views.viewsLineaPV import pullLineaVentaOdoo
from unidades.administracion.reporteVentas.controllers import ctrVentas

# --------------------------------------------------------------------------------------------------
# * Función: pullVentasOdoo
# * Descripción: Obtiene los productos de la base de datos de Odoo y los inserta en la base de datos de PostgreSQL
#
# ! Parámetros:
#     - Recibe un request, que en este caso no se usa en el codigo, pero si agregarlo para su correcta funcion
#
# ? Condiciones para insertar una venta:
#     1. La venta debe tener un idVenta o nombre disponible en la base de datos de PostgreSQL.
#
# ? Lógica para determinar el venta:
#     - Si "move_type" es igual a "out_invoice", significa que es una venta completada.
#     - Si "move_type" es igual a "out_refund", significa que es una nota de crédito.
# --------------------------------------------------------------------------------------------------
def pullVentasOdoo(request):
    try:
        #Traer todos los clientes de Odoo
        ventasOdoo=ctrVentas.get_allSales()
        
        if ventasOdoo['status'] == 'success':
            
            ventasPSQL = Ventas.objects.all().values_list('idVenta', flat=True)
       
            newVentas = 0
            newNota = 0
            
            for venta in ventasOdoo['ventas']:
                try:
                    print(venta)
                    '''if venta['name'] not in ventasPSQL:
                        if any(line.get('product_id') is False for line in venta['productsLines']):
                            pass
                        else:
                            if venta['move_type'] == 'out_invoice':
                                newVentas=newVentas+1
                            if venta['move_type'] == 'out_refund':
                                newNota=newNota+1
                                #Asignamos la distribución de la información en sus respectivas variables
                            Ventas.objects.create(
                                idVenta         = venta['name'],
                                fecha           = venta['invoice_date'],
                                ciudadVenta     = venta['city'],
                                estadoVenta     = venta['state_id'],
                                paisVenta       = venta['country_id'],
                                unidad          = venta['branch_id'][1] if venta['branch_id'] else "",
                                vendedor        = venta['invoice_user_id'][1],
                                total           = venta['amount_total_signed'],
                                idCliente_id    = venta['partner_id'][0]
                            )
                                
                            pullventas=pullLineaVentaOdoo(venta['productsLines'], venta['name'], venta['invoice_date'])
                            if pullventas['status'] == "error":
                                return JsonResponse({
                                        'status': 'error',
                                        'message': f"{pullventas['message']}, {venta}"
                                    })'''
                            
                except Exception as e:
                    return JsonResponse({
                        'status': 'error',
                        'message': f'Error registrando ventas: {e}'
                    })
        
            return JsonResponse({
                'status'  : 'success',
                'message' : f'{newVentas} ventas nuevas y {newNota} nuevas notas de credito'
            })    
        
        else:
            return JsonResponse({
                'status'  : 'error',
                'message' : ventasOdoo['message']
            })
        
    except Exception as e:
        return JsonResponse({
            'status'  : 'error',
            'message' : f'Ha ocurrido un error en pull Ventas: {e}'
        })
















        
def createVentasOdoo(request):
    try:
        #Traer todos los clientes de Odoo
        ventasOdoo=ctrVentas.get_newSales()
        
        if ventasOdoo['status'] == 'success':
            
            ventasPSQL = Ventas.objects.all().values_list('idVenta', flat=True)
       
            newVentas = 0
            newNota = 0
            
            for venta in ventasOdoo['ventas']:
                try:
                    if venta['name'] not in ventasPSQL:
                        if any(line.get('product_id') is False for line in venta['productsLines']):
                            pass
                        else:
                            if venta['move_type'] == 'out_invoice':
                                newVentas=newVentas+1
                            if venta['move_type'] == 'out_refund':
                                newNota=newNota+1
                                #Asignamos la distribución de la información en sus respectivas variables
                            Ventas.objects.create(
                                idVenta         = venta['name'],
                                fecha           = venta['invoice_date'],
                                ciudadVenta     = venta['city'],
                                estadoVenta     = venta['state_id'],
                                paisVenta       = venta['country_id'],
                                unidad          = venta['branch_id'][1] if venta['branch_id'] else "",
                                vendedor        = venta['invoice_user_id'][1],
                                total           = venta['amount_total_signed'],
                                idCliente_id    = venta['partner_id'][0]
                            )
                                
                            pullventas=pullLineaVentaOdoo(venta['productsLines'], venta['name'], venta['invoice_date'])
                            if pullventas['status'] == "error":
                                return JsonResponse({
                                        'status': 'error',
                                        'message': f"{pullventas['message']}, {venta}"
                                    })
                            
                except Exception as e:
                    return JsonResponse({
                        'status': 'error',
                        'message': f'Error registrando ventas: {e}'
                    })
        
            return JsonResponse({
                'status'  : 'success',
                'message' : f'{newVentas} ventas nuevas y {newNota} nuevas notas de credito'
            })    
        
        else:
            return JsonResponse({
                'status'  : 'error',
                'message' : ventasOdoo['message']
            })
        
    except Exception as e:
        return JsonResponse({
            'status'  : 'error',
            'message' : f'Ha ocurrido un error en pull Ventas: {e}'
        })

def updateVentasOdoo(request):
    pass

def deleteVentasPSQL():
    pass



#? Consulta para crear ventas desde el excel compact
def createSalesExcel(request):
    try:
        #Traer todos los clientes de Odoo
        ventasOdoo=ctrVentas.pullVentasExcel()
        
        if ventasOdoo['status'] == 'success':            
            newVenta=0
            
            ventasPSQL = Ventas.objects.all().values_list('idVenta', flat=True)
            
            for venta in ventasOdoo['ventas']:
                if venta['idVenta'] not in ventasPSQL:
                    newVenta=newVenta+1
                    #Asignamos la distribución de la información en sus respectivas variables
                    Ventas.objects.create(
                        idVenta         = venta['idVenta'],
                        fecha           = venta['fecha'],
                        ciudadVenta     = venta['ciudadVenta'],
                        estadoVenta     = venta['estadoVenta'],
                        paisVenta       = venta['paisVenta'],
                        unidad          = venta['unidad'],
                        vendedor        = venta['vendedor'],
                        total           = venta['total'],
                        idCliente_id    = venta['idCliente']
                    )
                    pullventas=ctrVentas.pullLineaVentaExcel(venta["idVenta"], venta['fecha'])
                    if pullventas['status'] == "error":
                        return JsonResponse({
                                'status': 'error',
                                'message': f"{pullventas['message']}, {venta}"
                            })
                    ventaFinal = Ventas.objects.get(idVenta=venta['idVenta'])
                    ventaFinal.total=pullventas['total']
                    ventaFinal.save()
                    print(newVenta)
                        
            return JsonResponse({
                'status'  : 'success',
                'message' : f'Las ventas nuevas son: {newVenta}'
            })
        else:
            return JsonResponse({
                'status'  : 'error',
                'message' : ventasOdoo['message']
            })
        
    except Exception as e:
        return JsonResponse({
            'status'  : 'error',
            'message' : f'Ha ocurrido un error en createSalesExcel: {e}'
        })