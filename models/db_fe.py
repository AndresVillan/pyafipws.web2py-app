# -*- coding: utf-8 -*-

migrate = True

# Constantes (para la aplicación)

WEBSERVICES = ['wsfe','wsbfe','wsfex','wsfev1', 'wsmtx']
INCOTERMS = ['EXW','FCA','FAS','FOB','CFR','CIF','CPT','CIP','DAF','DES','DEQ','DDU','DDP']
CONCEPTOS = {'1': 'Productos', '2': 'Servicios', '3': 'Otros/ambos'}
IDIOMAS = {'1':'Español', '2': 'Inglés', '3': 'Portugués'}
SINO = {'S': 'Si', 'N': 'No'}
PROVINCIAS = {0: u"C.A.B.A.",1: u"Buenos Aires", 2: u"Catamarca", 3: u"Córdoba",4: u"Corrientes", 5: u"Entre Ríos", 6:
u"Jujuy", 7: u"Mendoza", 8: u"La Rioja", 9: u"Salta", 10: u"San Juan", 11:
u"San Luis", 12: u"Santa Fe", 13: u"Santiago del Estero", 14:
u"Tucuman", 16: u"Chaco", 17: u"Chubut", 18: u"Formosa", 19: u"Misiones", 20:
u"Neuquen", 21: u"La Pampa", 22: u"Río Negro", 23: u"Santa Cruz", 24: u"Tierra del Fuego"}
FORMASPAGO = ['Contado/Efectivo', 'Cheque', 'Cuenta corriente', 'Transferencia', 'Sin especificar']
CONDICIONESIVA = {'IVA Responsable Inscripto': 1, 'IVA Responsable no Inscripto': 2, 'IVA no Responsable': 3,'IVA Sujeto Exento': 4,'Consumidor Final': 5, 'Responsable Monotributo': 6, 'Sujeto no Categorizado': 7, 'Importador del Exterior': 8, 'Cliente del Exterior': 9, 'IVA Liberado - Ley Nº 19.640': 10, 'IVA Responsable Inscripto - Agente de Percepción': 11}

# función para cálculo de detalle en cbte
def detalle_calcular_imp_iva(r):
    """ calcula el total del iva """
    imp_neto = r["precio"] * r["qty"]
    valor_iva = db.iva[r["iva_id"]].aliquota
    imp_iva = imp_neto * valor_iva
    return imp_iva

def detalle_calcular_imp_total(r):
    """ calcula el total del ítem """
    imp_neto = r["precio"] * r["qty"]
    valor_iva = db.iva[r["iva_id"]].aliquota
    imp_iva = imp_neto * valor_iva
    imp_total = imp_neto + imp_iva - r["bonif"]
    return imp_total


# Tablas dinámicas (pueden cambiar por AFIP/Usuario):


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
    
# Idiomas (Español, etc.)
db.define_table('idioma',
    Field('cod', type='id'),
    Field('desc'),
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
    Field('id_ws', 'integer', unique = True, writable=False, requires=IS_EMPTY_OR(IS_INT_IN_RANGE(0, 1e7))),
    Field('webservice', type='string', length=6, default='wsfe', writable = False, 
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
    Field('permiso_existente', type='string', length=1, default="N",
            requires=IS_IN_SET(SINO),
            comment="Permiso de Embarque (exportación)"),
    Field('dst_cmp', type=db.pais_dst, default=200,
            comment="País de destino (exportación)"),
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
    Field('imp_total', type='double', writable=False),
    Field('imp_tot_conc', type='double', writable=False),
    Field('imp_neto', type='double', writable=False),
    Field('impto_liq', type='double', writable=False),
    Field('impto_liq_rni', type='double', writable=False),
    Field('imp_op_ex', type='double', writable=False),
    Field('impto_perc', type='double', writable=False),
    Field('imp_iibb', type='double', writable=False),
    Field('impto_perc_mun', type='double', writable=False),
    Field('imp_internos', type='double', writable=False),
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
    Field('zona', type='string', length=5, default="0",
            comment="(no usado)", writable=False),
    Field('fecha_venc_pago', type='date', length=8,
           comment="(servicios)"),
    Field('fecha_serv_desde', type='date', length=8,
            comment="(servicios)"),
    Field('fecha_serv_hasta', type='date', 
            comment="(servicios)"),
    Field('cae', type='string', writable=False),
    Field('fecha_vto', type='date', length=8, writable=False),
    Field('resultado', type='string', length=1, writable=False),
    Field('reproceso', type='string', length=1, writable=False),
    Field('motivo', type='text', length=40, writable=False),
    Field('err_code', type='string', length=6, writable=False),
    Field('err_msg', type='string', length=1000, writable=False),
    Field('formato_id', type='integer', writable=False),
    Field('usuario', 'reference auth_user', default=auth.user_id, requires = IS_NOT_EMPTY()),
    migrate=migrate)

# detalle de los artículos por cada comprobante
db.define_table('detalle',
    Field('id', type='id'),
    Field('comprobante_id', type='reference comprobante', 
            readable=False, writable=False),
    Field('codigo', type='string', length=30,
            requires=IS_NOT_EMPTY()),
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
            comment="Importe de IVA liquidado",
            readable=False, writable=False, compute=detalle_calcular_imp_iva),
    migrate=migrate)

db.detalle.umed.represent=lambda id: db.umed[id].desc


# Permisos de exportación (si es requerido):
db.define_table('permiso',
    Field('id', type='id'),
    Field('comprobante_id', type='reference comprobante'),
    Field('tipo_reg', type='integer'),
    Field('id_permiso', type='string', length=16),
    Field('dst_merc', type=db.pais_dst),
    migrate=migrate)

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
db.define_table('variables', Field('punto_de_venta', 'reference punto_de_venta'), Field('cuit', 'integer'), Field('domicilio'), Field('telefono'), Field('localidad', 'reference localidad'), Field('provincia', 'reference provincia'), Field('certificate'), Field('private_key'), Field('produccion', 'boolean', default = False), Field('moneda', 'reference moneda'), Field('web_service', requires = IS_IN_SET(WEBSERVICES), default='wsfe'), Field('tipo_cbte', 'reference tipo_cbte'), Field('venc_pago', 'integer', default=30), Field('forma_pago', requires = IS_IN_SET(FORMASPAGO), default = 'Sin especificar'), migrate = migrate)

# Tablas accesorias
db.define_table('sugerir', Field('sugerir_producto', 'reference producto'), migrate = migrate)
db.sugerir.sugerir_producto.widget=SQLFORM.widgets.autocomplete(request, db.producto.ds, id_field=db.producto.id, limitby=(0,10), min_length=2)


# Tablas de depuración

# Bitácora de mensajes XML enviados y recibidos
db.define_table('xml',
    Field('id', type='id'),
    Field('comprobante_id', type='reference comprobante'),
    Field('response', type='text'),
    Field('request', type='text'),
    Field('ts', type='datetime', default=request.now),
    migrate=migrate)
