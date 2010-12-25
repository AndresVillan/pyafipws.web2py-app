# coding: utf8
# try something like
def index(): return dict(message="momentaneamente no implementado")

def comprobantes():

    """ Consulta de comprobantes con parámetros para filtro """
    
    anterior = None
    posterior = None
    los_link = None
    seccion = 0    

    # recuperar datos de filtrado

    try:
        filtro_campo = request.vars["filtro_campo"]
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

    try:
        session.consulta_registros = request.vars["registros"]
        registros = session.consulta_registros
    except KeyError:
        try:
            registros = int(session.consulta_registros)
        except KeyError:
            session.consulta_registros = 30
            registros = 30
        except TypeError:
            session.consulta_registros = 30
            registros = 30

    # si no se almacenó la consulta en session,
    # crear una nueva (agrupa los id en un arreglo
    # bidimensional de objs. list
    
    if session.consulta == None:
        if (filtro_campo and filtro_valor):
            el_set = el_set(filtro_campo + "==" + filtro_valor)

        el_set = db(db.comprobante)

        comprobantes = el_set.select(orderby=ordenar_campo + \
        " " + ordenar_sentido)

        session.consulta = list()
        contador = 0
        nro_seccion = -1
        for cbt in comprobantes:
            if (contador > (registros -1)) or (nro_seccion == -1):
                contador = 0
                session.consulta.append(list())   
                nro_seccion += 1
                session.consulta[nro_seccion].append(cbt.id)

            else:
                session.consulta[nro_seccion].append(cbt.id)
                contador +=1

        if len(session.consulta) > 0:
            los_comprobantes = db(db.comprobante.id.belongs(\
            session.consulta[0])).select(orderby=ordenar_campo + \
            " " + ordenar_sentido)
        else:
            los_comprobantes = None
            session.consulta = None

    else:
        try:
            seccion = request.vars["seccion"]
            los_comprobantes = db(db.comprobante.id.belongs(\
            session.consulta[int(seccion)])).select(\
            orderby=ordenar_campo + " " + ordenar_sentido)

        except KeyError:
            seccion = 0
            los_comprobantes = db(db.comprobante.id.belongs(\
            session.consulta[0])).select(orderby=ordenar_campo + \
            " " + ordenar_sentido)
            
    # Si existe una consulta previa,
    # devuelve un obj. rows con la sección especificada
    # en request.vars
    # Crear una lista de resultados para navegar entre secciones
    
    if session.consulta != None:
        los_link = [A(str(secc + 1), _href=URL(r=request, \
        c="consultas", f="comprobantes", vars={"seccion": secc})) \
        for secc in range(len(session.consulta))]    

        if seccion > 0:
            anterior = A("Anterior", _href=URL(r=request, \
            c="consultas", f="comprobantes", vars={"seccion": seccion}))
        else: anterior = None
        
        if seccion < len(los_link) -1:
            posterior = A("Posterior", _href=URL(r=request, \
            c="consultas", f="comprobantes", vars={"seccion": seccion}))
        else:
            posterior = None

    else:
        los_link = None

    # los datos de style deberían ir en un archivo estático css   
    return dict(los_comprobantes = DIV(SQLTABLE(los_comprobantes), _style="overflow: auto;"), \
    los_link = los_link, anterior = anterior, posterior = posterior)

