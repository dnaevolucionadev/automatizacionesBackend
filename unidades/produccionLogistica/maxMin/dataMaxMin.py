from django.http import JsonResponse
from django.db.models import F, ExpressionWrapper, FloatField, Subquery, OuterRef, Sum, Count, Value, Case, When, Q
from datetime import datetime
from dateutil.relativedelta import relativedelta

from unidades.produccionLogistica.maxMin.models import Insumos, MaterialPI
from unidades.administracion.reporteVentas.models import VentasPVA
from unidades.produccionLogistica.maxMin.views.viewInsumo import updateMaxMin


insumosNoCompartidosUpdated = []
insumosCompartidosUpdated   = []
insumos_dict                = {}


def calculationUnsharedInput(inputs, inputsPSQL):
    for insumo in inputs:
        #Obtenemos el insumo que se va a actualizar
        insumoActual = inputsPSQL.get(insumo['insumo_id_ref'])

        if insumoActual:
            #Realizamos el cálculo del máximo y del mínimo.
            if insumo['insumo_promedio'] == None:
                tiempoEntrega = 0
            else:
                tiempoEntrega = insumo['insumo_promedio'] * (insumo['tiempo_entrega'] / 30)
            
            if insumo['insumo_promedio'] == None:
                newMinQty = tiempoEntrega
                newMaxQty = newMinQty + tiempoEntrega
            else:
                newMinQty = (insumo['insumo_promedio'] * 1.5) + tiempoEntrega
                newMaxQty = newMinQty + tiempoEntrega + insumo['insumo_promedio']

            #Actualizamos en las bases de datos
            updateMaxMin(insumoActual, newMaxQty, newMinQty)

            #print(response1)
            insumosNoCompartidosUpdated.append(insumo)

            #break  #! Para solo trabajar con uno

def addAverageSalesSI(inputs):
    for insumo in inputs:
        nombre = insumo['nombre_insumo']
        if nombre in insumos_dict:
            if insumos_dict[nombre]['insumo_promedio'] == None:
                insumos_dict[nombre]['insumo_promedio'] = insumo['insumo_promedio']
            else:
                if insumo['insumo_promedio'] != None:
                    insumos_dict[nombre]['insumo_promedio'] += insumo['insumo_promedio']
        else:
            insumos_dict[nombre] = insumo.copy()



