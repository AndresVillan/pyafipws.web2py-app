# -*- coding: utf-8 -*-
import datetime

@auth.requires(auth.has_membership('administrador') or auth.has_membership('emisor'))
def comprobante_tabla_clientes():
    """ Muestra una tabla para establecer un cliente """
    los_clientes = db(db.cliente).select()
    if len(los_clientes) < 1: raise HTTP(500, "La tabla de clientes está vacía")
    return dict(clientes = los_clientes)

@auth.requires(auth.has_membership('administrador') or auth.has_membership('emisor'))
def comprobante_seleccionar_cliente():
    el_cliente = int(request.args[1])
    session.cliente_seleccionado = el_cliente
    response.flash = "Nuevo cliente seleccionado"
    redirect(URL(r=request, c='emision', f='iniciar'))


@auth.requires(auth.has_membership('administrador') or auth.has_membership('emisor'))
def iniciar():
    variables = None
    webservice = None
    punto_de_venta = None
    cliente = None
    variables_usuario = None
    
    fecha = datetime.datetime.now()
    "Crear/modificar datos generales del comprobante"
    # campos a mostrar:
    campos_generales = ['fecha_cbte','tipo_cbte', 'concepto', 'tipo_expo', 'permiso_existente', 'dst_cmp', \
    'dst_cuit', 'moneda_id', 'moneda_ctz','imp_iibb', 'obs_comerciales', \
    'obs', 'forma_pago', 'incoterms', 'incoterms_ds', 'idioma_cbte', \
    'fecha_venc_pago', 'fecha_serv_desde', 'fecha_serv_hasta', ]

    try:
        getattr(session, 'comporbante_id')
    except AttributeError:
        session.comprobante_id = None

    # creo un formulario para el comprobante (TODO: modificar)
    form = SQLFORM(db.comprobante, session.comprobante_id,
                   fields=campos_generales)

    variables = db(db.variables).select().first()
    if not variables:
        raise HTTP(500, "No se cargaron las opciones globales para formularios.")
    variables_usuario = db(db.variables_usuario.usuario == auth.user_id).select().first()
    if not variables_usuario:
        db.variables_usuario.insert(usuario = auth.user_id, \
            punto_de_venta = variables.punto_de_venta, \
            moneda = variables.moneda, \
            webservice = variables.webservice, \
            tipo_cbte = variables.tipo_cbte, \
            venc_pago = variables.venc_pago, \
            forma_pago = variables.forma_pago
        )
        response.flash = "Se generó el registro de variables para formularios del usuario."

    # si el cbte es nuevo pre cargar el formulario
    if not session.comprobante_id:    
        # Recupero opciones del registro global de variables
        form.vars.webservice = variables_usuario.webservice
        form.vars.tipo_cbte = variables_usuario.tipo_cbte
        form.vars.punto_vta = variables_usuario.punto_de_venta.numero
        form.vars.moneda_id = variables_usuario.moneda
        form.vars.forma_pago = variables_usuario.forma_pago
       
        form.vars.fecha_venc_pago = str(fecha + datetime.timedelta(variables_usuario.venc_pago))[0:10]
        form.vars.fecha_vto = str(fecha + datetime.timedelta(variables_usuario.venc_pago))[0:10]
        form.vars.fecha_serv_desde = str(fecha)[0:10]
        form.vars.fecha_serv_hasta = str(fecha)[0:10]
                        
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
        """
        session.webservice = form.vars.webservice
        session.tipo_cbte = form.vars.tipo_cbte
        session.moneda_id = form.vars.moneda_id
        session.punto_vta = form.vars.punto_vta
        session.forma_pago = form.vars.forma_pago
        """
        
        if not session.comprobante_id:
            # insertar el comprobante
            id = db.comprobante.insert(**form.vars)
            session.flash = "Comprobante creado..."
        else:
            id = session.comprobante_id
            
            # no cambiar el webservice si es un cbte
            # enviado
            if db.comprobante[id].resultado:
                form.vars.webservice = db.comprobante[id].webservice
                
            db(db.comprobante.id==id).update(**form.vars)
            session.flash = "Comprobante actualizado..."
        # guardo el ID del registro creado en la sesión
        session.comprobante_id = id
        # redirijo a la siguiente página
        redirect(URL("detallar"))
    elif form.errors:
       response.flash = '¡Hay errores en el formulario!'

    return dict(form=form, cliente = cliente, variables_usuario = variables_usuario)


