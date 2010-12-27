# coding: utf8

def comprobante_tabla_clientes():
    """ Muestra una tabla para establecer un cliente """
    los_clientes = db(db.cliente).select()
    tabla_clientes = DIV(SQLTABLE(los_clientes, linkto = URL(r=request, c='emision', f='comprobante_seleccionar_cliente')), _style='overflow: auto;')
    return dict(tabla_clientes = tabla_clientes)

def comprobante_seleccionar_cliente():
    el_cliente = int(request.args[1])
    session.cliente_seleccionado = el_cliente
    response.flash = "Nuevo cliente seleccionado"
    redirect(URL(r=request, c='emision', f='iniciar'))

def iniciar():
    "Crear/modificar datos generales del comprobante"
    # campos a mostrar:
    campos_generales = [
    'fecha_cbte','tipo_cbte','punto_vta','cbte_nro', 'concepto',
    'permiso_existente', 'dst_cmp',
    'nombre_cliente', 'tipo_doc', 'nro_doc', 'domicilio_cliente',
    'telefono_cliente',
    'localidad_cliente', 'provincia_cliente', 'email', 'id_impositivo',
    'moneda_id', 'moneda_ctz', 'obs_comerciales', 'obs', 'forma_pago',
    'incoterms', 'incoterms_ds', 'idioma_cbte',
    'fecha_venc_pago', 'fecha_serv_desde', 'fecha_serv_hasta', ]

    # creo un formulario para el comprobante (TODO: modificar)
    form = SQLFORM(db.comprobante, session.comprobante_id,
                   fields=campos_generales)

    # Si se seleccionó un cliente cargar datos
    try:
        cliente_seleccionado = session.cliente_seleccionado
    except (KeyError, ValueError):
        cliente_seleccionado = None
        
    if cliente_seleccionado != None:
        cliente = db(db.cliente.id == cliente_seleccionado).select().first()
        form.vars.nombre_cliente = cliente.nombre_cliente
        form.vars.tipo_doc = cliente.tipo_doc
        form.vars.nro_doc = cliente.nro_doc
        form.vars.domicilio_cliente = cliente.domicilio_cliente
        form.vars.telefono_cliente = cliente.telefono_cliente
        form.vars.localidad_cliente = cliente.localidad_cliente
        form.vars.provincia_cliente = cliente.provincia_cliente
        form.vars.email = cliente.email

    # valido el formulario (si han enviado datos)
    if form.accepts(request.vars, session, dbio=False):
        if not session.comprobante_id:
            # insertar el comprobante
            id = db.comprobante.insert(**form.vars)
            session.flash = "Comprobante creado..."
        else:
            id = session.comprobante_id
            db(db.comprobante.id==id).update(**form.vars)
            session.flash = "Comprobante actualizado..."
        # guardo el ID del registro creado en la sesión
        session.comprobante_id = id
        # redirijo a la siguiente página
        redirect(URL("detallar"))
    elif form.errors:
       response.flash = '¡Hay errores en el formulario!'
   
    return dict(form=form)


def detallar():
    # creo un formulario para el comprobante (TODO: modificar)
    campos_encabezado = ['fecha_cbte','tipo_cbte','punto_vta','cbte_nro',  ]
    form = SQLFORM(db.comprobante, session.comprobante_id,
                   fields=campos_encabezado, readonly=True)
    comprobante = db(db.comprobante.id==session.comprobante_id).select().first()
    return dict(form=form, comprobante=comprobante)

def detalle():
    form = SQLFORM(db.detalle)
    db.detalle.comprobante_id.default = session.comprobante_id
    if form.accepts(request.vars, session):
        response.flash ="Detalle agregado!"
    detalles = db(db.detalle.comprobante_id==session.comprobante_id).select()
    total = sum([detalle.imp_total for detalle in detalles], 0.00)
    # agregado por marcelo
    comprobante = db(db.comprobante.id==session.comprobante_id).select().first()
    tipo_cbte = db(db.tipo_cbte.id==comprobante.tipo_cbte).select().first()
    for p in range(len(detalles)):
        iva = db(db.iva.id==detalles[p].iva_id).select().first()
        if tipo_cbte.discriminar:
            detalles[p].imp_iva = detalles[p].qty * detalles[p].precio * iva.aliquota
        else:
            detalles[p].imp_iva = detalles[p].qty * detalles[p].precio * (1+iva.aliquota)
    # fin marcelo
    return dict(form=form, total=total,
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
    campos_encabezado = [
        'fecha_cbte','tipo_cbte','punto_vta','cbte_nro', 'concepto',
        'permiso_existente', 'dst_cmp',
        'nombre_cliente', 'tipo_doc', 'nro_doc', 'domicilio_cliente',
        'id_impositivo',
        'moneda_id', 'moneda_ctz', 'obs_comerciales', 'obs', 'forma_pago',
        'fecha_venc_pago', 'fecha_serv_desde', 'fecha_serv_hasta',]
    form = SQLFORM(db.comprobante, session.comprobante_id,
                   fields=campos_encabezado, readonly=True)

    comprobante = db(db.comprobante.id==session.comprobante_id).select().first()

    return dict(form=form, comprobante=comprobante)
