# -*- coding: utf-8 -*-

migrate = True

# Constantes (para la aplicación)

WEBSERVICES = ['wsfe','wsbfe','wsfex','wsfev1', 'wsmtxca']
INCOTERMS = ['EXW','FCA','FAS','FOB','CFR','CIF','CPT','CIP','DAF','DES','DEQ','DDU','DDP']
CONCEPTOS = {'1': 'Productos', '2': 'Servicios', '3': 'Otros/ambos'}
IDIOMAS = {'1':'Español', '2': 'Inglés', '3': 'Portugués'}
SINO = {'S': 'Si', 'N': 'No'}
SINOVACIO = {'S': 'Si', 'N': 'No', u'FACTURALIBREVALORNULL': 'Vacío'}
PROVINCIAS = {0: u"C.A.B.A.",1: u"Buenos Aires", 2: u"Catamarca", 3: u"Córdoba",4: u"Corrientes", 5: u"Entre Ríos", 6:
u"Jujuy", 7: u"Mendoza", 8: u"La Rioja", 9: u"Salta", 10: u"San Juan", 11:
u"San Luis", 12: u"Santa Fe", 13: u"Santiago del Estero", 14:
u"Tucuman", 16: u"Chaco", 17: u"Chubut", 18: u"Formosa", 19: u"Misiones", 20:
u"Neuquen", 21: u"La Pampa", 22: u"Río Negro", 23: u"Santa Cruz", 24: u"Tierra del Fuego"}
FORMASPAGO = ['Contado/Efectivo', 'Cheque', 'Cuenta corriente', 'Transferencia', 'Sin especificar']
CONDICIONESIVA = {'IVA Responsable Inscripto': 1, 'IVA Responsable no Inscripto': 2, 'IVA no Responsable': 3,'IVA Sujeto Exento': 4,'Consumidor Final': 5, 'Responsable Monotributo': 6, 'Sujeto no Categorizado': 7, 'Importador del Exterior': 8, 'Cliente del Exterior': 9, 'IVA Liberado - Ley Nº 19.640': 10, 'IVA Responsable Inscripto - Agente de Percepción': 11}
TIPOEXPO = {1: "Exp. definitiva de bienes", 2: "Servicios", 4: "Otros"}


def comprobante_id_represent(field):
    dr = None
    try:
        dr = str(db.comprobante[field].id)
    except (TypeError, KeyError, AttributeError):
        dr = None
    return dr



def detalle_cod_mtx_represent(field):
    dr = None
    try:
        cd = str(db.cod_mtx[field].ds)
    except (TypeError, KeyError, AttributeError):
        cd = None
    return cd


def dst_cuit_represent(field):
    try:
        return db.dst_cuit[field].ds
    except (TypeError, KeyError, AttributeError):
        return None
    
# función para cálculo de detalle en cbte
def detalle_calcular_imp_iva(r):
    """ calcula el total del iva """
    imp_neto = (r["precio"] * r["qty"]) - r["bonif"]
    valor_iva = db.iva[r["iva_id"]].aliquota
    imp_iva = imp_neto * valor_iva
    return imp_iva

def detalle_calcular_imp_total(r):
    """ calcula el total del ítem """
    imp_neto = (r["precio"] * r["qty"]) -r["bonif"]
    valor_iva = db.iva[r["iva_id"]].aliquota
    imp_iva = imp_neto * valor_iva
    imp_total = imp_neto + imp_iva
    
    if (int(r.comprobante_id.tipo_cbte.cod) in [6, 7, 8, 9] and (r.comprobante_id.webservice == "wsmtxca")):
        imp_total = imp_neto
    
    return imp_total

def detalle_calcular_base_iva(r):
    """ calcula el total del ítem """
    base_iva = (r["precio"] * r["qty"]) -r["bonif"]
    return base_iva


# Tablas dinámicas (pueden cambiar por AFIP/Usuario):

# CUIT del País de destino
db.define_table('dst_cuit', Field('ds'), Field('cuit', 'integer'), migrate = migrate, format="%(ds)s")

# Tipo de documento (FCA, FCB, FCC, FCE, NCA, RCA, etc.)
db.define_table('tipo_cbte',
    Field('cod', type='id'),
    Field('desc'),
    Field('discriminar', 'boolean'),
    format="%(desc)s",
    migrate=migrate,
    )

# condición IVA (Tipo de responsable)
db.define_table('condicion_iva', Field('codigo'), Field('desc'), \
    format="%(desc)s", \
    migrate=migrate
)

# Tipos de documentos (CUIT, CUIL, CDI, DNI, CI, etc.)
db.define_table('tipo_doc',
    Field('cod', type='id'),
    Field('desc'),
    format="%(desc)s",
    migrate=migrate,
    )

