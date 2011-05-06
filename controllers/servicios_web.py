# -*- coding: utf-8 -*-

response.title = "Servicios Web AFIP"

import os, os.path, time, datetime

# Constantes para homologación:

PRIVATE_PATH = os.path.join(request.env.web2py_path,'applications',request.application,'private')

# Configuración
# recuperar registro de variables
variables = db(db.variables).select().first()
if not variables: raise Exception("No se configuró el registro variables")
CUIT = variables.cuit
CERTIFICATE = variables.certificate
PRIVATE_KEY = variables.private_key

if variables.produccion:
    WSDL, WSAA_URL = None, None
else:
    WSDL = {
    'wsfe': "http://wswhomo.afip.gov.ar/wsfe/service.asmx?WSDL",
    'wsfev1': "http://wswhomo.afip.gov.ar/wsfev1/service.asmx?WSDL",
    'wsfex': "http://wswhomo.afip.gov.ar/wsfex/service.asmx?WSDL",
    'wsbfe': "http://wswhomo.afip.gov.ar/wsbfe/service.asmx?WSDL",
    'wsmtxca': "https://fwshomo.afip.gov.ar/wsmtxca/services/MTXCAService?wsdl",
    }

    WSAA_URL = "https://wsaahomo.afip.gov.ar/ws/services/LoginCms"
    
def ymd2date(vto):
    "Convertir formato AFIP 20101231 a python date(2010,12,31)"
    return datetime.date(int(vto[0:4]), int(vto[4:6]), int(vto[6:8]))


def _autenticar(service="wsfe", ttl=60*60*5):
    "Obtener el TA"

    # wsfev1 => wsfe!
    # service = {'wsfev1': 'wsfe'}.get(service, service)
    service = variables.web_service
    
    if service not in ("wsfe","wsfev1","wsmtxca","wsfex","wsbfe"):
        raise HTTP(500,"Servicio %s incorrecto" % service)
    
    # verifico archivo temporal con el ticket de acceso
    TA = os.path.join(PRIVATE_PATH, "TA-%s.xml" % service)
    ttl = 60*60*5
    if not os.path.exists(TA) or os.path.getmtime(TA)+(ttl)<time.time():
        # solicito una nueva autenticación
        wsaa = local_import("pyafipws.wsaa")
        cert = os.path.join(PRIVATE_PATH, CERTIFICATE)
        privatekey = os.path.join(PRIVATE_PATH, PRIVATE_KEY)
        # creo un ticket de requerimiento de acceso
        tra = wsaa.create_tra(service=SERVICE,ttl=ttl)
        # firmo el ticket de requerimiento de acceso
        cms = wsaa.sign_tra(str(tra),str(cert),str(privatekey))
        # llamo al webservice para obtener el ticket de acceso
        ta_string = wsaa.call_wsaa(cms,WSAA_URL,trace=False)
        # guardo el ticket de acceso obtenido:
        open(TA,"w").write(ta_string)
    
    # procesar el ticket de acceso y extraer TOKEN y SIGN:
    from gluon.contrib.pysimplesoap.simplexml import SimpleXMLElement
    ta_string=open(TA).read()
    ta = SimpleXMLElement(ta_string)
    token = str(ta.credentials.token)
    sign = str(ta.credentials.sign)
    return token, sign

# Conexión al webservice:
from gluon.contrib.pysimplesoap.client import SoapClient, SoapFault

# detecto webservice en uso (desde URL o desde el formulario)
if request.args:
    SERVICE = request.args[0]
elif request.vars:
    SERVICE = request.vars.get('webservice')
else: 
    SERVICE = ""
    TOKEN = SIGN = ''
    client = None
    
if SERVICE:        
    # solicito autenticación
    if request.controller!="dummy":
        TOKEN, SIGN = _autenticar(SERVICE)        
        
    # conecto al webservice
    client = SoapClient( 
            wsdl = WSDL[SERVICE],
            cache = PRIVATE_PATH,
            trace = False)

# Funciones expuestas al usuario:

def autenticar():
    "Prueba de autenticación"
    response.subtitle = "Prueba de autenticación (%s)" % SERVICE
    token, sign = _autenticar(SERVICE or 'wsfe')
    return dict(token=TOKEN[:10]+"...", sign=SIGN[:10]+"...")


