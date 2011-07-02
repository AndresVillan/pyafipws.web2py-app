# -*- coding: utf-8 -*-

""" Copyright 2011 Alan Etkin, spametki@gmail.com.

Este programa se distribuye bajo los términos de la licencia AGPLv3.

This program is free software: you can redistribute it and/or modify
it under the terms of the Affero GNU General Public License as published by
the Free Software Foundation, version 3 of the License, or any later
version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the Affero GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""

import datetime, random


#########################################################################
## This is a samples controller
## - index is the default action of any application
## - user is required for authentication and authorization
## - download is for downloading files uploaded in the db (does streaming)
## - call exposes all registered services (none by default)
#########################################################################

def formato_moneda(valor):
    try:
        return "%.2f" % valor
    except (TypeError, ValueError):
        return valor

@auth.requires(auth.has_membership('administrador') or auth.has_membership('emisor') or auth.has_membership('invitado'))
def index():
    """
    Formulario de cbte con tablas jqgrid.
    
    example action using the internationalization operator T and flash
    rendered by views/default/index.html or views/generic.html
    """
    if not session.has_key('ialt'):
        response.flash = T('FacturaLibre: interfaz de usuario alternativa')
        session.comprobante = None
        session.ialt = True

    if "nuevo" in request.args:
        session.comprobante = None

    if not control_acceso(session):
        raise HTTP(503,"Se alcanzó límite de consultas")
    else:
        if session.comprobante:
            pass
        else:
            variables = db(db.variables).select().first()
            variablesusuario = db(db.variablesusuario.usuario == auth.user_id).select().first()

            # variables por defecto de cbte

            # session.comprobante = db.comprobante.insert()
            session.comprobante = db.comprobante.insert(\
            usuario = auth.user_id, punto_vta = int(variablesusuario.puntodeventa.numero), \
            moneda_id = int(variablesusuario.moneda), webservice = str(variablesusuario.webservice), \
            tipocbte = int(variablesusuario.tipocbte), \
            fecha_venc_pago = str(datetime.datetime.now() + datetime.timedelta(variablesusuario.venc_pago))[0:10], \
            forma_pago = str(variablesusuario.forma_pago))

        cbte = db(db.comprobante.id == session.comprobante).select().first()
        
        # form = crud.update(db.comprobante, cbte.id, deletable = False)

        # if form.errors:
        #    response.flash = "¡Error al procesar el comprobante!"

        return dict(message=T('Hello World'), form = None, comprobante = cbte)


@auth.requires(auth.has_membership('administrador') or auth.has_membership('emisor') or auth.has_membership('invitado'))
def form_cbte():
    if not session.comprobante: return dict(cbte_update_form = None)

    variables = db(db.variablesusuario.usuario == auth.user_id).select().first()
    if variables: 
        webservice = variables.webservice
    else:
        webservice = 'wsfev1'

    campos_generales = ['id_ws', 'webservice',  'fecha_cbte', 'tipocbte', 'punto_vta', 'cbte_nro', 'concepto', 'imp_total', 'imp_tot_conc', 'imp_neto', 'impto_liq', 'impto_liq_rni', 'imp_op_ex', 'impto_perc', 'imp_iibb', 'imp_subtotal', 'imp_trib', 'impto_perc_mun', 'imp_internos', 'moneda_id', 'moneda_ctz', 'obs_comerciales', 'obs', 'forma_pago', 'zona', 'fecha_venc_pago', 'fecha_serv_desde', 'fecha_serv_hasta', 'formato_id']
    if webservice == "wsfex": campos_generales += ['permiso_existente', 'id_impositivo', 'dst_cmp', 'dstcuit', 'incoterms', 'incoterms_ds', 'idioma_cbte', 'tipo_expo', 'operacion']
    
    cbte_update_form = SQLFORM(db.comprobante, session.comprobante, \
    fields = campos_generales, keepvalues = True, _id="formulario_comprobante")

    if cbte_update_form.accepts(request.vars, session, formname = "actualizar_comprobante"):
        response.flash = "Se registraron los cambios!"
    elif cbte_update_form.errors:
        response.flash = "Hay errores en el formulario!"
    else:
        cbte_update_form.vars.webservice = webservice
    
    return dict(cbte_update_form = cbte_update_form)


@auth.requires(auth.has_membership('administrador') or auth.has_membership('emisor') or auth.has_membership('invitado'))
def reprocesar():
    session.ialt = True
    try:
        session.comprobante = request.args[0]
    except (AttributeError, KeyError, TypeError, ValueError):
        response.flash = "La referencia de cbte. no es válida."

    redirect(URL(r=request, c="ialt", f="index"))


def user():
    """
    exposes:
    http://..../[app]/default/user/login
    http://..../[app]/default/user/logout
    http://..../[app]/default/user/register
    http://..../[app]/default/user/profile
    http://..../[app]/default/user/retrieve_password
    http://..../[app]/default/user/change_password
    use @auth.requires_login()
        @auth.requires_membership('group name')
        @auth.requires_permission('read','table name',record_id)
    to decorate functions that need access control
    """
    return dict(form=auth())


def download():
    """
    allows downloading of uploaded files
    http://..../[app]/default/download/[filename]
    """
    return response.download(request,db)


def call():
    """
    exposes services. for example:
    http://..../[app]/default/call/jsonrpc
    decorate with @services.jsonrpc the functions to expose
    supports xml, json, xmlrpc, jsonrpc, amfrpc, rss, csv
    """
    session.forget()
    return service()



@service.json
def detalles():
    if not control_acceso(session):
        raise HTTP(503,"Se alcanzó límite de consultas")


    lista = []
    undict = None
    respuesta = dict()
    respuesta["page"] = 1
    respuesta["total"] = 1
    respuesta["records"] = 0

    for detalle in db(db.detalle.comprobante == request.args[2]).select():
        undict = dict(id = detalle.id, cell = [detalle.id, detalle.codigo, detalle.ds, detalle.qty, formato_moneda(detalle.precio), detalle.umed.ds, formato_moneda(detalle.imp_total), detalle.iva.ds, detalle.ncm, detalle.sec, formato_moneda(detalle.bonif), formato_moneda(detalle.imp_iva), formato_moneda(detalle.base_imp_iva), formato_moneda(detalle.base_imp_tributo)])
        lista.append(undict)
        respuesta["records"] += 1 # cantidad de registros

    respuesta["rows"] = lista
    return respuesta

@service.json
def items_tributo():
    if not control_acceso(session):
        raise HTTP(503,"Se alcanzó límite de consultas")

    lista = []
    undict = None
    respuesta = dict()
    respuesta["page"] = 1
    respuesta["total"] = 1
    respuesta["records"] = 0

    for item in db(db.detalletributo.comprobante == request.args[2]).select():
        undict = dict(id = item.id, cell = [item.id, item.tributo.ds, formato_moneda(item.base_imp), formato_moneda(item.importe)])
        lista.append(undict)
        respuesta["records"] += 1 # cantidad de registros

    respuesta["rows"] = lista
    return respuesta


@service.json
def cbtes_asoc():
    if not control_acceso(session):
        raise HTTP(503,"Se alcanzó límite de consultas")

    lista = []
    undict = None
    respuesta = dict()
    respuesta["page"] = 1
    respuesta["total"] = 1
    respuesta["records"] = 0

    for item in db(db.comprobanteasociado.comprobante == request.args[2]).select():
        undict = dict(id = item.id, cell = [item.id, item.comprobante, item.asociado])
        lista.append(undict)
        respuesta["records"] += 1 # cantidad de registros

    respuesta["rows"] = lista
    return respuesta

@service.json
def permisos():
    if not control_acceso(session):
        raise HTTP(503,"Se alcanzó límite de consultas")

    lista = []
    undict = None
    respuesta = dict()
    respuesta["page"] = 1
    respuesta["total"] = 1
    respuesta["records"] = 0

    for item in db(db.permiso.comprobante == request.args[2]).select():
        try:
            dst = item.dst_merc.ds
        except (KeyError, AttributeError, ValueError):
            dst = ""
        undict = dict(id = item.id, cell = [item.id, item.tipo_reg, item.id_permiso, dst])
        lista.append(undict)
        respuesta["records"] += 1 # cantidad de registros

    respuesta["rows"] = lista
    return respuesta


@service.json
def productos():
    if not control_acceso(session):
        raise HTTP(503,"Se alcanzó límite de consultas")

    lista = []
    undict = None
    respuesta = dict()
    respuesta["page"] = 1
    respuesta["total"] = 1
    respuesta["records"] = 0

    for producto in db(db.producto).select():
        undict = dict(id = producto.id, cell = [producto.id, producto.ds, formato_moneda(producto.precio), producto.iva.ds])
        lista.append(undict)
        respuesta["records"] += 1 # cantidad de registros

    respuesta["rows"] = lista
    return respuesta

@service.json
def clientes():
    if not control_acceso(session):
        raise HTTP(503,"Se alcanzó límite de consultas")

    lista = []
    undict = None
    respuesta = dict()
    respuesta["page"] = 1
    respuesta["total"] = 1
    respuesta["records"] = 0

    for cliente in db(db.cliente).select():
        undict = dict(id = cliente.id, cell = [cliente.id, cliente.nombre_cliente, cliente.nro_doc, cliente.domicilio_cliente, cliente.email])
        lista.append(undict)
        respuesta["records"] += 1 # cantidad de registros

    respuesta["rows"] = lista
    return respuesta

@service.json
def tributos():
    if not control_acceso(session):
        raise HTTP(503,"Se alcanzó límite de consultas")

    lista = []
    undict = None
    respuesta = dict()
    respuesta["page"] = 1
    respuesta["total"] = 1
    respuesta["records"] = 0

    for tributo in db(db.tributo).select():
        undict = dict(id = tributo.id, cell = [tributo.id, tributo.ds, tributo.aliquota])
        lista.append(undict)
        respuesta["records"] += 1 # cantidad de registros

    respuesta["rows"] = lista
    return respuesta

@service.json
def comprobantes():
    if not control_acceso(session):
        raise HTTP(503,"Se alcanzó límite de consultas")

    fecha_piso = datetime.datetime.now() - datetime.timedelta(31)

    lista = []
    undict = None
    respuesta = dict()
    respuesta["page"] = 1
    respuesta["total"] = 1
    respuesta["records"] = 0

    for cbte in db(db.comprobante.fecha_cbte > fecha_piso).select():
        undict = dict(id = cbte.id, cell = [cbte.id, cbte.id_ws, cbte.webservice, cbte.tipocbte.ds, cbte.cbte_nro])
        lista.append(undict)
        respuesta["records"] += 1 # cantidad de registros

    respuesta["rows"] = lista
    return respuesta

@service.json
def editar_item():
    if not control_acceso(session):
        raise HTTP(503,"Se alcanzó límite de consultas")

    # db.xml.insert(request = str(request.args))
    # db.commit()
    
    mensaje = None
    if request.vars["oper"] == 'edit':
        if request.args[2] == "detalle":
            el_item = db(db.detalle.id == int(request.vars["id"])).select().first()
            el_item.update_record(**request.vars)
            mensaje = "Se modificó el registro nro. " + request.vars["id"]

        elif request.args[2] == "tributo":
            el_item = db(db.detalletributo.id == int(request.vars["id"])).select().first()
            el_item.update_record(**request.vars)
            mensaje = "Se modificó el registro nro. " + request.vars["id"]

        elif request.args[2] == "permiso":
            el_item = db(db.permiso.id == int(request.vars["id"])).select().first()
            el_item.update_record(**request.vars)
            mensaje = "Se modificó el registro nro. " + request.vars["id"]

        elif request.args[2] == "comprobanteasociado":
            el_item = db(db.comprobanteasociado.id == int(request.vars["id"])).select().first()
            el_item.update_record(**request.vars)
            mensaje = "Se modificó el registro nro. " + request.vars["id"]


    elif request.vars["oper"] == 'del':
        if request.args[2] == "detalle":
            db(db.detalle.id == int(request.vars["id"])).delete()
            mensaje = "Se eliminó el registro nro. " + request.vars["id"]

        if request.args[2] == "tributo":
            db(db.detalletributo.id == int(request.vars["id"])).delete()
            mensaje = "Se eliminó el registro nro. " + request.vars["id"]

        if request.args[2] == "permiso":
            db(db.permiso.id == int(request.vars["id"])).delete()
            mensaje = "Se eliminó el registro nro. " + request.vars["id"]

        if request.args[2] == "comprobanteasociado":
            db(db.comprobanteasociado.id == int(request.vars["id"])).delete()
            mensaje = "Se eliminó el registro nro. " + request.vars["id"]

    return mensaje


@service.json
def agregar_item():
    if not control_acceso(session):
        raise HTTP(503,"Se alcanzó límite de consultas")

    el_cbte = db(db.comprobante.id == int(request.vars["cbte"])).select().first()
    el_tipo = request.vars.tipo
    # el_id = int(request.vars.id)

    if el_tipo == "producto":
        el_producto = db(db.producto.id == request.vars["id"]).select().first()        
        db.detalle.insert(comprobante = el_cbte.id, codigo = el_producto.codigo, unidadmtx = el_producto.unidadmtx, \
        codigomtx = el_producto.codigomtx, ds = el_producto.ds, precio = el_producto.precio, umed = el_producto.umed, \
        iva = el_producto.iva, ncm = el_producto.ncm, sec = el_producto.sec)
    elif el_tipo == "tributo":
        db.detalletributo.insert(comprobante = el_cbte.id, tributo = request.vars["id"])

    elif el_tipo == "cliente":
        # cambiar el cliente y actualizar el cbte_asoc
        el_cliente = db.cliente[request.vars.id]
        el_cbte.update_record(nombre_cliente = el_cliente.nombre_cliente, \
        tipodoc = el_cliente.tipodoc, nro_doc =  el_cliente.nro_doc, \
        domicilio_cliente = el_cliente.domicilio_cliente, \
        localidad_cliente = el_cliente.localidad_cliente, \
        telefono_cliente = el_cliente.telefono_cliente, \
        provincia_cliente = el_cliente.provincia_cliente, \
        condicioniva_cliente = el_cliente.condicioniva, \
        email = el_cliente.email, id_impositivo = el_cliente.id_impositivo, cp_cliente = el_cliente.cp)

        
    elif el_tipo == "comprobanteasociado":
        cbte_asoc = db(db.comprobante.id == request.vars.id).select().first()
        db.comprobanteasociado.insert(comprobante = el_cbte.id, asociado = cbte_asoc.id)

    elif el_tipo == "permiso":
        db.permiso.insert(comprobante = el_cbte.id)

    return str(request.vars)


@auth.requires(auth.has_membership('administrador') or auth.has_membership('emisor') or auth.has_membership('invitado'))
def vista_previa():
    """ previsualización del comprobante """

    vp_form = FORM(INPUT(_type='submit', _value="Vista previa"), _id="form_vista_previa")
    el_cbte = db(db.comprobante.id == session.comprobante).select().first()
    previsualizacion = None

    # detecto submit (previsualización)
    if vp_form.accepts(request.vars, session, formname = "vista_previa"):
        if el_cbte:
            previsualizacion = SQLFORM(db.comprobante, el_cbte.id, \
            fields = ["id", "webservice", "nombre_cliente", \
            "tipocbte", "imp_total"], readonly = True)
        else:
            previsualizacion = None
    elif vp_form.errors:
        response.flash = "Hay errores en el form."

    return dict(previsualizacion = previsualizacion, vp_form = vp_form)


def control_acceso(session):
    # recuperar ordenes del día

    """
    hoy = datetime.datetime.now()
    dif = datetime.timedelta(1)
    ayer = hoy - dif
    cant_ordenes = db(db.orden.fecha > ayer).count()
    # si se superó el límite de órdenes devolver false
    if cant_ordenes > 500: return False
    else:
        ordenes = db(db.orden.fecha > ayer).select()

    cant_item = 0
    for orden in ordenes:
        cant_item += db(db.item.orden == orden).count()
        # si hay un exceso salir con estado false
        if cant_item > 2500: return False
    """
    return True