@auth.requires(auth.has_membership('administrador') or auth.has_membership('emisor'))
def detallar():
    # creo un formulario para el comprobante (TODO: modificar)
    campos_encabezado = ['fecha_cbte','tipo_cbte','punto_vta','cbte_nro', 'webservice' ]
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

    try:
        # Trato de obtener un producto especificado
        # para pre-completar campos de detalle
        el_cbte_asoc = int(request.vars["cbte_asoc"])

    except KeyError:
        # no se envió un producto en la solicitud
        el_cbte_asoc = None

    return dict(form=form, comprobante=comprobante, producto = el_producto, vprevia = None, cbte_asoc = el_cbte_asoc)


def calcular_item_detalle(form):
    """ calcula el total del ítem """
    try:
        imp_neto = (form.vars.precio * form.vars.qty) -form.vars.bonif
        valor_iva = db.iva[form.vars.iva_id].aliquota
        if not valor_iva: valor_iva = 0.00
        form.vars.imp_iva = imp_neto * valor_iva
        form.vars.imp_total = imp_neto + form.vars.imp_iva
        form.vars.base_imp_iva = imp_neto
        form.vars.base_imp_tributo = imp_neto
    except (ValueError, KeyError, AttributeError), e:
        db.xml.insert(request = "Error al calcular el ítem", response = str(e))


@auth.requires(auth.has_membership('administrador') or auth.has_membership('emisor'))
def detalle():
    qty = 1
    bonif = 0.0
    form = SQLFORM(db.detalle, keepvalues = True, _class="excluir", _id="formulario_ingreso_detalle")
    iva_texto = ""
    umed_texto = ""
    iva_valor = 0.0

    if request.vars.codigo:    
        form.vars.codigo = request.vars.codigo
        form.vars.ds = request.vars.ds
        form.vars.iva_id = request.vars.iva_id
        form.vars.precio = request.vars.precio
        form.vars.umed = request.vars.umed
        form.vars.ncm = request.vars.ncm
        form.vars.sec = request.vars.sec
        form.vars.qty = request.vars.qty
        form.vars.bonif = request.vars.bonif
        umed_texto = db.umed[form.vars.umed].desc
        iva_texto = db.iva[form.vars.iva_id].desc
         
    else:
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

    elif form.errors:
        response.flash = "El detalle tiene errores!: " + str(form.errors.keys()) + " " + str(form.errors.values())
        
    detalles = db(db.detalle.comprobante_id==session.comprobante_id).select()

    total = sum([detalle.imp_total for detalle in detalles], 0.00)
    # agregado por marcelo
    comprobante = db(db.comprobante.id==session.comprobante_id).select().first()
    tipo_cbte = db(db.tipo_cbte.id==comprobante.tipo_cbte).select().first()
    for p in range(len(detalles)):
        iva = db(db.iva.id==detalles[p].iva_id).select().first()
        try:
            if tipo_cbte.discriminar:
                detalles[p].imp_iva = detalles[p].qty * detalles[p].precio * iva.aliquota
                
            else:
                detalles[p].imp_iva = detalles[p].qty * detalles[p].precio * (1+iva.aliquota)
        except (ValueError, KeyError, AttributeError, TypeError):
            detalles[p].imp_iva = 0.00
            
    # fin marcelo
    return dict(form=form, total=total,
                detalles=detalles, iva_desc = iva_texto, umed_desc = umed_texto, iva_aliquota = iva_valor)


