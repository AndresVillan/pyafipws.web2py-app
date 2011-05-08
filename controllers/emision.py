# -*- coding: utf-8 -*-
import datetime

def comprobante_tabla_clientes():
    """ Muestra una tabla para establecer un cliente """
    los_clientes = db(db.cliente).select()
    if len(los_clientes) < 1: raise Exception("La tabla de clientes está vacía")
    return dict(clientes = los_clientes)

def comprobante_seleccionar_cliente():
    el_cliente = int(request.args[1])
    session.cliente_seleccionado = el_cliente
    response.flash = "Nuevo cliente seleccionado"
    redirect(URL(r=request, c='emision', f='iniciar'))

def iniciar():
    "Crear/modificar datos generales del comprobante"
    # campos a mostrar:
    campos_generales = ['webservice',
    'fecha_cbte','tipo_cbte','punto_vta','cbte_nro', 'concepto',
    'permiso_existente', 'dst_cmp',
    'nombre_cliente', 'tipo_doc', 'nro_doc', 'domicilio_cliente',
    'telefono_cliente',
    'localidad_cliente', 'provincia_cliente', 'email', 'id_impositivo',
    'moneda_id', 'moneda_ctz', 'obs_comerciales', 'obs', 'forma_pago',
    'incoterms', 'incoterms_ds', 'idioma_cbte',
    'fecha_venc_pago', 'fecha_serv_desde', 'fecha_serv_hasta', ]

    try:
        getattr(session, 'comporbante_id')
    except AttributeError:
        session.comprobante_id = None

    # creo un formulario para el comprobante (TODO: modificar)
    form = SQLFORM(db.comprobante, session.comprobante_id,
                   fields=campos_generales)

    # si el cbte es nuevo pre cargar el formulario
    if not session.comprobante_id:    
        variables = db(db.variables).select().first()
        if not variables:
            raise Exception("No se cargaron las opciones para formularios (variables).")
        else:
            # Recupero opciones de session o del registro de variables
            try:
                if session.punto_vta:
                    form.vars.webservice = session.webservice
                    form.vars.tipo_cbte = session.tipo_cbte
                    form.vars.punto_vta = session.punto_vta
                    form.vars.moneda_id = session.moneda_id
                    form.vars.forma_pago = session.forma_pago
                else: raise KeyError()

            except KeyError:
                form.vars.webservice = variables.web_service
                form.vars.tipo_cbte = variables.tipo_cbte
                form.vars.punto_vta = variables.punto_de_venta.numero
                form.vars.moneda_id = variables.moneda
                form.vars.forma_pago = variables.forma_pago

            form.vars.fecha_venc_pago = str(datetime.datetime.now() + datetime.timedelta(variables.venc_pago))[0:10]            

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
        form.vars.localidad_cliente = cliente.localidad_cliente.desc
        form.vars.provincia_cliente = cliente.provincia_cliente.desc
        form.vars.email = cliente.email

    # valido el formulario (si han enviado datos)
    if form.accepts(request.vars, session, dbio=False):
        session.webservice = form.vars.webservice
        session.tipo_cbte = form.vars.tipo_cbte
        session.moneda_id = form.vars.moneda_id
        session.punto_vta = form.vars.punto_vta
        session.forma_pago = form.vars.forma_pago
        
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
    try:
        # Trato de obtener un producto especificado
        # para pre-completar campos de detalle
        el_producto = int(request.vars["producto"])

    except KeyError:
        # no se envió un producto en la solicitud
        el_producto = None
    
    return dict(form=form, comprobante=comprobante, producto = el_producto, vprevia = None)


def calcular_item_detalle(form):
    """ calcula el total del ítem """
    imp_neto = form.vars.precio * form.vars.qty
    valor_iva = db.iva[form.vars.iva_id].aliquota
    form.vars.imp_iva = imp_neto * valor_iva
    form.vars.imp_total = imp_neto + form.vars.imp_iva - form.vars.bonif


def detalle():
    qty = 1
    bonif = 0.0
    form = SQLFORM(db.detalle, _id="formulario_ingreso_detalle", keepvalues = True, _class="excluir", _style="display: none;")
    iva_texto = ""
    umed_texto = ""
    iva_valor = ""
    try:
        producto = db(db.producto.id == int(request.vars["producto"])).select().first()
        
        form.vars.codigo = producto.codigo
        form.vars.ds = producto.ds
        form.vars.iva_id = producto.iva_id
        form.vars.precio = producto.precio
        form.vars.umed = producto.umed
        form.vars.ncm = producto.ncm
        form.vars.sec = producto.sec
        form.vars.qty = qty
        form.vars.bonif = bonif
        
        iva = db.iva[producto.iva_id]
        iva_texto = iva.desc
        umed_texto = db.umed[producto.umed].desc
        iva_valor = iva.aliquota
        
        form.vars.imp_iva = producto.precio * iva_valor * qty
        form.vars.imp_total = (producto.precio * qty) + (producto.precio * iva_valor * qty)
        
    except KeyError:
        # no se especifica producto pre-cargado
        # en el formulario
        pass

   
    db.detalle.comprobante_id.default = session.comprobante_id
    if form.accepts(request.vars, session, keepvalues = True, onvalidation = calcular_item_detalle):
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
                detalles=detalles, iva_texto = iva_texto, umed_texto = umed_texto, iva_valor = iva_valor)


def editar_detalle():
    form = SQLFORM(db.detalle, request.args[0],deletable=True)
    #db(db.detalle.id==request.args[0]).delete()
    if form.accepts(request.vars, session):
        session.flash = 'formulario aceptado'
        redirect(URL("detallar.html"))
    elif form.errors:
        response.flash = 'formulario con errores'
    return dict(form=form)


def link_cargar_producto(field, type, ref):
    """ función para carga de campos en detalle (no utilizada)"""
    return URL(r=request, f='detallar', vars={'producto': int(field)})


def cargar_producto():
    los_productos = db(db.producto.id > 0).select()
    if len(los_productos) < 1: raise Exception("La tabla productos está vacía.")
    return dict(productos=los_productos)


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
