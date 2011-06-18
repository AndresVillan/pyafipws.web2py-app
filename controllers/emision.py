# -*- coding: utf-8 -*-
import datetime

@auth.requires(auth.has_membership('administrador') or auth.has_membership('emisor') or auth.has_membership('invitado'))
def comprobante_tabla_clientes():
    """ Muestra una tabla para establecer un cliente """
    los_clientes = db(db.cliente).select()
    if len(los_clientes) < 1: raise HTTP(500, "La tabla de clientes está vacía")
    return dict(clientes = los_clientes)

@auth.requires(auth.has_membership('administrador') or auth.has_membership('emisor') or auth.has_membership('invitado'))
def comprobante_seleccionar_cliente():
    el_cliente = int(request.args[1])
    session.cliente_seleccionado = el_cliente
    response.flash = "Nuevo cliente seleccionado"
    redirect(URL(r=request, c='emision', f='iniciar'))


@auth.requires(auth.has_membership('administrador') or auth.has_membership('emisor') or auth.has_membership('invitado'))
def reprocesar():
    try:
        session.comprobante = request.args[0]
    except (AttributeError, KeyError, TypeError, ValueError):
        response.flash = "La referencia de cbte. no es válida."

    redirect(URL(r=request, c="emision", f="iniciar"))



@auth.requires(auth.has_membership('administrador') or auth.has_membership('emisor') or auth.has_membership('invitado'))
def iniciar():

    variables = None
    webservice = None
    puntodeventa = None
    cliente = None
    variablesusuario = None
    
    fecha = datetime.datetime.now()

    if 'nuevo' in request.args: session.comprobante = None

    try:
        getattr(session, 'comprobante')
    except AttributeError:
        session.comprobante = None

    variables = db(db.variables).select().first()
    if not variables:
        raise HTTP(500, "No se cargaron las opciones globales para formularios.")
    variablesusuario = db(db.variablesusuario.usuario == auth.user_id).select().first()
    if not variablesusuario:
        db.variablesusuario.insert(usuario = auth.user_id, \
            puntodeventa = variables.puntodeventa, \
            moneda = variables.moneda, \
            webservice = variables.webservice, \
            tipocbte = variables.tipocbte, \
            venc_pago = variables.venc_pago, \
            forma_pago = variables.forma_pago
        )
        response.flash = "Se generó el registro de variables para formularios del usuario."


    "Crear/modificar datos generales del comprobante"
    # campos a mostrar:
    campos_generales = ['fecha_cbte','tipocbte', 'concepto', \
    'moneda_id', 'moneda_ctz','imp_iibb', 'obs_comerciales', \
    'obs', 'forma_pago', 'fecha_venc_pago', 'fecha_serv_desde', 'fecha_serv_hasta']

    if 'wsfex' == variablesusuario.webservice:
        campos_generales += ['dst_cmp', 'dstcuit', 'id_impositivo', 'incoterms', 'incoterms_ds', 'idioma_cbte', 'tipo_expo', 'permiso_existente']

    # creo un formulario para el comprobante (TODO: modificar)
    form = SQLFORM(db.comprobante, session.comprobante,
                   fields=campos_generales)

    # si el cbte es nuevo pre cargar el formulario
    if not session.comprobante:
        # Recupero opciones del registro global de variables
        form.vars.webservice = variablesusuario.webservice
        form.vars.tipocbte = variablesusuario.tipocbte
        form.vars.punto_vta = variablesusuario.puntodeventa.numero
        form.vars.moneda_id = variablesusuario.moneda
        form.vars.forma_pago = variablesusuario.forma_pago
       
        form.vars.fecha_venc_pago = str(fecha + datetime.timedelta(variablesusuario.venc_pago))[0:10]
        form.vars.fecha_vto = str(fecha + datetime.timedelta(variablesusuario.venc_pago))[0:10]
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
        form.vars.tipodoc = cliente.tipodoc
        form.vars.nro_doc = cliente.nro_doc
        form.vars.domicilio_cliente = cliente.domicilio_cliente
        form.vars.telefono_cliente = cliente.telefono_cliente
        form.vars.localidad_cliente = cliente.localidad_cliente.ds
        form.vars.provincia_cliente = cliente.provincia_cliente.ds
        form.vars.email = cliente.email
        form.vars.cp_cliente = cliente.cp

    # valido el formulario (si han enviado datos)
    if form.accepts(request.vars, session, dbio=False, formname="iniciar_comprobante"):
        """
        session.webservice = form.vars.webservice
        session.tipocbte = form.vars.tipocbte
        session.moneda_id = form.vars.moneda_id
        session.punto_vta = form.vars.punto_vta
        session.forma_pago = form.vars.forma_pago
        """
        
        if not session.comprobante:
            # insertar el comprobante
            id = db.comprobante.insert(**form.vars)
            session.flash = "Comprobante creado..."
        else:
            id = session.comprobante
            
            # no cambiar el webservice si es un cbte
            # enviado
            if db.comprobante[id].resultado:
                form.vars.webservice = db.comprobante[id].webservice
                
            db(db.comprobante.id==id).update(**form.vars)
            session.flash = "Comprobante actualizado..."
        # guardo el ID del registro creado en la sesión
        session.comprobante = id
        # redirijo a la siguiente página
        redirect(URL("detallar"))
    elif form.errors:
       response.flash = '¡Hay errores en el formulario!'

    return dict(form=form, cliente = cliente, variablesusuario = variablesusuario)