@auth.requires(auth.has_membership('administrador') or auth.has_membership('emisor'))
def detalle_tributo():
    comprobante = None
    tributo = None
    base_imp = None
    importe = None

    form = SQLFORM(db.tributo_item, keepvalues = True, _class="excluir", _id="formulario_ingreso_detalle_tributo")

    if request.vars.tributo:    
        form.vars.comprobante = request.vars.comprobante
        form.vars.tributo = request.vars.tributo
        form.vars.base_imp = request.vars.base_imp
        form.vars.importe = request.vars.importe
        form.vars.comprobante = session.comprobante_id        
         
    else:
        try:
            form.vars.comprobante = request.vars.comprobante
            form.vars.tributo = request.vars.tributo
            form.vars.base_imp = request.vars.base_imp
            form.vars.importe = request.vars.importe
            form.vars.comprobante = session.comprobante_id
        
        except KeyError:
             # no se especifica tributo
            # en el formulario
            pass
   
    db.tributo_item.comprobante.default = session.comprobante_id
    
    if form.accepts(request.vars, session, keepvalues = True):
        response.flash ="Detalle de tributo agregado!"

    elif form.errors:
        response.flash = "El detalle tiene errores!: " + str(form.errors.keys()) + " " + str(form.errors.values())
        
    los_tributos = db(db.tributo_item.comprobante==session.comprobante_id).select()
    return dict(form=form, tributos=los_tributos)


@auth.requires(auth.has_membership('administrador') or auth.has_membership('emisor'))
def detalle_permiso():
    comprobante = None
    id_permiso = None
    tipo_reg = None
    dst_merc = None

    form = SQLFORM(db.permiso, keepvalues = True, _class="excluir", _id="formulario_ingreso_detalle_permiso")

    if request.vars.id_permiso:    
        form.vars.id_permiso = request.vars.id_permiso
        form.vars.tipo_reg = request.vars.tipo_reg
        form.vars.dst_merc = request.vars.dst_merc
        form.vars.comprobante_id = session.comprobante_id
         
    else:
        try:
            form.vars.id_permiso = request.vars.id_permiso
            form.vars.tipo_reg = request.vars.tipo_reg
            form.vars.dst_merc = request.vars.dst_merc
            form.vars.comprobante_id = session.comprobante_id
        
        except KeyError:
             # no se especifica tributo
            # en el formulario
            pass
   
    db.permiso.comprobante_id.default = session.comprobante_id
    
    if form.accepts(request.vars, session, keepvalues = True):
        response.flash ="Detalle de permiso agregado!"

    elif form.errors:
        response.flash = "El detalle tiene errores!: " + str(form.errors.keys()) + " " + str(form.errors.values())
        
    los_permisos = db(db.permiso.comprobante_id==session.comprobante_id).select()
    return dict(form=form, permisos=los_permisos)


@auth.requires(auth.has_membership('administrador') or auth.has_membership('emisor'))
def detalle_asociado():
    asoc_cbte_nro = None
    asoc_tipo_cbte = None
    asoc_punto_vta = None

    form = SQLFORM.factory(
        Field('asoc_cbte_nro', requires=IS_NOT_EMPTY()),
        Field('asoc_tipo_cbte', requires=IS_NOT_EMPTY()),
        Field('asoc_punto_vta', requires=IS_NOT_EMPTY()), \
        keepvalues = True, _class="excluir", _id="formulario_ingreso_detalle_asociado")
        
    # db.comprobante_asociado.comprobante.default = session.comprobante_id
    
    if form.accepts(request.vars, session):
        cbtasoc = None
        for cbte in db(db.comprobante.cbte_nro == form.vars.asoc_cbte_nro).select():
            if cbte.tipo_cbte.cod == int(form.vars.asoc_tipo_cbte):
                if cbte.punto_vta == db.punto_de_venta[form.vars.asoc_punto_vta].numero:
                    if cbte.webservice == db.comprobante[session.comprobante_id].webservice:
                        cbtasoc = db.comprobante_asociado.insert(comprobante = int(str(session.comprobante_id)), \
                        asociado = int(str(cbte.id)))
                        response.flash ="Cbte asociado agregado!:"
        if not cbtasoc: response.flash = "El cbte asociado no es válido"

    elif form.errors:
        response.flash = "El cbte asociado tiene errores!: " + \
        str(form.errors.keys()) + " " + str(form.errors.values())

    los_asociados = db(db.comprobante_asociado.comprobante==session.comprobante_id).select()
    return dict(form=form, asociados=los_asociados)


