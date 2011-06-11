# -*- coding: utf-8 -*- 

def index():
    """
    example action using the internationalization operator T and flash
    rendered by views/default/index.html or views/generic.html
    """
    
    if not session.bienvenida:
        response.flash = T('FacturaLibre. Aplicación web para factura electrónica')
        session.bienvenida = True
    
    return dict(message=T('FacturaLibre. Aplicación web para factura electrónica'))


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
    
    # Redirigir autenticación a protocolo https

    """
    # redirigir autenticación a https (autenticación por httpd genera una excepción en sqlite)
    try:
        if request.env.server_port == "80":
            redirect("https://" + str(request.env.http_host) + str(request.url))
            response.flash = "La autenticación requiere una conexión segura."
    except (AttributeError, KeyError, ValueError):
        response.flash = "La autenticación requiere una conexión segura."
    """
    
    form=auth()
    return dict(form=form)


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



def mensaje():
    mensaje = session.mensaje or None
    session.mensaje = None
    return dict(mensaje = mensaje)
