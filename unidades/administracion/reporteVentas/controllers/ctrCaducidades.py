from conexiones.conectionOdoo import OdooAPI

conn=OdooAPI()

### *Traer todos los clientes que hay en Odoo
def get_allCaducidades():
    caducidades = conn.models.execute_kw(
        conn.db, conn.uid, conn.password, 
        'stock.lot', 'search_read', 
        [[]],
        { 'fields' : ['name', 'product_id', 'product_qty']}
    )
    
    return ({
        'status'  : 'success',
        'caducidades' : caducidades
    })