@auth.requires(auth.has_membership('administrador') or auth.has_membership('emisor') or auth.has_membership('invitado'))
def detallar():
    # creo un formulario para el comprobante (TODO: modificar)
    campos_encabezado = ['fecha_cbte','tipocbte','punto_vta','cbte_nro', 'webservice' ]
    form = SQLFORM(db.comprobante, session.comprobante,
                   fields=campos_encabezado, readonly=True)
    comprobante = db(db.comprobante.id==session.comprobante).select().first()

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
        valor_iva = db.iva[form.vars.iva].aliquota
        if not valor_iva: valor_iva = 0.00
        form.vars.imp_iva = imp_neto * valor_iva
        form.vars.imp_total = imp_neto + form.vars.imp_iva
        form.vars.base_imp_iva = imp_neto
        form.vars.base_imp_tributo = imp_neto
    except (ValueError, KeyError, AttributeError), e:
        db.xml.insert(request = "Error al calcular el ítem", response = str(e))


@auth.requires(auth.has_membership('administrador') or auth.has_membership('emisor')  or auth.has_membership('invitado'))
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
        form.vars.iva = request.vars.iva
        form.vars.precio = request.vars.precio
        form.vars.umed = request.vars.umed
        form.vars.ncm = request.vars.ncm
        form.vars.sec = request.vars.sec
        form.vars.qty = request.vars.qty
        form.vars.bonif = request.vars.bonif
        umed_texto = db.umed[form.vars.umed].ds
        iva_texto = db.iva[form.vars.iva].ds
         
    else:
        try:
            producto = db(db.producto.id == int(request.vars["producto"])).select().first()
            form.vars.codigo = producto.codigo
            form.vars.ds = producto.ds
            form.vars.iva = producto.iva
            form.vars.precio = producto.precio
            form.vars.umed = producto.umed
            form.vars.ncm = producto.ncm
            form.vars.sec = producto.sec
            form.vars.qty = qty
            form.vars.bonif = bonif
        
            iva = db.iva[producto.iva]
            iva_texto = iva.ds
            umed_texto = db.umed[producto.umed].ds
            try:
                iva_valor = iva.aliquota
            except (ValueError, AttributeError, KeyError, TypeError):
                iva_valor = 0
            if not iva_valor: iva_valor = 0.0
            form.vars.imp_iva = producto.precio * iva_valor * qty
            form.vars.imp_total = (producto.precio * qty) + (producto.precio * iva_valor * qty)
        
        except KeyError:
             # no se especifica producto pre-cargado
            # en el formulario
            pass
   
    db.detalle.comprobante.default = session.comprobante
    if form.accepts(request.vars, session, keepvalues = True, onvalidation = calcular_item_detalle, formname="editar_detalle"):
        response.flash ="Detalle agregado!"

    elif form.errors:
        response.flash = "El detalle tiene errores!: " + str(form.errors.keys()) + " " + str(form.errors.values())
        
    detalles = db(db.detalle.comprobante==session.comprobante).select()

    total = "%.2f" % sum([detalle.imp_total for detalle in detalles], 0.00)
    # agregado por marcelo
    comprobante = db(db.comprobante.id==session.comprobante).select().first()
    tipocbte = db(db.tipocbte.id==comprobante.tipocbte).select().first()
    for p in range(len(detalles)):
        iva = db(db.iva.id==detalles[p].iva).select().first()
        try:
            if tipocbte.discriminar:
                detalles[p].imp_iva = detalles[p].qty * detalles[p].precio * iva.aliquota
                
            else:
                detalles[p].imp_iva = detalles[p].qty * detalles[p].precio * (1+iva.aliquota)
        except (ValueError, KeyError, AttributeError, TypeError):
            detalles[p].imp_iva = 0.00
            
    # fin marcelo
    return dict(form=form, total=total,
                detalles=detalles, iva_ds = iva_texto, umed_ds = umed_texto, iva_aliquota = iva_valor)


