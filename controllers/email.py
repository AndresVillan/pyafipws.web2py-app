# -*- coding: utf-8 -*-
# módulo para envío de correos
import os

COMPROBANTES_PATH = os.path.join(request.env.web2py_path,'applications',request.application,'private', 'comprobantes')

@auth.requires(auth.has_membership('administrador') or auth.has_membership('emisor'))
def enviar_comprobante():
    comprobante = db.comprobante[int(request.args[0])]
    
    if not comprobante: raise HTTP("Comprobante inexistente")


    try:
        variables = db(db.variables).select().first()

        # variables de mensaje
        empresa = str(variables.empresa)
        punto_vta = str(comprobante.punto_vta)
        cliente = str(comprobante.nombre_cliente)
        tipocbte = str(comprobante.tipocbte.ds)
        cbte_nro = str(comprobante.cbte_nro)
        fecha_vto = str(comprobante.fecha_venc_pago)
        fecha_cbte = str(comprobante.fecha_cbte)
        url_descarga = variables.url + "salida/invoice/comprobante/" + str(comprobante.id)
        mail.settings.server = variables.mail_server
        mail.settings.sender = variables.mail_sender
        mail.settings.login = variables.mail_login
        
    except (AttributeError, KeyError, ValueError, TypeError), e:
        raise HTTP(500, "No se configurararon las variables generales o de envío. %s" % str(e))

    mensaje = None
    attachment = None
    
    texto = variables.aviso_de_cbte_texto.replace("{{=empresa}}", empresa).replace("{{=cliente}}", cliente).replace("{{=tipocbte}}", tipocbte).replace("{{=cbte_nro}}", cbte_nro).replace("{{=fecha_cbte}}", fecha_cbte).replace("{{=fecha_vto}}", fecha_vto ).replace("{{=punto_vta}}", punto_vta).replace("{{=url_descarga}}", url_descarga)
    asunto = variables.aviso_de_cbte_asunto.replace("{{=empresa}}", empresa).replace("{{=cliente}}", cliente).replace("{{=tipocbte}}", tipocbte).replace("{{=cbte_nro}}", cbte_nro).replace("{{=fecha_cbte}}", fecha_cbte).replace("{{=fecha_vto}}", fecha_vto ).replace("{{=punto_vta}}", punto_vta)
    
    nombre_cbte = "%s.pdf" % str(comprobante.id)
    # si se creó el cbte en el sistema adjuntarlo
    if  nombre_cbte in os.listdir(COMPROBANTES_PATH):
        attachment = os.path.join(COMPROBANTES_PATH, nombre_cbte)    
        mail.send(str(comprobante.email), asunto, texto, \
        attachments = Mail.Attachment(attachment))

    else:
        mail.send(str(comprobante.email), asunto, texto)        

    mensaje = "Se envió el comprobante a: " + str(comprobante.email)
    
    return dict(mensaje = mensaje, asunto = asunto, texto = texto)