#!Actualizar máximos y mínimos de Odoo. 
def updateMinMax(request):
    try:
        #? Traemos los datos que son necesarios 
        #? Primero hacemos la subconsulta del promedio de ventas de los productos para el tercer trimestre mayor al del año pasado
        hoy = datetime.now()
        año = hoy.year
        mes = hoy.month

        if mes in [1, 2, 3]:
            fecha_nueve_meses = datetime(año - 1, 4, 1)
            fecha_seis_meses = datetime(año - 1, 6, 30)
        elif mes in [4, 5, 6]:
            fecha_nueve_meses = datetime(año - 1, 7, 1)
            fecha_seis_meses = datetime(año - 1, 9, 30)
        elif mes in [7, 8, 9]:
            fecha_nueve_meses = datetime(año - 1, 10, 1)
            fecha_seis_meses = datetime(año - 1, 12, 31)
        else:
            fecha_doce_meses = datetime(año, 1, 1)
            fecha_seis_meses = datetime(año, 3, 31)
        
        fecha_doce_meses = datetime(año-1, mes, 1)
        if mes in [1, 2, 3, 4, 5, 6]:
            fecha_menor_6_meses = datetime(año - 1, mes - 6, 1)
        else:
            fecha_menor_6_meses = datetime(año, mes - 6, 1)
        
        if mes in [1, 2, 3]:
            fecha_menor_3_meses = datetime(año - 1, mes, 1)
        else:
            fecha_menor_3_meses = datetime(año, mes, 1)
        
        fecha_doce_meses = datetime.now() - relativedelta(month=12)

        ventas12meses_subquery = VentasPVA.objects.filter(
            idProducto = OuterRef('producto_id'),
            #fecha__year = datetime.now().year - 1
            fecha__gte = fecha_nueve_meses,
            fecha__lte = fecha_seis_meses
        ).values('idProducto_id').annotate(
            total_ventas=Sum('cantidad'), 
            meses=Count('fecha__month', distinct=True)
        ).annotate(
            promedio_ventas=ExpressionWrapper(
                Case(
                    When(meses__gt=0, then=F('total_ventas') / F('meses')),
                    default=Value(0),
                    output_field=FloatField()
                ),
                output_field=FloatField()        
            )
        ).values('promedio_ventas')[:1]


        #? Subconsulta para promedio de ventas de productos que no cuentan con 12 meses de 
        #? ventas pero que pasan de los 3 meses.
        ventasMenores12meses_subquery = VentasPVA.objects.filter(
            idProducto = OuterRef('producto_id'),
            fecha__gte=fecha_menor_3_meses
        ).values('idProducto_id').annotate(
            total_ventas=Sum('cantidad'),
            meses=Count('fecha__month', distinct=True)
        ).annotate(
            promedio_ventas=ExpressionWrapper(
                Case(
                    When(meses__gt=0, then=F('total_ventas') / F('meses')),
                    default=Value(0),
                    output_field=FloatField()
                ),
                output_field=FloatField()
            )
        ).values('promedio_ventas')[:1]

        #? Consulta completa de todos los productos cons sus insumos cuando los insumos no son compartidos.
        #? Y que tengan más de 12 meses de existencia
        #Me arroja la cantidad de insumos promedio que se necesitan para crear los productos vendidos.

        #! Consulas para productos con mas de 12 meses de registro
        insumosUnicos12meses = MaterialPI.objects.select_related('producto', 'insumo').filter(
            Q(producto__tipoProducto='INTERNO RESURTIBLE') &
            ~Q(insumo__sku__icontains='00') &
            Q(producto__fechaCreacion__lt=fecha_doce_meses)
        ).annotate(
            promedio_ventas=Subquery(ventas12meses_subquery),
            insumo_promedio=ExpressionWrapper(
                F('promedio_ventas') * F('cantidad'),
                output_field=FloatField()
            )
        ).values(
            producto_id_ref=F('producto__id'),
            nombre_producto=F('producto__nombre'),
            marca=F('producto__marca'),
            insumo_id_ref=F('insumo__id'),
            cantidad_final=F('cantidad'),
            nombre_insumo=F('insumo__nombre'),
            sku=F('insumo__sku'),
            tiempo_entrega=F('insumo__tiempoEntrega'),
            insumo_promedio=F('insumo_promedio')
        ).order_by('producto__nombre')


        #? Insumos compartidos
        insumosCompartidos12meses = MaterialPI.objects.select_related('producto', 'insumo').filter(
            Q(producto__tipoProducto='INTERNO RESURTIBLE') &
            Q(insumo__sku__icontains='00') &
            Q(producto__fechaCreacion__lt=fecha_doce_meses)
        ).annotate(
            promedio_ventas=Subquery(ventas12meses_subquery),
            insumo_promedio=ExpressionWrapper(
                F('promedio_ventas') * F('cantidad'),
                output_field=FloatField()
            )
        ).values(
            producto_id_ref=F('producto__id'),
            nombre_producto=F('producto__nombre'),
            marca=F('producto__marca'),
            insumo_id_ref=F('insumo__id'),
            cantidad_final=F('cantidad'),
            nombre_insumo=F('insumo__nombre'),
            sku=F('insumo__sku'),
            tiempo_entrega=F('insumo__tiempoEntrega'),
            insumo_promedio=F('insumo_promedio')
        ).order_by('producto__nombre')

        #! Consultas para productos con menos de 12 meses de registro
        insumosUnicosMenor12meses = MaterialPI.objects.select_related('producto', 'insumo').filter(
            Q(producto__tipoProducto='INTERNO RESURTIBLE') &
            ~Q(insumo__sku__icontains='00') &
            Q(producto__fechaCreacion__gte=fecha_doce_meses) &
            Q(producto__fechaCreacion__lt=fecha_seis_meses)
        ).annotate(
            promedio_ventas=Subquery(ventasMenores12meses_subquery),
            insumo_promedio=ExpressionWrapper(
                F('promedio_ventas') * F('cantidad'),
                output_field=FloatField()
            )
        ).values(
            producto_id_ref=F('producto__id'),
            nombre_producto=F('producto__nombre'),
            marca=F('producto__marca'),
            insumo_id_ref=F('insumo__id'),
            cantidad_final=F('cantidad'),
            nombre_insumo=F('insumo__nombre'),
            sku=F('insumo__sku'),
            tiempo_entrega=F('insumo__tiempoEntrega'),
            insumo_promedio=F('insumo_promedio')
        ).order_by('producto__nombre')

        #? Insumos compartidos
        insumosCompartidosMenor12meses = MaterialPI.objects.select_related('producto', 'insumo').filter(
            Q(producto__tipoProducto='INTERNO RESURTIBLE') &
            Q(insumo__sku__icontains='00') &
            Q(producto__fechaCreacion__gte=fecha_doce_meses) &
            Q(producto__fechaCreacion__lt=fecha_menor_6_meses)
        ).annotate(
            promedio_ventas=Subquery(ventasMenores12meses_subquery),
            insumo_promedio=ExpressionWrapper(
                F('promedio_ventas') * F('cantidad'),
                output_field=FloatField()
            )
        ).values(
            producto_id_ref=F('producto__id'),
            nombre_producto=F('producto__nombre'),
            marca=F('producto__marca'),
            insumo_id_ref=F('insumo__id'),
            cantidad_final=F('cantidad'),
            nombre_insumo=F('insumo__nombre'),
            sku=F('insumo__sku'),
            tiempo_entrega=F('insumo__tiempoEntrega'),
            insumo_promedio=F('insumo_promedio')
        ).order_by('producto__nombre')


        #! Sacamos los minimos y máximos de todos los productos
        #? Traemos todos los insumos para poder actualizarlos
        insumosPSQL = list(Insumos.objects.all())
        insumosForUpdated = {i.id: i for i in insumosPSQL}


        #!Realizamos el cálculo para los insumos no compartidos
        calculationUnsharedInput(insumosUnicos12meses, insumosForUpdated)
        calculationUnsharedInput(insumosUnicosMenor12meses, insumosForUpdated)


        #! Sumar ventas promedio de los insumos compartidos
        addAverageSalesSI(insumosCompartidos12meses)
        addAverageSalesSI(insumosCompartidosMenor12meses)
                

        #?Ya tengo la lista con insumos compartidos juntos.
        insumosCompartidosJuntos = list(insumos_dict.values())

        #! Cálculo de máximo y mínimo para insumos compartidos
        for insumoCompartido in insumosCompartidosJuntos:
            insumoActual = insumosForUpdated.get(insumoCompartido['insumo_id_ref'])
            if insumoActual:
                if insumoCompartido['tiempo_entrega'] == 0:
                    tiempoEntrega = 10
                else:
                    tiempoEntrega = insumoCompartido['insumo_promedio'] * (insumoCompartido['tiempo_entrega'] / 30)

                if insumoCompartido['insumo_promedio'] == None:
                    newMinQty = tiempoEntrega
                    newMaxQty = newMinQty + tiempoEntrega
                else:
                    newMinQty = (insumoCompartido['insumo_promedio'] * 1.5) + tiempoEntrega
                    newMaxQty = newMinQty + tiempoEntrega + insumoCompartido['insumo_promedio']

                #Actualizamos en las bases de datos
                updateMaxMin(insumoActual, newMaxQty, newMinQty)
                insumosCompartidosUpdated.append(insumoCompartido)


        return JsonResponse({
            'status'         : 'success', 
            'no_compartidos' : insumosNoCompartidosUpdated,
            'compartidos'    : insumosCompartidosUpdated
        })

    except Exception as e:
        return JsonResponse({
            'status'       : 'error',
            'message'      : f'Ha ocurrido un error al tratar de insertar los datos: {str(e)}'
        })