@auth.requires(auth.has_membership('administrador') or auth.has_membership('emisor')  or auth.has_membership('invitado'))
def detalle_tributo():
    comprobante = None
    tributo = None
    base_imp = None
    importe = None

    form = SQLFORM(db.detalletributo, keepvalues = True, _class="excluir", _id="formulario_ingreso_detalle_tributo")

    if request.vars.tributo:    
        form.vars.comprobante = request.vars.comprobante
        form.vars.tributo = request.vars.tributo
        form.vars.base_imp = request.vars.base_imp
        form.vars.importe = request.vars.importe
        form.vars.comprobante = session.comprobante
         
    else:
        try:
            form.vars.comprobante = request.vars.comprobante
            form.vars.tributo = request.vars.tributo
            form.vars.base_imp = request.vars.base_imp
            form.vars.importe = request.vars.importe
            form.vars.comprobante = session.comprobante
        
        except KeyError:
             # no se especifica tributo
            # en el formulario
            pass
   
    db.detalletributo.comprobante.default = session.comprobante
    
    if form.accepts(request.vars, session, keepvalues = True, formname="agregar_tributo"):
        response.flash ="Detalle de tributo agregado!"

    elif form.errors:
        response.flash = "El detalle tiene errores!: " + str(form.errors.keys()) + " " + str(form.errors.values())
        
    los_tributos = db(db.detalletributo.comprobante==session.comprobante).select()
    return dict(form=form, tributos=los_tributos)


@auth.requires(auth.has_membership('administrador') or auth.has_membership('emisor')  or auth.has_membership('invitado'))
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
        form.vars.comprobante = session.comprobante
         
    else:
        try:
            form.vars.id_permiso = request.vars.id_permiso
            form.vars.tipo_reg = request.vars.tipo_reg
            form.vars.dst_merc = request.vars.dst_merc
            form.vars.comprobante = session.comprobante
        
        except KeyError:
             # no se especifica tributo
            # en el formulario
            pass
   
    db.permiso.comprobante.default = session.comprobante
    
    if form.accepts(request.vars, session, keepvalues = True, formname="agregar_permiso"):
        response.flash ="Detalle de permiso agregado!"

    elif form.errors:
        response.flash = "El detalle tiene errores!: " + str(form.errors.keys()) + " " + str(form.errors.values())
        
    los_permisos = db(db.permiso.comprobante==session.comprobante).select()
    return dict(form=form, permisos=los_permisos)


@auth.requires(auth.has_membership('administrador') or auth.has_membership('emisor')  or auth.has_membership('invitado'))
def detalle_asociado():
    asoc_cbte_nro = None
    asoc_tipocbte = None
    asoc_punto_vta = None

    form = SQLFORM.factory(
        Field('asoc_cbte_nro', requires=IS_NOT_EMPTY()),
        Field('asoc_tipocbte', requires=IS_NOT_EMPTY()),
        Field('asoc_punto_vta', requires=IS_NOT_EMPTY()), \
        keepvalues = True, _class="excluir", _id="formulario_ingreso_detalle_asociado")
        
    # db.comprobanteasociado.comprobante.default = session.comprobante
    
    if form.accepts(request.vars, session, formname="agregar_cbteasoc"):
        cbtasoc = None
        for cbte in db(db.comprobante.cbte_nro == form.vars.asoc_cbte_nro).select():
            if cbte.tipocbte.id == int(form.vars.asoc_tipocbte):
                if cbte.punto_vta == db.puntodeventa[form.vars.asoc_punto_vta].numero:
                    if cbte.webservice == db.comprobante[session.comprobante].webservice:
                        cbtasoc = db.comprobanteasociado.insert(comprobante = int(str(session.comprobante)), \
                        asociado = int(str(cbte.id)))
                        response.flash ="Cbte asociado agregado!:"
        if not cbtasoc: response.flash = "El cbte asociado no es válido"

    elif form.errors:
        response.flash = "El cbte asociado tiene errores!: " + \
        str(form.errors.keys()) + " " + str(form.errors.values())

    los_asociados = db(db.comprobanteasociado.comprobante==session.comprobante).select()
    return dict(form=form, asociados=los_asociados)


