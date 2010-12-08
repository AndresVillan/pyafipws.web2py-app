# coding: utf8

migrate = True

# Constantes (para la aplicación)

WEBSERVICES = ['wsfe','wsbfe','wsfex','wsfev1', 'wsmtx']
INCOTERMS = ['EXW','FCA','FAS','FOB','CFR','CIF','CPT','CIP','DAF','DES','DEQ','DDU','DDP']
CONCEPTOS = {'1': 'Productos', '2': 'Servicios', '3': 'Otros/ambos'}
IDIOMAS = {'1':'Español', '2': 'Inglés', '3': 'Portugués'}
SINO = {'S': 'Si', 'N': 'No'}

# Tablas dinámicas (pueden cambiar por AFIP/Usuario):

# Tipo de documento (FCA, FCB, FCC, FCE, NCA, RCA, etc.)
db.define_table('tipo_cbte',
    Field('cod', type='id'),
    Field('desc'),
    format="%(desc)s",
    migrate=migrate,
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

# Tablas principales

# Datos generales del comprobante:
db.define_table('comprobante',
    Field('id', type='id'),
    Field('webservice', type='string', length=6, default='wsfe',
            requires = IS_IN_SET(WEBSERVICES)),
    Field('fecha_cbte', type='date', default=request.now.date(),
            requires=IS_NOT_EMPTY(),
            comment="Fecha de emisión"),
    Field('tipo_cbte', type=db.tipo_cbte,),
    Field('punto_vta', type='integer', 
            comment="Prefijo Habilitado", default=1,
            requires=IS_NOT_EMPTY()),
    Field('cbte_nro', type='integer',
            comment="Número", default=1,
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
    Field('email', type='string', length=100),    
    Field('id_impositivo', type='string', length=50,
            comment="CNJP, RUT, RUC (exportación"),
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
    Field('obs', type='string', length=1000),
    Field('forma_pago', type='string', length=50),
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
    Field('resultado', type='date', length=1, writable=False),
    Field('reproceso', type='date', length=1, writable=False),
    Field('motivo', type='string', length=40, writable=False),
    Field('err_code', type='string', length=6, writable=False),
    Field('err_msg', type='string', length=1000, writable=False),
    Field('formato_id', type='integer', writable=False),
    migrate=migrate)

# detalle de los artículos por cada comprobante
db.define_table('detalle',
    Field('id', type='id'),
    Field('comprobante_id', type='reference comprobante', 
            readable=False, writable=False),
    Field('codigo', type='string', length=30),
    Field('qty', type='double', label="Cant.", default=1),
    Field('umed', type=db.umed, default=7),
    Field('precio', type='double'),
    Field('imp_total', type='double'),
    Field('iva_id', type=db.iva, default=5),
    Field('ds', type='string', length=4000, label="Descripción"),
    Field('ncm', type='string', length=15),
    Field('sec', type='string', length=15),
    Field('bonif', type='double'),
    migrate=migrate)

# Comprobantes asociados (para NC yND):
db.define_table('cmp_asoc',
    Field('id', type='id'),
    Field('comprobante_id', type='reference comprobante'),
    Field('tipo_reg', type='integer'),
    Field('cbte_tipo', type='integer'),
    Field('cbte_punto_vta', type='integer'),
    Field('cbte_nro', type='integer'),
    migrate=migrate)

# Permisos de exportación (si es requerido):
db.define_table('permiso',
    Field('id', type='id'),
    Field('comprobante_id', type='reference comprobante'),
    Field('tipo_reg', type='integer'),
    Field('id_permiso', type='string', length=16),
    Field('dst_merc', type=db.pais_dst),
    migrate=migrate)

# Tablas de depuración

# Bitácora de mensajes XML enviados y recibidos
db.define_table('xml',
    Field('id', type='id'),
    Field('comprobante_id', type='reference comprobante'),
    Field('response', type='text'),
    Field('request', type='text'),
    Field('ts', type='datetime', default=request.now),
    migrate=migrate)
