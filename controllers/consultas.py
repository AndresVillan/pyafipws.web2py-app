# coding: utf8
# try something like
import datetime
import json

def index(): return dict(message="momentaneamente no implementado")

def detalle():
    comprobante, detalle = None, None
    el_id = int(request.args[1])
    comprobante = db(db.comprobante.id == el_id).select().first()
    detalle = db(db.detalle.comprobante_id == el_id).select()

    return dict(comprobante = BEAUTIFY(comprobante.as_dict()), detalle = BEAUTIFY(detalle.as_dict()))


def comprobantes():
    """ Consulta de comprobantes con parámetros para filtro """
    form_enviado = False
   
    form = SQLFORM.factory(Field('periodo', 'integer', \
    requires = IS_IN_SET([y for y in range(1900, 2020)]), \
    default=datetime.datetime.now().year), Field('tipo', \
    requires = IS_NULL_OR(IS_IN_DB(db, db.tipo_cbte.cod, \
    '%(desc)s')) \
    ), Field('cliente', \
    requires = IS_NULL_OR(IS_IN_DB(db, db.cliente.nombre_cliente, \
    '%(nombre_cliente)s')) \
    ), Field('desde_fecha', type="date"), Field('hasta_fecha', type="date")\
    , Field('desde_cbte'), \
    Field('hasta_cbte'), Field('ordenar_campo', \
    requires = IS_IN_SET(db.comprobante.fields()), default = "id"), \
    Field('ordenar_sentido', requires = IS_IN_SET(['asc', 'desc']), default = 'asc' ), \
    Field('registros', type="integer") )

    if form.accepts(request.vars, session, keepvalues = True):
        # conservar los valores del form
        pass

    else:
        if form.errors:
            response.flash = "Hay errores en la consulta"
        
    if "desde_fecha" in request.vars.keys():
        session.consulta_comprobante = None
        form_enviado = True

    else:
        if not ("seccion" in request.vars.keys()):
            # no se envió una consulta
            return dict(los_comprobantes = None, \
        los_link = None, anterior = None, \
        posterior = None, seccion = None, \
        laseccion = None, form = form, \
        consulta = False, registros = None)

    if "nueva" in request.vars.keys():
        if request.vars["nueva"] == "true":
            session.consulta_comprobante = None   
             
    anterior = None
    posterior = None
    los_link = None
    seccion = 0
    la_seccion = ""
    primera = None
    ultima = None
    
    # recuperar datos de filtrado
    try:
        filtro_campo = "id.comprobante. " + request.vars["filtro_campo"]
        filtro_valor = request.vars["filtro_valor"]
    except KeyError:
        filtro_campo = None
        filtro_valor = None
    try:
        ordenar_campo = request.vars["ordenar_campo"]
        ordenar_sentido = request.vars["ordenar_sentido"]

    except KeyError:
        ordenar_campo = "id"
        ordenar_sentido = "asc"

    # registros por página
    # si se especificó en formulario y es un entero
    # actualizar el valor en session
    try:
        session.consulta_registros = int(request.vars["registros"])
        registros = session.consulta_registros
    except (KeyError, ValueError):
        # no se pasó cantidad por formulario. Buscar en session
        try:
            registros = int(session.consulta_registros)
        except (ValueError, AttributeError, TypeError):
            session.consulta_registros = 30
            registros = 30
            
    # si no se almacenó la consulta en session,
    # crear una nueva (agrupa los id en un arreglo
    # bidimensional de objs. list
    
    if session.consulta_comprobante == None:
        anterior = None
        posterior = None
        los_link = None

        try:
            el_periodo = datetime.datetime(int(request.vars["periodo"]), 1, 1)
            el_set = db((db.comprobante.fecha_cbte >= str(\
            el_periodo.year) + "-01-01") & (db.comprobante.fecha_cbte < str(el_periodo.year +1) + "-01-01"))
        except (ValueError, KeyError, AttributeError), e:
            el_periodo = datetime.datetime(datetime.datetime.now().year, 1, 1)        
            el_set = db((db.comprobante.fecha_cbte >= str(\
            el_periodo.year) + "-01-01") & (db.comprobante.fecha_cbte < str(el_periodo.year +1) + "-01-01"))

        # subset sucesivos según filtro
        if form_enviado:
            if "tipo" in request.vars.keys():
                if request.vars["tipo"] != "":
                    el_set = el_set(db.comprobante.tipo_cbte == request.vars["tipo"])

            if "cliente" in request.vars.keys():
                if request.vars["cliente"] != "":
                    el_set = el_set(db.comprobante.nombre_cliente == request.vars["cliente"])

            if "desde_fecha" in request.vars.keys():
                if request.vars["desde_fecha"] != "":
                    el_set = el_set(db.comprobante.fecha_cbte >= request.vars["desde_fecha"])

            if "hasta_fecha" in request.vars.keys():
                if request.vars["hasta_fecha"] != "":
                    el_set = el_set(db.comprobante.fecha_cbte <= request.vars["hasta_fecha"])

            if "desde_cbte" in request.vars.keys():
                if request.vars["desde_cbte"] != "":
                    el_set = el_set(db.comprobante.cbte_nro >= int(request.vars["desde_cbte"]))

            if "hasta_cbte" in request.vars.keys():
                if request.vars["hasta_cbte"] != "":
                    el_set = el_set(db.comprobante.cbte_nro <= request.vars["hasta_cbte"])

        if (filtro_campo and filtro_valor):
            el_set = el_set(filtro_campo + "==" + filtro_valor)

        # acá da error la consulta si los parámetros son cadenas vacías
        if not ordenar_campo: ordenar_campo = "id"
        if not ordenar_sentido: ordenar_sentido = "asc"
        comprobantes = el_set.select(orderby=ordenar_campo + \
        " " + ordenar_sentido)

        session.consulta_comprobante = list()
        contador = 0
        nro_seccion = -1
        for cbt in comprobantes:
            contador +=1
            if (contador > (int(registros))) or (nro_seccion == -1):
                contador = 0
                session.consulta_comprobante.append(list())   
                nro_seccion += 1
                session.consulta_comprobante[nro_seccion].append(cbt.cbte_nro)

            else:
                session.consulta_comprobante[nro_seccion].append(cbt.cbte_nro)


        if len(session.consulta_comprobante) > 0:
            los_comprobantes = db(db.comprobante.cbte_nro.belongs(\
            session.consulta_comprobante[0])).select(orderby=ordenar_campo + \
            " " + ordenar_sentido)
        else:
            los_comprobantes = None
            session.consulta_comprobante = None

    else:
        # Si existe una consulta previa,
        # devuelve un obj. rows con la sección especificada
        # en request.vars
        # Crear una lista de resultados para navegar entre secciones

        try:
            seccion = request.vars["seccion"]
            los_comprobantes = db(db.comprobante.cbte_nro.belongs(\
            session.consulta_comprobante[int(seccion)])).select(\
            orderby=ordenar_campo + " " + ordenar_sentido)

        except KeyError:
            seccion = 0
            los_comprobantes = db(db.comprobante.cbte_nro.belongs(\
            session.consulta_comprobante[0])).select(orderby=ordenar_campo + \
            " " + ordenar_sentido)
            
    # preparar los link a cada seccion
    if session.consulta_comprobante != None:    
        los_link = [\
        A( str(session.consulta_comprobante[secc][0])+ \
        "-" + str(session.consulta_comprobante[secc][-1]),\
        _href=URL(r=request, \
        c="consultas", f="comprobantes", vars={"seccion": secc})) \
        for secc in range(len(session.consulta_comprobante))]    

        # obtengo la sección seleccionada como texto
        if len(los_link) > 0:
            la_seccion = los_link[int(seccion)]
            primera = A( 'Primera', _href=URL(r=request, \
        c="consultas", f="comprobantes", vars={"seccion": 0}))
            ultima = A( 'Última', _href=URL(r=request, \
        c="consultas", f="comprobantes", vars={"seccion": len(los_link) -1}))

        if int(seccion) > 0:
            anterior = A("Anterior", _href=URL(r=request, \
            c="consultas", f="comprobantes", vars={"seccion": int(seccion) -1}))
        else: anterior = None
        
        if int(seccion) < len(los_link) -1:
            posterior = A("Posterior", _href=URL(r=request, \
            c="consultas", f="comprobantes", vars={"seccion": int(seccion) +1}))
        else:
            posterior = None

    if los_comprobantes != None:
        los_comprobantes = DIV(SQLTABLE(los_comprobantes, linkto=URL(\
        r=request, c='consultas', f='detalle')), _style="overflow: auto;")
    

    return dict(los_comprobantes = los_comprobantes, \
    los_link = los_link, anterior = anterior, \
    posterior = posterior, seccion = seccion, laseccion = la_seccion, \
    form = form, consulta = True, registros = registros, primera = primera, \
    ultima = ultima)


def detalles():
    return dict(detalles = db(db.detalle).select())


def producto():
    """ lista de valores de un producto """
    el_producto = db.producto[int(request.args[0])]
    iva = db.iva[el_producto.iva_id]
    return dict(codigo = el_producto.codigo, iva = iva.cod, umed = el_producto.umed, \
    umed_desc = db.umed[el_producto.umed].desc, ds = el_producto.ds, ncm = el_producto.ncm, sec = el_producto.sec, precio = el_producto.precio, iva_aliquota = iva.aliquota, iva_desc = iva.desc)


def productoporcodigo():
    """ lista de valores de un producto """
    existente = False
    el_producto = db(db.producto.codigo == request.args[0]).select().first()
    try:
        id = el_producto.id
        existente = True
    except (KeyError, AttributeError):
        id = None
    return dict(id = id, existente = existente)
