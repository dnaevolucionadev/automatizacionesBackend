import xmlrpc.client
from conexiones.conectionOdoo import OdooAPI
from datetime import datetime, timedelta
import pandas as pd
from unidades.administracion.reporteVentas.models import VentasPVH, VentasPVA
from unidades.produccionLogistica.maxMin.models import Productos

#?Intancia de conexión a Odoo
conn=OdooAPI()

#?Obtiene un archivo mendiante la url y lo abre en la pestaña necesaria para su posterior lectura
archivo = 'C:/Users/DSWB-PC02/Downloads/ContpaqBD.xlsx'
dfVenta = pd.read_excel(archivo, sheet_name='pvh')


# --------------------------------------------------------------------------------------------------
# * Función: get_allSales
# * Descripción: Obtiene todos las Ventas/Facturas y notas de credito de Odoo
#
# ! Parámetros:
#   - No recibe ningún parámetro
#
# ? Condiciones para saber que productos obtener
#   1. El "status" debe ser:
#       - Posted
#   2. El "move_type" debe ser:
#       - out_invoice
#       - out_refund
#   3. El "branch_id" no debe contener:
#       - STUDIO
#       - TORRE
#   4. El "name" de la venta debe contener
#       - INV/
#       - BONIF/
#       - MUEST/
#
# ? Return:
#   - Caso success:
#       Retorna un JSON con el status success y una lista (array) de ventas. cada producto contiene los siguientes campos:
#       {  id, nombre, fechaCreacion, cliente, vendedor, direccionEnvio, unidad, totalVenta, tipoFactura, lineaProducto {[idProducto, nombreProducto, cantidad, precioUnitario, precioSubtotal, marca, categoria], ...}, pais, estado, ciudad  }
#   - Caso error: 
#       En caso de haber ocurrido algun error retorna un JSON con status error y el mensaje del error
# --------------------------------------------------------------------------------------------------
def get_allSales():
    #!Determinamos que haya algna conexión con Odoo
    if not conn.models:
        return ({
            'status'  : 'error',
            'message' : 'Error en la conexión con Odoo, no hay conexión Activa'
        })
    
    #función try para obtener las facturas
    try: 
        #Busca en odoo las ventas que complan con las siguientes condiciones dadas
        order_sale = conn.models.execute_kw(
            conn.db, conn.uid, conn.password, 
            'account.move', 'search_read', 
            [[['state', '=', 'posted'], '|', ['move_type', '=', 'out_invoice'], ['move_type', '=', 'out_refund'], ['branch_id', 'not ilike', 'STUDIO'], ['branch_id', 'not ilike', 'TORRE'], '|', '|', ['name', 'ilike', 'INV/'], ['name', 'ilike', 'MUEST/'], ['name', 'ilike', 'BONIF/']]],
            { 'fields' : ['name', 'invoice_date', 'partner_id', 'invoice_user_id', 'partner_shipping_id', 'branch_id', 'amount_total_signed', 'move_type']}
        )
        
        for order in order_sale:
            # *Traemos los producto ordenados
            productos = conn.models.execute_kw(
                conn.db, conn.uid, conn.password, 
                'account.move.line', 'search_read', 
                [[['move_id', '=', order['id']], ['display_type', '=', 'product']]],
                { 'fields' :['name', 'product_id', 'quantity', 'price_unit', 'price_subtotal', 'x_studio_marca', 'x_studio_related_field_e1jP7']}
            )
            order['productsLines']=productos
            
            # *Traemos la dirección de a donde es el envio
            direccion = conn.models.execute_kw(
                conn.db, conn.uid, conn.password, 
                'res.partner', 'search_read', 
                [[['id', '=', order['partner_shipping_id'][0]]]],
                { 'fields' : ['city', 'state_id', 'country_id',]}
            )
            if direccion != []:
                order['country_id']= direccion[0]['country_id'][1] if direccion[0]['country_id'] != False else ""
                order['state_id']=direccion[0]['state_id'][1] if direccion[0]['state_id'] != False else ""
                order['city']=direccion[0]['city'] if direccion[0]['city'] != False else ""
            else:
                order['country_id']=""
                order['state_id']=""
                order['city']=""
                
            '''#Lista de Ids que se buscaran
        ordersID=[]
        shippingID=[]
        
        #Obtiene los IDS de la orden y de la dirección para guardarlos en un a lista
        for order in order_sale:
            ordersID.append(order['id'])
            if order['partner_shipping_id']:
                shippingID.append(order['partner_shipping_id'][0])
        
        #Hace una unica busqueda donde encuentra todas las lineas de productos que coincidan con el id de la lista de facturas
        products_data={}
        all_product_line = conn.models.execute_kw(
            conn.db, conn.uid, conn.password, 
            'account.move.line', 'search_read', 
            [[['move_id', 'in', ordersID], ['display_type', '=', 'product']]],
            { 'fields' :['name', 'product_id', 'quantity', 'price_unit', 'price_subtotal', 'x_studio_marca', 'x_studio_related_field_e1jP7', 'move_id']}
        )
        #Las guarda todas en un objetos junto con el id de la factura como id principal para encontrarla
        for line in all_product_line:
            products_data.setdefault(line['move_id'][0], []).append(line)
        
        shipping_data={}
        all_shippings=conn.models.execute_kw(
            conn.db, conn.uid, conn.password, 
            'res.partner', 'search_read', 
            [[['id', 'in', shippingID]]],
            { 'fields' : ['city', 'state_id', 'country_id',]}
        )
        for dir in all_shippings:
            shipping_data[dir['id']]=dir
        
        for order in order_sale:
            order['productsLines'] = products_data.get(order['id'], [])
            
            shipping_id = order['partner_shipping_id'][0] if order['partner_shipping_id'] else None
            direccion = shipping_data.get(shipping_id, {})
            
            order['country_id'] = direccion.get('country_id', [False, ""])[1] if direccion.get('country_id') else ""
            order['state_id'] = direccion.get('state_id', [False, ""])[1] if direccion.get('state_id') else ""
            order['city'] = direccion.get('city') if direccion.get('city') else ""'''
        
        return ({
            'status'  : 'success',
            'ventas' : order_sale
        })
    
    except xmlrpc.client.Fault as e:
        return ({
            'status'       : 'error',
            'message'      : f'Error al ejecutar la consulta a Odoo: {str(e)}',
            'fault_code'   : e.faultCode,
            'fault_string' : e.faultString,
        })









































    