# Monedas (PES: Peso, DOL: DOLAR, etc.)
db.define_table('moneda',
    Field('cod', type='string'),
    Field('desc'),
    format="%(desc)s",
    migrate=migrate,
    )

# unidades MTX
db.define_table('u_mtx',
    Field('cod', 'integer'),
    Field('ds'),
    format="%(ds)s",
    migrate=migrate,
    )

# codigos MTX
db.define_table('cod_mtx',
    Field('cod', length = 14),
    Field('ds'),
    format="%(ds)s",
    migrate=migrate,
    )

# Idiomas (Español, etc.)
db.define_table('idioma',
    Field('cod', type='id'),
    Field('desc'),
    format="%(desc)s",
    migrate=migrate,
    )

# tributos (clases)
db.define_table('tributo',
    Field('cod', type='id'),
    Field('desc'),
    Field('aliquota', 'double'),        
    format="%(desc)s",
    migrate=migrate,
    )

# Unidades de medida (u, kg, m, etc.) 
db.define_table('umed',
    Field('cod', type='id'),
    Field('desc'),
    format="%(desc)s",
    migrate=migrate,
    )

# Alícuotas de IVA (EX, NG, 0%, 10.5%, 21%, 27%)
db.define_table('iva',
    Field('cod', type='id'),
    Field('desc'),
    Field('aliquota', 'double'),
    format="%(desc)s",
    migrate=migrate,
    )

# Paises (destino de exportación)
db.define_table('pais_dst',
    Field('cod', type='id'),
    Field('desc'),
    Field('cuit', requires = IS_CUIT()),    
    format="%(desc)s",
    migrate=migrate,
    )

# provincia
db.define_table('provincia',
    Field('cod',type='integer', requires =IS_IN_SET(PROVINCIAS.keys())),
    Field('desc'),
    format="%(desc)s (%(id)s)",
    migrate=migrate,
    )

# localidad
db.define_table('localidad',
    Field('cod'),
    Field('provincia', type='reference provincia'),
    Field('desc'),
    format='%(desc)s (%(provincia)s)',
    migrate=migrate
    )

# Tablas principales

# Datos generales del comprobante:
db.define_table('comprobante',
    Field('id_ws', 'integer', writable=False, requires=IS_EMPTY_OR(IS_INT_IN_RANGE(0, 1e7))),
    Field('webservice', type='string', length=6, writable = False, 
            requires = IS_IN_SET(WEBSERVICES)),
    Field('fecha_cbte', type='date', default=request.now.date(),
            requires=IS_NOT_EMPTY(), writable = False,
            comment="Fecha de emisión"),
    Field('tipo_cbte', type=db.tipo_cbte,),
    Field('punto_vta', type='integer', 
            comment="Prefijo Habilitado", default=1,
            requires=IS_NOT_EMPTY(), writable = False),
    Field('cbte_nro', type='integer',
            comment="Número", writable=False,
            requires=IS_NOT_EMPTY()),
    Field('concepto', type='integer', default=1,
            requires=IS_IN_SET(CONCEPTOS),),
    Field('permiso_existente', type='string', default="N",
            requires=IS_IN_SET(SINOVACIO),
            comment="Permiso de Embarque (exportación)"),
    Field('dst_cmp', type=db.pais_dst, default=200,
            comment="País de destino (exportación)"),
    Field('dst_cuit', type=db.dst_cuit, default = 1),            
    Field('nombre_cliente', type='string', length=200),
    Field('tipo_doc', type=db.tipo_doc, default='80'),
    Field('nro_doc', type='string',
            requires=IS_CUIT()),
    Field('domicilio_cliente', type='string', length=300),
    Field('telefono_cliente', type='string', length=50),
    Field('localidad_cliente', type='string', length=50),
    Field('provincia_cliente', type='string', length=50),
    Field('condicion_iva_cliente', length=50),
    Field('email', type='string', length=100),    
    Field('id_impositivo', type='string', length=50,
            comment="CNJP, RUT, RUC (exportación)"),
    Field('imp_total', type='double'),
    Field('imp_tot_conc', type='double'),
    Field('imp_neto', type='double'),
    Field('impto_liq', type='double'),
    Field('impto_liq_rni', type='double'),
    Field('imp_op_ex', type='double'),
    Field('impto_perc', type='double'),
    Field('imp_iibb', type='double'),
    Field('imp_subtotal', type='double'),
    Field('imp_trib', type='double'),
    Field('impto_perc_mun', type='double'),
    Field('imp_internos', type='double'),
    Field('moneda_id', type=db.moneda, length=3, default=14),
    Field('moneda_ctz', type='double', default="1.000"),
    Field('obs_comerciales', type='string', length=1000),
    Field('obs', type='text', length=1000),
    Field('forma_pago', type='string', length=50, requires = IS_IN_SET(FORMASPAGO)),
    Field('incoterms', type='string', length=3,
        requires=IS_EMPTY_OR(IS_IN_SET(INCOTERMS)),
        comment="Términos de comercio exterior"),
    Field('incoterms_ds', type='string', length=20),
    Field('idioma_cbte', type='string', length=1, default="1",
           requires=IS_IN_SET(IDIOMAS)),
    Field('zona', type='string', length=5, default="1",
            comment="(no usado)", writable=False),
    Field('fecha_venc_pago', type='date', length=8,
           comment="(servicios)", default=request.now.date()),
    Field('fecha_serv_desde', type='date', length=8,
            comment="(servicios)", default=request.now.date()),
    Field('fecha_serv_hasta', type='date', 
            comment="(servicios)", default=request.now.date()),
    Field('cae', type='string', writable=False),
    Field('fecha_vto', type='date', length=8, writable=False),
    Field('resultado', type='string', length=1, writable=False),
    Field('reproceso', type='string', length=1, writable=False),
    Field('motivo', type='text', length=40, writable=False),
    Field('err_code', type='string', length=6, writable=False),
    Field('err_msg', type='string', length=1000, writable=False),
    Field('formato_id', type='integer', writable=False),
    Field('tipo_expo', 'integer', requires = IS_IN_SET(TIPOEXPO), default = 1),
    Field('usuario', 'reference auth_user', default=auth.user_id, requires = IS_NOT_EMPTY()),
    migrate=migrate)