def dummy():
    "Obtener el estado de los servidores de la AFIP"
    response.subtitle = "DUMMY: Consulta estado de servidores (%s)" % SERVICE
    if SERVICE=='wsfe':
        result = client.FEDummy()['FEDummyResult']
    elif SERVICE=='wsfev1':
        result = client.FEDummy()['FEDummyResult']
    elif SERVICE=='wsbfe':
        result = client.BFEDummy()['BFEDummyResult']
    elif SERVICE=='wsfex':
        result = client.FEXDummy()['FEXDummyResult']
    elif SERVICE=='wsmtxca':
        result = client.dummy()
    else:
        result = {}
    return result


def ultimo_id():
    "Obtener el último ID de transacción AFIP"
    response.subtitle = "Consulta el último ID de transacción utilizado"
    
    form = SQLFORM.factory(
        Field('webservice', type='string', length=6, default='wsfe',
            requires = IS_IN_SET(WEBSERVICES)),
    )
    
    result = {}
    
    if form.accepts(request.vars, session, keepvalues=True):                
        if SERVICE=='wsfe':
            result = client.FEUltNroRequest(
                argAuth = {'Token': TOKEN, 'Sign' : SIGN, 'cuit' : CUIT},
                )['FEUltNroRequestResult']
        elif SERVICE=='wsfex':
            result = client.FEXGetLast_ID(
                Auth={'Token': TOKEN, 'Sign': SIGN, 'Cuit': CUIT,}
                )['FEXGetLast_IDResult']
        elif SERVICE=='wsbfe':
            result = client.BFEGetLast_ID(
                Auth={'Token': TOKEN, 'Sign': SIGN, 'Cuit': CUIT,}
                )['BFEGetLast_IDResult']
        else:
            pass
            
    return {'form': form, 'result': result}


# devuelve unicamente id
def f_ultimo_id(comprobante):
    "Obtener el último ID de transacción AFIP (sin formulario)"
    
    result = {}
    
    if SERVICE=='wsfe':
        result = client.FEUltNroRequest(
            argAuth = {'Token': TOKEN, 'Sign' : SIGN, 'cuit' : CUIT},
            )['FEUltNroRequestResult']
    elif SERVICE=='wsfex':
        result = client.FEXGetLast_ID(
            Auth={'Token': TOKEN, 'Sign': SIGN, 'Cuit': CUIT,}
            )['FEXGetLast_IDResult']
    elif SERVICE=='wsbfe':
        result = client.BFEGetLast_ID(
            Auth={'Token': TOKEN, 'Sign': SIGN, 'Cuit': CUIT,}
            )['BFEGetLast_IDResult']
    else:
        pass
            
    return result



def ultimo_numero_comprobante():
    "Obtener el último comprobante autorizado por la AFIP"
    response.subtitle = "Consulta el último número de comprobante autorizado"
    
    form = SQLFORM.factory(
        Field('webservice', type='string', length=6, default='wsfe',
            requires = IS_IN_SET(WEBSERVICES)),
        Field('tipo_cbte', type='integer', 
                requires=IS_IN_DB(db,db.tipo_cbte.cod,"%(desc)s")),
        Field('punto_vta', type='integer', default=1,
                requires=IS_NOT_EMPTY()),
    )
    
    result = {}
    
    if form.accepts(request.vars, session, keepvalues=True):                
        if SERVICE=='wsfe':
            result = client.FERecuperaLastCMPRequest(
                argAuth = {'Token': TOKEN, 'Sign' : SIGN, 'cuit' : CUIT},
                argTCMP={'PtoVta' : form.vars.punto_vta, 'TipoCbte' : form.vars.tipo_cbte}
                )['FERecuperaLastCMPRequestResult']
        elif SERVICE=='wsfev1':
            result = client.FECompUltimoAutorizado(
                Auth={'Token': TOKEN, 'Sign': SIGN, 'Cuit': CUIT},
                PtoVta=form.vars.punto_vta,
                CbteTipo=form.vars.tipo_cbte,
                )['FECompUltimoAutorizadoResult']
        elif SERVICE=='wsfex':
            result = client.FEXGetLast_CMP(
                Auth={'Token': TOKEN, 'Sign': SIGN, 'Cuit': CUIT,
                    "Tipo_cbte": form.vars.punto_vta,
                    "Pto_venta": form.vars.tipo_cbte,}
                )['FEXGetLast_CMPResult']
        elif SERVICE=='wsbfe':
            pass
        elif SERVICE=='wsmtxca':
            pass
        else:
            pass
            
    return {'form': form, 'result': result}