@auth.requires(auth.has_membership('administrador') or auth.has_membership('emisor'))
def editar_detalle():
    form = SQLFORM(db.detalle, request.args[0],deletable=True, onvalidation = calcular_item_detalle)
    #db(db.detalle.id==request.args[0]).delete()
    if form.accepts(request.vars, session):
        session.flash = 'formulario aceptado'
        redirect(URL("detallar.html"))
    elif form.errors:
        response.flash = 'formulario con errores'
    return dict(form=form)


@auth.requires(auth.has_membership('administrador') or auth.has_membership('emisor'))
def editar_detalle_tributo():
    form = SQLFORM(db.tributo_item, request.args[0],deletable=True)
    #db(db.detalle.id==request.args[0]).delete()
    if form.accepts(request.vars, session):
        session.flash = 'formulario aceptado'
        redirect(URL("detallar.html"))
    elif form.errors:
        response.flash = 'formulario con errores'
    return dict(form=form)


@auth.requires(auth.has_membership('administrador') or auth.has_membership('emisor'))
def editar_detalle_asociado():
    form = SQLFORM(db.comprobante_asociado, request.args[0],deletable=True)
    #db(db.detalle.id==request.args[0]).delete()
    if form.accepts(request.vars, session):
        session.flash = 'formulario aceptado'
        redirect(URL("detallar.html"))
    elif form.errors:
        response.flash = 'formulario con errores'
    return dict(form=form)


@auth.requires(auth.has_membership('administrador') or auth.has_membership('emisor'))
def editar_detalle_permiso():
    form = SQLFORM(db.permiso, request.args[0],deletable=True)
    #db(db.detalle.id==request.args[0]).delete()
    if form.accepts(request.vars, session):
        session.flash = 'formulario aceptado'
        redirect(URL("detallar.html"))
    elif form.errors:
        response.flash = 'formulario con errores'
    return dict(form=form)


@auth.requires_login()
def link_cargar_producto(field, type, ref):
    """ función para carga de campos en detalle (no utilizada)"""
    return URL(r=request, f='detallar', vars={'producto': int(field)})


@auth.requires(auth.has_membership('administrador') or auth.has_membership('emisor'))
def cargar_producto():
    los_productos = db(db.producto.id > 0).select()
    if len(los_productos) < 1: raise HTTP(500, "La tabla productos está vacía.")
    return dict(productos=los_productos)


@auth.requires(auth.has_membership('administrador') or auth.has_membership('emisor'))
def finalizar():
    campos_encabezado = [
        'fecha_cbte','tipo_cbte','punto_vta', 'webservice','cbte_nro', 'concepto',
        'permiso_existente', 'dst_cmp',
        'nombre_cliente', 'tipo_doc', 'nro_doc', 'domicilio_cliente',
        'id_impositivo',
        'moneda_id', 'moneda_ctz', 'obs_comerciales', 'obs', 'forma_pago',
        'fecha_venc_pago', 'fecha_serv_desde', 'fecha_serv_hasta',]
    form = SQLFORM(db.comprobante, session.comprobante_id,
                   fields=campos_encabezado, readonly=True)

    comprobante = db(db.comprobante.id==session.comprobante_id).select().first()

    return dict(form=form, comprobante=comprobante)
