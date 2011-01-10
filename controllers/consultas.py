# coding: utf8
# try something like
def index(): return dict(message="momentaneamente no implementado")

def detalle():
    comprobante, detalle = None, None
    el_id = int(request.args[1])
    cbte = db(db.comprobante.id == el_id).select()
    detalle = db(db.detalle.comprobante_id == el_id).select()
            
    if ((detalle != None) and (len(detalle) > 0)):
        detalle = DIV(SQLTABLE(detalle), _style="overflow: auto;")
    else:
        detalle = None

    return dict(comprobante = DIV(cbte, _style="overflow: auto;"\
    ), detalle = detalle)


def comprobantes():

    """ Consulta de comprobantes con parámetros para filtro """
    form_enviado = False
    
    form = SQLFORM.factory(Field('tipo', \
    requires = IS_IN_DB(db, db.tipo_cbte.cod, \
    '%(desc)s') \
    ), Field('cliente', \
    requires = IS_IN_DB(db, db.cliente.nombre_cliente, \
    '%(nombre_cliente)s') \
    ), Field('desde_fecha', type="date"), Field('hasta_fecha', type="date")\
    , Field('desde_cbte'), \
    Field('hasta_cbte'), Field('registros', type="integer") )

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

        el_set = db(db.comprobante)

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

        comprobantes = el_set.select(orderby=ordenar_campo + \
        " " + ordenar_sentido)

        session.consulta_comprobante = list()
        contador = 0
        nro_seccion = -1
        for cbt in comprobantes:
            if (contador > (int(registros) -1)) or (nro_seccion == -1):
                contador = 0
                session.consulta_comprobante.append(list())   
                nro_seccion += 1
                session.consulta_comprobante[nro_seccion].append(int(cbt.cbte_nro))

            else:
                session.consulta_comprobante[nro_seccion].append(int(cbt.cbte_nro))
                contador +=1

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
    form = form, consulta = True, registros = registros)