def get_newSales():
    lastDay = (datetime.today() - timedelta(days=1)).strftime('%Y-%m-%d')
    
    order_sale = conn.models.execute_kw(
        conn.db, conn.uid, conn.password, 
        'account.move', 'search_read', 
        [[['create_date', '>=', lastDay], ['state', '=', 'posted'], '|', ['move_type', '=', 'out_invoice'], ['move_type', '=', 'out_refund'], ['branch_id', 'not ilike', 'STUDIO'], ['branch_id', 'not ilike', 'TORRE'], '|', '|', ['name', 'ilike', 'INV/'], ['name', 'ilike', 'MUEST/'], ['name', 'ilike', 'BONIF/']]],
        { 'fields' : ['name', 'invoice_date', 'partner_id', 'invoice_user_id', 'partner_shipping_id', 'branch_id', 'amount_total_signed', 'move_type']}
    )
    
    for order in order_sale:
        # *Traemos los producto ordenados
        productos = conn.models.execute_kw(
            conn.db, conn.uid, conn.password, 
            'account.move.line', 'search_read', 
            [[['move_id', '=', order['id']], ['display_type', '=', 'product']]],
            { 'fields' :['name', 'product_id', 'quantity', 'price_unit', 'price_subtotal', 'x_studio_marca', 'x_studio_related_field_e1jP7']}
        )
        order['productsLines']=productos
        
        # *Traemos la dirección de a donde es el envio
        direccion = conn.models.execute_kw(
            conn.db, conn.uid, conn.password, 
            'res.partner', 'search_read', 
            [[['id', '=', order['partner_shipping_id'][0]]]],
            { 'fields' : ['city', 'state_id', 'country_id']}
        )
        if direccion != []:
            order['country_id']= direccion[0]['country_id'][1] if direccion[0]['country_id'] != False else ""
            order['state_id']=direccion[0]['state_id'][1] if direccion[0]['state_id'] != False else ""
            order['city']=direccion[0]['city'] if direccion[0]['city'] != False else ""
        else:
            order['country_id']=""
            order['state_id']=""
            order['city']=""
    
    return ({
        'status'  : 'success',
        'ventas' : order_sale
    })
    
