import xmlrpc.client
from conexiones.conectionOdoo import OdooAPI
import pandas as pd
from datetime import datetime, timedelta

#?Intancia de conexión a Odoo
conn=OdooAPI()

#?Obtiene un archivo mendiante la url y lo abre en la pestaña necesaria para su posterior lectura
archivo = 'C:/Users/DSWB-PC02/Downloads/ContpaqBD.xlsx'
dfVenta = pd.read_excel(archivo, sheet_name='pvh')

# --------------------------------------------------------------------------------------------------
# * Función: get_allClients
# * Descripción: Obtiene todos los clientes (que hayan hecho alguna compra) de Odoo
#
# ! Parámetros:
#   - No recibe ningún parámetro
#
# ? Condiciones para saber que clientes obtener
#   1. invoice_ids no debe ser False o estar vacio:
#   2. active debe ser True o False para que obtenga todos, incluso los archivados:
#
# ? Return:
#   - Caso success:
#       Retorna un JSON con el status success y una lista (array) de clientes. cada producto contiene los siguientes campos:
#       { id, name, city, state_id, country_id, sale_order_count }
#   - Caso error: 
#       En caso de haber ocurrido algun error retorna un JSON con status error y el mensaje del error
# --------------------------------------------------------------------------------------------------
def get_allClients():
    #!Determinamos que haya algna conexión con Odoo
    if not conn.models:
        return ({
            'status'  : 'error',
            'message' : 'Error en la conexión con Odoo, no hay conexión Activa'
        })
    
    #Función try para obteners a todos lo clientes
    try:
        #Obtener a todos los clientes que cumplan con las condiciones
        res_partner = conn.models.execute_kw(
            conn.db, conn.uid, conn.password, 
            'res.partner', 'search_read', 
            [[['invoice_ids', '!=', False], '|', ['active', '=', True], ['active', '=', False]]],
            { 'fields' : ['name', 'city', 'state_id', 'country_id', 'sale_order_count']}
        )
        
        #Retorna todos lo clientes encontrados
        return ({
            'status'  : 'success',
            'clientes' : res_partner
        })
        
    except xmlrpc.client.Fault as e:
        return ({
            'status'       : 'error',
            'message'      : f'Error al ejecutar la consulta a Odoo: {str(e)}',
            'fault_code'   : e.faultCode,
            'fault_string' : e.faultString,
        })
    
    
    
    
#-------------------------------------------------------------------------------
def get_newClients():
    lastDay = (datetime.today() - timedelta(days=1)).strftime('%Y-%m-%d')
    
    res_partner = conn.models.execute_kw(
        conn.db, conn.uid, conn.password, 
        'res.partner', 'search_read', 
        [[['create_date', '>=', lastDay], '|', ['active', '=', True], ['active', '=', False]]],
        { 'fields' : ['name', 'city', 'state_id', 'country_id', 'sale_order_count']}
    )
    
    return ({
        'status'  : 'success',
        'clientes' : res_partner
    })

def update_Clients():
    lastDay = (datetime.today() - timedelta(days=1)).strftime('%Y-%m-%d')
    
    res_partner = conn.models.execute_kw(
        conn.db, conn.uid, conn.password, 
        'res.partner', 'search_read', 
        [[['write_date', '>=', lastDay], ['invoice_ids', '!=', False], '|', ['active', '=', True], ['active', '=', False]]],
        { 'fields' : ['name', 'city', 'state_id', 'country_id', 'sale_order_count']}
    )
    
    return ({
        'status'  : 'success',
        'clientes' : res_partner
    })
    
def pullClientsExcel(idsclientes):
    df = pd.read_excel(archivo, sheet_name='Clientes')
    clientes=[]
    
    for index, cliente in df.iterrows():
        
        if cliente["idCliente"] not in idsclientes:
            res_partner = conn.models.execute_kw(
                conn.db, conn.uid, conn.password, 
                'res.partner', 'search_read', 
                [[['id', '=', cliente["idCliente"]], '|', ['active', '=', True], ['active', '=', False]]],
                { 'fields' : ['name', 'city', 'state_id', 'country_id', 'sale_order_count']}
            )
            if res_partner != []:
                clientes.append(res_partner[0])
            if res_partner == []:
                clientes.append({
                    'id': cliente["idCliente"],
                    'name': cliente["Cliente"],
                    'city': False,
                    'state_id': False,
                    'country_id': False,
                    'sale_order_count': 0,
                })
    
    return ({
        'status'  : 'success',
        'clientes' : clientes
    })