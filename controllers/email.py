# -*- coding: utf-8 -*-
# módulo para envío de correos
import os

COMPROBANTES_PATH = os.path.join(request.env.web2py_path,'applications',request.application,'private', 'comprobantes')

def enviar_comprobante():
    comprobante = db.comprobante[int(request.args[0])]
    
    if not comprobante: raise HTTP("Comprobante inexistente")
    
    variables = db(db.variables).select().first()
    
    # variables de mensaje
    empresa = str(variables.empresa)
    punto_vta = str(comprobante.punto_vta)
    cliente = str(comprobante.nombre_cliente)
    tipo_cbte = str(comprobante.tipo_cbte.desc)
    cbte_nro = str(comprobante.cbte_nro)
    fecha_vto = str(comprobante.fecha_venc_pago)
    fecha_cbte = str(comprobante.fecha_cbte)
    url_descarga = variables.url + "/salida/comprobante.pdf/" +  str(comprobante.id)

    mensaje = None
    attachment = None
    
    texto = variables.aviso_de_cbte_texto.replace("{{=empresa}}", empresa).replace("{{=cliente}}", cliente).replace("{{=tipo_cbte}}", tipo_cbte).replace("{{=cbte_nro}}", cbte_nro).replace("{{=fecha_cbte}}", fecha_cbte).replace("{{=fecha_vto}}", fecha_vto ).replace("{{=punto_vta}}", punto_vta).replace("{{=url_descarga}}", url_descarga)
    asunto = variables.aviso_de_cbte_asunto.replace("{{=empresa}}", empresa).replace("{{=cliente}}", cliente).replace("{{=tipo_cbte}}", tipo_cbte).replace("{{=cbte_nro}}", cbte_nro).replace("{{=fecha_cbte}}", fecha_cbte).replace("{{=fecha_vto}}", fecha_vto ).replace("{{=punto_vta}}", punto_vta)
    
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
