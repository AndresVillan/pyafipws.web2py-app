# coding: utf8

response.title = "Servicios Web AFIP"

import os, os.path, time, datetime

# Constantes para homologación:

PRIVATE_PATH = os.path.join(request.env.web2py_path,'applications',request.application,'private')
WSDL = {
    'wsfe': "http://wswhomo.afip.gov.ar/wsfe/service.asmx?WSDL",
    'wsfev1': "http://wswhomo.afip.gov.ar/wsfev1/service.asmx?WSDL",
    'wsfex': "http://wswhomo.afip.gov.ar/wsfex/service.asmx?WSDL",
    'wsbfe': "http://wswhomo.afip.gov.ar/wsbfe/service.asmx?WSDL",
    'wsmtxca': "https://fwshomo.afip.gov.ar/wsmtxca/services/MTXCAService?wsdl",
    }

WSAA_URL = "https://wsaahomo.afip.gov.ar/ws/services/LoginCms"

# Configuración (mover al modelo):

CUIT = 20267565393
CERTIFICATE = 'reingart.crt'
PRIVATE_KEY = 'reingart.key'


def ymd2date(vto):
    "Convertir formato AFIP 20101231 a python date(2010,12,31)"
    return datetime.date(int(vto[0:4]), int(vto[4:6]), int(vto[6:8]))


def _autenticar(service="wsfe", ttl=60*60*5):
    "Obtener el TA"

    # wsfev1 => wsfe!
    service = {'wsfev1': 'wsfe'}.get(service, service)
    
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
        
    result = {}
    actualizar = {}
    
    try:
        
        if SERVICE=='wsfe':
            result = client.FEAutRequest(
                argAuth={'Token': TOKEN, 'Sign': SIGN, 'cuit': CUIT},
                Fer={
                    'Fecr': {'id': long(comprobante_id)+10000, 'cantidadreg': 1, 
                             'presta_serv': comprobante.concepto==1 and '0' or '1'},
                    'Fedr': {'FEDetalleRequest': {
                        'tipo_doc': comprobante.tipo_doc,
                        'nro_doc':  comprobante.nro_doc.replace("-",""),
                        'tipo_cbte': comprobante.tipo_cbte,
                        'punto_vta': comprobante.punto_vta,
                        'cbt_desde': comprobante.cbte_nro,
                        'cbt_hasta': comprobante.cbte_nro,
                        'imp_total': comprobante.imp_total or 0.00,
                        'imp_tot_conc': comprobante.imp_tot_conc or 0.00,
                        'imp_neto': comprobante.imp_neto or 0.00,
                        'impto_liq': comprobante.impto_liq or 0.00,
                        'impto_liq_rni': 0.00,
                        'imp_op_ex': comprobante.imp_op_ex or 0.00,
                        'fecha_cbte': comprobante.fecha_cbte.strftime("%Y%m%d"),
                        'fecha_venc_pago': comprobante.fecha_venc_pago.strftime("%Y%m%d"),
                    }}
                }
            )['FEAutRequestResult']
            
            if 'resultado' in result['FecResp']:
                # actualizo el registro del comprobante con el resultado:
                actualizar = dict(
                    # Resultado: Aceptado o Rechazado
                    resultado=result['FecResp']['resultado'],
                    # Motivo general/del detalle:
                    motivo=result['FecResp']['motivo'],
                    reproceso=result['FecResp']['reproceso'],
                    cae=result['FedResp'][0]['FEDetalleResponse']['cae'],
                    fecha_vto=ymd2date(result['FedResp'][0]['FEDetalleResponse']['fecha_vto']),
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