db.comprobante.dst_cuit.represent=dst_cuit_represent

# detalle de los artículos por cada comprobante
db.define_table('detalle',
    Field('id', type='id'),
    Field('comprobante_id', type='reference comprobante', \
    writable=False, represent=comprobante_id_represent),
    Field('codigo', type='string', length=30,
            requires=IS_NOT_EMPTY()),
    Field('u_mtx', type=db.u_mtx, requires = IS_EMPTY_OR(IS_IN_DB(db,db.u_mtx))),
    Field('cod_mtx', type=db.cod_mtx, requires = IS_EMPTY_OR(IS_IN_DB(db,db.cod_mtx))),
    Field('ds', type='text', length=4000, label="Descripción",
            requires=IS_NOT_EMPTY()),
    Field('qty', type='double', label="Cant.", default=1,
            requires=IS_FLOAT_IN_RANGE(0.0001, 1000000000)),
    Field('precio', type='double', notnull=True,
            requires=IS_FLOAT_IN_RANGE(0.01, 1000000000)),
    Field('umed', type=db.umed, default=7,
            ),
    Field('imp_total', type='double', label="Subtotal",
            requires=IS_NOT_EMPTY(), compute=detalle_calcular_imp_total),
    Field('iva_id', type=db.iva, default=5, label="IVA",
            represent=lambda id: db.iva[id].desc,
            comment="Alícuota de IVA"),
    Field('ncm', type='string', length=15, 
            comment="Código Nomenclador Común Mercosur (Bono fiscal)"),
    Field('sec', type='string', length=15,
            comment="Código Secretaría de Comercio (Bono fiscal)"),
    Field('bonif', type='double', default=0.00,
            requires=IS_FLOAT_IN_RANGE(0.0, 1000000000)),
    Field('imp_iva', type="double", default=0.00, 
            comment="Importe de IVA liquidado", compute=detalle_calcular_imp_iva),
    Field('base_imp_iva', 'double', compute=detalle_calcular_base_iva),
    Field('base_imp_tributo', 'double'),
    migrate=migrate)

db.detalle.umed.represent=lambda id: db.umed[id].desc

# tributo por comprobante
db.define_table('tributo_item',
    Field('comprobante', type=db.comprobante),
    Field('tributo', type=db.tributo),
    Field('base_imp', 'double'),
    Field('importe', 'double'),
    migrate=migrate,
    )

db.tributo_item.tributo.represent=lambda id: db.tributo[id].desc
db.tributo_item.comprobante.represent=lambda id: db.comprobante[id].cbte_nro

# Permisos de exportación (si es requerido):
db.define_table('permiso',
    Field('id', type='id'),
    Field('comprobante_id', type=db.comprobante),
    Field('tipo_reg', type='integer'),
    Field('id_permiso', type='string', length=16),
    Field('dst_merc', type=db.pais_dst),
    migrate=migrate)

db.permiso.comprobante_id.represent=lambda id: db.comprobante[id].cbte_nro

