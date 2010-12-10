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
    
    (T('Emisión'), False, URL(request.application,'emision','iniciar'), []),
    (T('Consultas'), False, URL(request.application,'consultas','index'), []),    

    (T('Ayuda'), False, None , [
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
