# -*- coding: utf-8 -*- 

#########################################################################
## Customize your APP title, subtitle and menus here
#########################################################################

response.title = ""
response.subtitle = ""

##########################################
## this is the main application menu
## add/remove items as required
##########################################

response.menu = [
    (T('Inicio'), False, URL(request.application,'default','index'), []),
    
    (T('Emisión'), False, None, [\
(T('Secuencial'), False, URL(request.application,'emision','iniciar'), []), \
(T('Asíncrona'), False, URL(request.application,'ialt','index'), []), \
    ]),
    (T('Consultas'), False, False, \
     [ \
         (T('Comprobantes'), False, URL(request.application,'consultas', 'consulta', vars={"table": "comprobante"})), \
         (T('Detalles'), False, URL(request.application,'consultas', 'consulta', vars={"table": "detalle"})), \
         (T('Clientes'), False, URL(request.application,'consultas', 'consulta', vars={"table": "cliente"})), \
         (T('Productos'), False, URL(request.application,'consultas', 'consulta', vars={"table": "producto"})), \
         (T('Listar comprobantes.'), False, URL(request.application,'consultas', 'lista_comprobantes', vars={"nueva": "true"})), \
         (T('Listar detalles'), False, URL(request.application,'consultas', 'lista_detalles'))]), \
    (T('Duplicados'), False, URL(a = request.application, c="duplicados", f="index"), \
     []), \
    (T('Servicios Web'), False, None , [
        (T('Estado (dummy)'), False, "", [
            (T('WSFEv0'), False, URL(request.application,'servicios_web','dummy',args="wsfe"), []),
            (T('WSFEv1'), False, URL(request.application,'servicios_web','dummy',args="wsfev1"), []),
            (T('WSMTXCA'), False, URL(request.application,'servicios_web','dummy',args="wsmtxca"), []),
            (T('WSFEX'), False, URL(request.application,'servicios_web','dummy',args="wsfex"), []),
            (T('WSBFE'), False, URL(request.application,'servicios_web','dummy',args="wsbfe"), []),
        ]),
        (T('Últ.Nro.Cbte.'), False, URL(request.application,'servicios_web','ultimo_numero_comprobante'), []),
        (T('Últ.ID'), False, URL(request.application,'servicios_web','ultimo_id'), []),
        (T('Cotización'), False, URL(request.application,'servicios_web','cotizacion'), []),
    ]),
    (T('Configurar'), False, URL(request.application,'setup','index'), []),
    (T('Ayuda'), False, None , [
        (T('Inicio'), False, URL(r = request, c="ayuda", f="inicio"), []),
        (T('Configuración'), False, URL(r = request, c="ayuda", f="configuracion"), []),        
        (T('Emisión'), False, URL(r = request, c="ayuda", f="emision"), []),                
        (T('FacturaLibre'), False, "http://www.sistemasagiles.com.ar/trac/wiki/FacturaLibre", []),    
        (T('Información General'), False, "http://www.sistemasagiles.com.ar/trac/wiki/FacturaElectronica", []),
        (T('Información Técnica'), False, "http://www.sistemasagiles.com.ar/trac/wiki/ManualPyAfipWs", [
            (T('WSFEv0'), False, "http://www.sistemasagiles.com.ar/trac/wiki/PyAfipWs", []),
            (T('WSFEv1'), False, "http://www.sistemasagiles.com.ar/trac/wiki/ProyectoWSFEv1", []),
            (T('WSMTXCA'), False, "http://www.sistemasagiles.com.ar/trac/wiki/FacturaElectronicaMTXCAService", []),
            (T('WSFEX'), False, "http://www.sistemasagiles.com.ar/trac/wiki/FacturaElectronicaExportacion", []),
            (T('WSBFE'), False, "http://www.sistemasagiles.com.ar/trac/wiki/FacturaElectronicaExportacion", []),
        ]),    
    ]),
    ]

##########################################
## this is here to provide shortcuts
## during development. remove in production 
##
## mind that plugins may also affect menu
##########################################

"""
response.menu+=[
    (T('Edit'), False, URL('admin', 'default', 'design/%s' % request.application),
     [
            (T('Controller'), False, 
             URL('admin', 'default', 'edit/%s/controllers/%s.py' \
                     % (request.application,request.controller=='appadmin' and
                        'default' or request.controller))), 
            (T('View'), False, 
             URL('admin', 'default', 'edit/%s/views/%s' \
                     % (request.application,response.view))),
            (T('Layout'), False, 
             URL('admin', 'default', 'edit/%s/views/layout.html' \
                     % request.application)),
            (T('Stylesheet'), False, 
             URL('admin', 'default', 'edit/%s/static/base.css' \
                     % request.application)),
            (T('DB Model'), False, 
             URL('admin', 'default', 'edit/%s/models/db.py' \
                     % request.application)),
            (T('Menu Model'), False, 
             URL('admin', 'default', 'edit/%s/models/menu.py' \
                     % request.application)),
            (T('Database'), False, 
             URL(request.application, 'appadmin', 'index')),
            ]
   ),
  ]
"""