db.define_table('producto', Field('ds', type='text', length=4000, label="Descripción", \
            requires=IS_NOT_EMPTY()), Field('iva_id', \
    type=db.iva, default=5, label="IVA", represent=lambda id: db.iva[id].desc, \
    comment="Alícuota de IVA"), Field('codigo', type='string', \
    length=30, requires=IS_NOT_EMPTY()), Field('precio', \
    type='double', notnull=True, requires=IS_FLOAT_IN_RANGE(0.01, 1000000000)), \
    Field('umed', type=db.umed, default=7), Field('ncm', type='string', \
    length=15, comment="Código Nomenclador Común Mercosur (Bono fiscal)"), \
    Field('sec', type='string', length=15, \
    comment="Código Secretaría de Comercio (Bono fiscal)"),
    Field('u_mtx', type=db.u_mtx, requires = IS_EMPTY_OR(IS_IN_DB(db, db.u_mtx))), \
    Field('cod_mtx', type=db.cod_mtx, requires = IS_EMPTY_OR(IS_IN_DB(db, db.cod_mtx))), \
    migrate=migrate)

db.define_table('cliente', Field('nombre_cliente', type='string', length=200),
    Field('tipo_doc', type=db.tipo_doc, default='80'),
    Field('nro_doc', type='string',
            requires=IS_CUIT()),
    Field('domicilio_cliente', type='string', length=300),
    Field('telefono_cliente', type='string', length=50),
    Field('localidad_cliente', type='reference localidad', comment='Localidad (id de provincia)', length=50),
    Field('provincia_cliente', type='reference provincia', comment='Provincia (id)'),
    Field('email', type='string', length=100),    
    Field('condicion_iva', 'reference condicion_iva'), \
    Field('id_impositivo', type='string', length=50,
            comment="CNJP, RUT, RUC (exportación)"), migrate=migrate)

# punto de venta
db.define_table('punto_de_venta', Field('numero', 'integer', unique = True), Field('nombre'), Field('domicilio'), Field('localidad', 'reference localidad'), Field('provincia', 'reference provincia'), migrate = migrate, format="%(nombre)s")

# variables generales (único registro)
db.define_table('variables', Field('punto_de_venta', 'reference punto_de_venta'), Field('cuit', 'integer'), Field('domicilio'), Field('telefono'), Field('localidad', 'reference localidad'), Field('provincia', 'reference provincia'), Field('certificate'), Field('private_key'), Field('produccion', 'boolean', default = False), Field('moneda', 'reference moneda'), Field('webservice', requires = IS_IN_SET(WEBSERVICES), default='wsfe'), Field('tipo_cbte', 'reference tipo_cbte'), Field('venc_pago', 'integer', default=30), Field('forma_pago', requires = IS_IN_SET(FORMASPAGO), default = 'Sin especificar'), migrate = migrate)

# comprobantes asociados (tabla intermedia)
db.define_table('comprobante_asociado', Field('comprobante', type=db.comprobante), Field('asociado', type=db.comprobante), migrate = migrate)



def cbte_asociado_asociado_represent(field):
    try:
        return str(db.comprobante[field.id].tipo_cbte.desc) + " " + str(db.comprobante[field.id].cbte_nro)
    except (AttributeError, KeyError, ValueError):
        return "Sin número"

def cbte_asociado_comprobante_represent(field):
    try:
        return str(db.comprobante[field.id].tipo_cbte.desc) + " " + str(db.comprobante[field.id].cbte_nro)
    except (AttributeError, KeyError, ValueError):
        return "Sin número"


db.comprobante_asociado.asociado.represent=cbte_asociado_asociado_represent
db.comprobante_asociado.comprobante.represent=cbte_asociado_comprobante_represent

# detalle tributo asociado
db.define_table('lista_tributo', Field('comprobante', 'reference comprobante'), Field('tributo', 'reference tributo'), Field('importe', 'double'), migrate = migrate)

# variables por usuario
db.define_table('variables_usuario', Field('usuario', 'reference auth_user', unique = True, writable = False), Field('punto_de_venta', 'reference punto_de_venta'), Field('moneda', 'reference moneda'), Field('webservice', requires = IS_IN_SET(WEBSERVICES), default='wsfe'), Field('tipo_cbte', 'reference tipo_cbte'), Field('venc_pago', 'integer', default=30), Field('forma_pago', requires = IS_IN_SET(FORMASPAGO), default = 'Sin especificar'), migrate = migrate)

# Tablas accesorias
db.define_table('sugerir', Field('sugerir_producto', 'reference producto'), migrate = migrate)
db.sugerir.sugerir_producto.widget=SQLFORM.widgets.autocomplete(request, db.producto.ds, id_field=db.producto.id, limitby=(0,10), min_length=3)

# Tablas de depuración

# Bitácora de mensajes XML enviados y recibidos
db.define_table('xml',
    Field('id', type='id'),
    Field('comprobante_id', type='reference comprobante'),
    Field('response', type='text'),
    Field('request', type='text'),
    Field('ts', type='datetime', default=request.now),
    migrate=migrate)