def pullVentasExcel():
    df = pd.read_excel(archivo, sheet_name='Ventas')
    Ventas=[]
    
    for index, venta in df.iterrows():
        print(index)
        direccion = conn.models.execute_kw(
            conn.db, conn.uid, conn.password, 
            'res.partner', 'search_read', 
            [[['id', '=', venta["idcliente"]], '|', ['active', '=', True], ['active', '=', False]]],
            { 'fields' : ['city', 'state_id', 'country_id']}
        )
        
        if direccion != []:
            Ventas.append(
                {
                'idVenta': venta["idVenta"],
                'fecha': venta["Fecha"],
                'paisVenta': direccion[0]['country_id'][1] if direccion[0]['country_id'] != False else "",
                'estadoVenta': direccion[0]['state_id'][1] if direccion[0]['state_id'] != False else "",
                'ciudadVenta': direccion[0]['city'] if direccion[0]['city'] != False else "",
                'unidad': venta["unidad"],
                'vendedor': venta["vendedor"],
                'total': 0,
                'idCliente': venta["idcliente"]
            }
            )
            
        if direccion == []:
            Ventas.append({
                'idVenta': venta["idVenta"],
                'fecha': venta["Fecha"],
                'paisVenta': False,
                'estadoVenta': False,
                'ciudadVenta': False,
                'unidad': venta["unidad"],
                'vendedor': venta["vendedor"],
                'total': 0,
                'idCliente': venta["idcliente"]
            })
            
    return ({
        'status'  : 'success',
        'ventas' : Ventas
    })
    
def pullLineaVentaExcel(idVenta, fecha):
    try:
        productosList=dfVenta[dfVenta['idVenta']==idVenta]
        
        
        productsPSQL = Productos.objects.all().values_list('sku', flat=True)
        
        total=0
        
        for index, venta in productosList.iterrows():
            if venta["idVenta"] == idVenta:
                
                total=total+(venta['Cantidad facturada']*venta['Precio unitario'])
                productsOdoo = conn.models.execute_kw(
                    conn.db, conn.uid, conn.password, 
                    'product.product', 'search_read',
                    [[['default_code', '=', venta['SKU']], '|', ['active', '=', True], ['active', '=', False]]],
                    { 'fields' : ['name', 'categ_id']}
                )
                
                if venta['SKU'] in productsPSQL and productsOdoo != []:
                    try:
                        VentasPVA.objects.create(
                            fecha           = fecha,
                            cantidad        = venta['Cantidad facturada'],
                            idProducto_id   = productsOdoo[0]['id']
                        )
                    except:
                        try:
                            VentasPVA.objects.create(
                                fecha           = fecha,
                                cantidad        = venta['Cantidad facturada'],
                                idInsumo_id     = productsOdoo[0]['id']
                            )
                        except:
                            pass
                
                VentasPVH.objects.create(
                        cantidad        = venta['Cantidad facturada'],
                        precioUnitario  = venta['Precio unitario'],
                        subtotal        = venta['Total'],
                        marca           = venta['Marca'] if venta['Marca'] else "",
                        categoria       = productsOdoo[0]['categ_id'][1] if productsOdoo != [] else "PRODUCTO DESCONTINUADO/"+venta['categoria'],
                        idVenta_id      = idVenta,
                        nombre          = productsOdoo[0]['name'] if productsOdoo != [] else venta['nombreProducto'],
                        sku             = venta['SKU']
                )
                
        return({
            'status'  : 'success',
            'total' : total
        })   
        
    except Exception as e:
        return({
            'status'  : 'error',
            'message' : f'Ha ocurrido un error al tratar de insertar los datos en ventasPV excel: {e}'
        })