# devuelve último cbte
def f_ultimo_numero_comprobante(comprobante):
    "Obtener el último comprobante autorizado por la AFIP (sin formulario)"
    
    result = {}
    if True:    
        if SERVICE=='wsfe':
            result = client.FERecuperaLastCMPRequest(
                argAuth = {'Token': TOKEN, 'Sign' : SIGN, 'cuit' : CUIT},
                argTCMP={'PtoVta' : comprobante.punto_vta, 'TipoCbte' : comprobante.tipo_cbte}
                )['FERecuperaLastCMPRequestResult']
        elif SERVICE=='wsfev1':
            result = client.FECompUltimoAutorizado(
                Auth={'Token': TOKEN, 'Sign': SIGN, 'Cuit': CUIT},
                PtoVta=comprobante.punto_vta,
                CbteTipo=comprobante.tipo_cbte,
                )['FECompUltimoAutorizadoResult']
        elif SERVICE=='wsfex':
            result = client.FEXGetLast_CMP(
                Auth={'Token': TOKEN, 'Sign': SIGN, 'Cuit': CUIT,
                    "Tipo_cbte": comprobante.punto_vta,
                    "Pto_venta": comprobante.tipo_cbte,}
                )['FEXGetLast_CMPResult']
        elif SERVICE=='wsbfe':
            pass
        elif SERVICE=='wsmtxca':
            pass
        else:
            pass
            
    return result


def cotizacion():
    "Obtener cotización de referencia según AFIP"
    response.subtitle = "Consulta cotización de referencia"
    
    form = SQLFORM.factory(
        Field('webservice', type='string', length=6, default='wsfex',
            requires = IS_IN_SET(WEBSERVICES)),
        Field('moneda_id', type='integer', default="DOL",
            requires=IS_IN_DB(db,db.moneda.cod,"%(desc)s")),
    )
    
    result = {}
    
    if form.accepts(request.vars, session, keepvalues=True):                
        if SERVICE=='wsfex':
            result = client.FEXGetPARAM_Ctz(
                Auth={'Token': TOKEN, 'Sign': SIGN, 'Cuit': CUIT},
                      Mon_id= form.vars.moneda_id,
                )['FEXGetPARAM_CtzResult']
        elif SERVICE=='wsfev1':
            result = client.FEParamGetCotizacion(
                Auth={'Token': TOKEN, 'Sign': SIGN, 'Cuit': CUIT},
                MonId=form.vars.moneda_id,
                )['FEParamGetCotizacionResult']    
        else:
            pass
            
    return {'form': form, 'result': result}