@auth.requires(auth.has_membership('administrador') or auth.has_membership('emisor') or auth.has_membership('invitado'))
def editar_detalle():
    form = SQLFORM(db.detalle, request.args[0],deletable=True, onvalidation = calcular_item_detalle)
    #db(db.detalle.id==request.args[0]).delete()
    if form.accepts(request.vars, session, formname="edicion_detalle"):
        session.flash = 'formulario aceptado'
        redirect(URL("detallar.html"))
    elif form.errors:
        response.flash = 'formulario con errores'
    return dict(form=form)


@auth.requires(auth.has_membership('administrador') or auth.has_membership('emisor') or auth.has_membership('invitado'))
def editar_detalle_tributo():
    form = SQLFORM(db.detalletributo, request.args[0],deletable=True)
    #db(db.detalle.id==request.args[0]).delete()
    if form.accepts(request.vars, session, formname="edicion_tributo"):
        session.flash = 'formulario aceptado'
        redirect(URL("detallar.html"))
    elif form.errors:
        response.flash = 'formulario con errores'
    return dict(form=form)


@auth.requires(auth.has_membership('administrador') or auth.has_membership('emisor') or auth.has_membership('invitado'))
def editar_detalle_asociado():
    form = SQLFORM(db.comprobanteasociado, request.args[0],deletable=True)
    #db(db.detalle.id==request.args[0]).delete()
    if form.accepts(request.vars, session, formname="edicion_detalle_asociado"):
        session.flash = 'formulario aceptado'
        redirect(URL("detallar.html"))
    elif form.errors:
        response.flash = 'formulario con errores'
    return dict(form=form)


@auth.requires(auth.has_membership('administrador') or auth.has_membership('emisor') or auth.has_membership('invitado'))
def editar_detalle_permiso():
    form = SQLFORM(db.permiso, request.args[0],deletable=True)
    #db(db.detalle.id==request.args[0]).delete()
    if form.accepts(request.vars, session, formname="edicion_detalle_permiso"):
        session.flash = 'formulario aceptado'
        redirect(URL("detallar.html"))
    elif form.errors:
        response.flash = 'formulario con errores'
    return dict(form=form)


@auth.requires_login()
def link_cargar_producto(field, type, ref):
    """ función para carga de campos en detalle (no utilizada)"""
    return URL(r=request, f='detallar', vars={'producto': int(field)})


@auth.requires(auth.has_membership('administrador') or auth.has_membership('emisor') or auth.has_membership('invitado'))
def cargar_producto():
    los_productos = db(db.producto.id > 0).select()
    if len(los_productos) < 1: raise HTTP(500, "La tabla productos está vacía.")
    return dict(productos=los_productos)


@auth.requires(auth.has_membership('administrador') or auth.has_membership('emisor') or auth.has_membership('invitado'))
def finalizar():
    campos_encabezado = [
        'fecha_cbte','tipocbte','punto_vta', 'webservice','cbte_nro', 'concepto',
        'permiso_existente', 'dst_cmp',
        'nombre_cliente', 'tipodoc', 'nro_doc', 'domicilio_cliente',
        'id_impositivo',
        'moneda_id', 'moneda_ctz', 'obs_comerciales', 'obs', 'forma_pago',
        'fecha_venc_pago', 'fecha_serv_desde', 'fecha_serv_hasta',]
    form = SQLFORM(db.comprobante, session.comprobante,
                   fields=campos_encabezado, readonly=True)

    comprobante = db(db.comprobante.id==session.comprobante).select().first()

    return dict(form=form, comprobante=comprobante)
