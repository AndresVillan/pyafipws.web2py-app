# coding: utf8

def iniciar():
    "Crear/modificar datos generales del comprobante"
    # campos a mostrar:
    campos_generales = [
    'fecha_cbte','tipo_cbte','punto_vta','cbte_nro', 'concepto','permiso_existente', 'dst_cmp',
    'nombre_cliente', 'tipo_doc', 'nro_doc', 'domicilio_cliente', 'telefono_cliente',
    'localidad_cliente', 'provincia_cliente', 'email', 'id_impositivo',
    'moneda_id', 'moneda_ctz', 'obs_comerciales', 'obs', 'forma_pago', 
    'incoterms', 'incoterms_ds', 'idioma_cbte',
    'fecha_venc_pago', 'fecha_serv_desde', 'fecha_serv_hasta', ]
    
    # creo un formulario para el comprobante (TODO: modificar)
    form = SQLFORM(db.comprobante, fields=campos_generales)
    
    # valido el formulario (si han enviado datos)
    if form.accepts(request.vars, session, dbio=False):
        # insertar el comprobante (TODO: modificarlo)
        id = db.comprobante.insert(**form.vars)
        # guardo el ID del registro creado en la sesión
        session.comprobante_id = id
        # redirijo a la siguiente página
        session.flash = "Comprobante creado..."
        redirect(URL("detallar"))
    elif form.errors:
       response.flash = '¡Hay errores en el formulario!'
    return dict(form=form)

def detallar():
    # creo un formulario para el comprobante (TODO: modificar)
    campos_encabezado = ['fecha_cbte','tipo_cbte','punto_vta','cbte_nro',  ]
    form = SQLFORM(db.comprobante, session.comprobante_id, fields=campos_encabezado, readonly=True)
    
    comprobante = db(db.comprobante.id==session.comprobante_id).select().first()
    return dict(form=form, comprobante=comprobante)
    
def detalle():
    form = SQLFORM(db.detalle)
    db.detalle.comprobante_id.default = session.comprobante_id
    if form.accepts(request.vars, session):
        response.flash ="Detalle agregado!"
    detalles = db(db.detalle.comprobante_id==session.comprobante_id).select()
    return dict(form=form,
                detalles=detalles)

def editar_detalle():
    form = SQLFORM(db.detalle, request.args[0],deletable=True,)
    #db(db.detalle.id==request.args[0]).delete()
    if form.accepts(request.vars, session):
        session.flash = 'formulario aceptado'
        redirect(URL("detallar.html"))
    elif form.errors:
        response.flash = 'formulario con errores'
    return dict(form=form)
    
def finalizar():
    return {}