def autorizar():
    "Facturador (Solicitud de Autorización de Factura Electrónica AFIP)"
    response.subtitle = "Solicitud de Autorización - CAE  (%s)" % SERVICE
    
    comprobante_id = request.args[1]
    comprobante = db(db.comprobante.id==comprobante_id).select().first()
    detalles = db(db.detalle.comprobante_id==comprobante_id).select()

    # cálculo de cbte para autorización
    calcular_comprobante(comprobante)
        
    result = {}
    actualizar = {}

    # si el cbte no tiene id_ws o nro => consultar último/s
    if not comprobante.id_ws:
        comprobante.id_ws = int(f_ultimo_id(comprobante)['nro']['value']) +1

    if not comprobante.cbte_nro:
        comprobante.cbte_nro = int(f_ultimo_numero_comprobante(comprobante)['cbte_nro']) +1

    try:
        
        if SERVICE=='wsfe':
            
            result = client.FEAutRequest(
                argAuth={'Token': TOKEN, 'Sign': SIGN, 'cuit': CUIT},
                Fer={
                    'Fecr': {'id': long(comprobante.id_ws)+10000, 'cantidadreg': 1, 
                             'presta_serv': comprobante.concepto==1 and '0' or '1'},
                    'Fedr': {'FEDetalleRequest': {
                        'tipo_doc': comprobante.tipo_doc,
                        'nro_doc':  comprobante.nro_doc.replace("-",""),
                        'tipo_cbte': comprobante.tipo_cbte,
                        'punto_vta': comprobante.punto_vta,
                        'cbt_desde': comprobante.cbte_nro,
                        'cbt_hasta': comprobante.cbte_nro,
                        'imp_total': comprobante.imp_total,
                        'imp_tot_conc': comprobante.imp_tot_conc or 0.00,
                        'imp_neto': comprobante.imp_neto,
                        'impto_liq': comprobante.impto_liq,
                        'impto_liq_rni': 0.00,
                        'imp_op_ex': comprobante.imp_op_ex or 0.00,
                        'fecha_cbte': comprobante.fecha_cbte.strftime("%Y%m%d"),
                        'fecha_venc_pago': comprobante.fecha_venc_pago and comprobante.fecha_venc_pago.strftime("%Y%m%d"),
                    }}
                }
            )['FEAutRequestResult']
            
            if 'resultado' in result.get('FecResp',{}):
            
                # actualizo el registro del comprobante con el resultado:
                # intento recuperar fecha de vto.
                
                # para operación aprobada reset de id (local)
                if result['FecResp']['resultado'] == "A":
                    session.comprobante_id = None
                    
                try:
                    la_fecha_vto = ymd2date(result['FedResp'][0]['FEDetalleResponse']['fecha_vto'])
                except ValueError:
                    la_fecha_vto = None    
                actualizar = dict(
                    # Resultado: Aceptado o Rechazado
                    resultado=result['FecResp']['resultado'],
                    # Motivo general/del detalle:
                    motivo=result['FecResp']['motivo'],
                    reproceso=result['FecResp']['reproceso'],
                    cae=result['FedResp'][0]['FEDetalleResponse']['cae'],
                    fecha_vto=la_fecha_vto,
                    cbte_nro=result['FedResp'][0]['FEDetalleResponse']['cbt_desde'],
                    id_ws=result['FecResp']['id'],
                    )
        

        elif SERVICE=='wsfev1':
            pass
        elif SERVICE=='wsfex':
            pass
        elif SERVICE=='wsbfe':
            pass
        elif SERVICE=='wsmtxca':
            pass
        else:
            pass

    except SoapFault,sf:
        return {'fault': sf.faultstring, 
                'xml_request': client.xml_request, 
                'xml_response': client.xml_response,
                } 
    
    # actualizo el registro del comprobante con el resultado:
    if actualizar:
        db(db.comprobante.id==comprobante_id).update(**actualizar)

    return result


def calcular_comprobante(comprobante):
    """ Cálculo del cbte usando una sección
    de código de Marcelo como ejemplo para el
    bucle de consulta a la base de datos"""

    detalles = db(db.detalle.comprobante_id==comprobante.id).select()
    tipo_cbte = db(db.tipo_cbte.id==comprobante.tipo_cbte).select().first()
    
    for p in range(len(detalles)):
        iva = db(db.iva.id==detalles[p].iva_id).select().first()
        if tipo_cbte.discriminar:
            detalles[p].imp_iva = detalles[p].qty * detalles[p].precio * iva.aliquota
            detalles[p].imp_neto = detalles[p].qty * detalles[p].precio
            detalles[p].imp_total = detalles[p].imp_neto + detalles[p].imp_iva

        else:
            detalles[p].imp_iva = 0
            detalles[p].imp_neto = detalles[p].qty * detalles[p].precio
            detalles[p].imp_total = detalles[p].imp_neto
        
    liq = sum([detalle.imp_iva for detalle in detalles], 0.00)
    neto = sum([detalle.imp_neto for detalle in detalles], 0.00)
    total = sum([detalle.imp_total for detalle in detalles], 0.00)
    
    comprobante.imp_total = total
    comprobante.imp_neto = neto
    comprobante.impto_liq = liq

    return True
