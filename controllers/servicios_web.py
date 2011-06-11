# -*- coding: utf-8 -*-

def utftolatin(text):
    return unicode(text, "utf-8").encode("latin-1")

response.title = "Servicios Web AFIP"

from xml.parsers.expat import ExpatError
from urllib2 import HTTPError

import os, os.path, time, datetime

# Conexión al webservice:
try:
    from pysimplesoap.client import SoapClient, SoapFault
    from pyafipws import wsaa
except ImportError:
    raise Exception("Por favor instale las librerías pysimplesoap y pyafipws en la carpeta site-packages.")

# Constantes para homologación:

PRIVATE_PATH = os.path.join(request.env.web2py_path,'applications',request.application,'private')

# Configuración
# recuperar registro de variables
variables = db(db.variables).select().first()
if not variables: raise HTTP(500, "No se configuró el registro variables")
variablesusuario = db(db.variablesusuario.usuario == auth.user_id).select().first()
if not variablesusuario: raise HTTP(500,"No se configuró el registro variables de usuario")

CUIT = variables.cuit

# almacenar los certificados en la carpeta private
CERTIFICATE = variables.certificate
PRIVATE_KEY = variables.private_key


def detalles_bono_fiscal(comprobante):
    items = []
    for det in db(db.detalle.comprobante == comprobante.id).select():
        items.append(
            {
            "Pro_codigo_ncm": det.ncm or 0,
            "Pro_codigo_sec": det.sec or 0,
            "Pro_ds": det.ds,
            "Pro_qty": det.qty,
            "Pro_umed": det.umed.cod,
            "Pro_precio_uni": "%.2f" %  det.precio,
            "Imp_bonif": "%.2f" % det.bonif,
            "Imp_total": "%.2f" % det.imp_total,
            "Iva_id": det.iva.cod,
            }            
        )  
    return items


def calcular_comprobante(comprobante):
    """ Cálculo del cbte usando una sección
    de código de Marcelo como ejemplo para el
    bucle de consulta a la base de datos"""

    detalles = db(db.detalle.comprobante==comprobante.id).select()
    tipocbte = db(db.tipocbte.id==comprobante.tipocbte).select().first()
    
    for p in range(len(detalles)):
        iva = db(db.iva.id==detalles[p].iva).select().first()

        try:
            detalles[p].imp_neto = (detalles[p].qty * detalles[p].precio) -detalles[p].bonif
        except TypeError:
            detalles[p].imp_neto
            
        try:
            detalles[p].imp_iva = detalles[p].imp_neto * iva.aliquota
        except TypeError:
            detalles[p].imp_iva = 0.00            
        detalles[p].imp_total = detalles[p].imp_neto + detalles[p].imp_iva

    neto = sum([detalle.imp_neto for detalle in detalles], 0.00)         
    
    if not int(comprobante.tipocbte.cod) in [11, 12, 13, 15]:
        liq = sum([detalle.imp_iva for detalle in detalles], 0.00)
        total = sum([detalle.imp_total for detalle in detalles], 0.00)
        
    else:
        liq = 0.0
        total = neto

    
    comprobante.imp_total = total
    comprobante.imp_neto = neto
    comprobante.impto_liq = liq

    return True


def comprobante_sumar_iva(comprobante):
    """ calcula los totales de iva por item de un cbte. Devuelve un arreglo bidimensional (dict/list) con valores por alícuota. """
    alicuotas = set()
    sumas = []
    
    detalles = db(db.detalle.comprobante == comprobante).select()
    for detalle in detalles:
        alicuotas.add(detalle.iva.id)
    for alicuota in alicuotas:
        id = ""
        base_imp = 0
        importe = 0
        
        for detalle in detalles:
            if detalle.iva == alicuota:
                try:
                    # sumar iva
                    if not id: id = str(detalle.iva.cod)
                    base_imp += detalle.base_imp_iva
                    importe += detalle.imp_iva
                except TypeError:
                    """ TODO: manejo de errores en cómputo de ítem. """
                    pass

        if importe > 0:
            sumas.append(dict(id = id, base_imp = base_imp, importe = importe))

    return sumas

# detecto webservice en uso (desde URL o desde el formulario)
if request.args:
    SERVICE = request.args[0]

elif request.vars:
    SERVICE = request.vars.get('webservice')

else:
    SERVICE = ""
    TOKEN = SIGN = ''
    client = None


if variables.produccion:
    WSDL = {
    'wsfe': None,
    'wsfev1': "https://servicios1.afip.gov.ar/wsfev1/service.asmx?WSDL",
    'wsfex': "https://servicios1.afip.gov.ar/wsfex/service.asmx", # ?WSDL
    'wsbfe': "https://servicios1.afip.gov.ar/wsbfe/service.asmx", # ?WSDL
    'wsmtxca': "https://serviciosjava.afip.gob.ar/wsmtxca/services/MTXCAService?wsdl",
     }
    WSAA_URL = "https://wsaa.afip.gov.ar/ws/services/LoginCms"
    
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

def date2y_m_d(fch):
    #Convertir de date a AAAA-MM-DD
    try:
        fchtmp = fch.strftime("%Y%m%d")
        return fchtmp[:4] + "-" + fchtmp[4:6] + "-" + fchtmp[6:]
    except AttributeError:
        return None

def y_m_d2date(fch):
    # convertir formato AFIP AAAA-MM-DD a date
    try:
        return ymd2date(fch.replace("-", ""))
    except AttributeError:
        return None

def _autenticar(service="wsfe", ttl=60*60*5):
    "Obtener el TA"

    # wsfev1 => wsfe!
    # service = {'wsfev1': 'wsfe'}.get(service, service)
    
    if service not in ("wsfe","wsfev1","wsmtxca","wsfex","wsbfe"):
        raise HTTP(500,"Servicio %s incorrecto" % service)
    
    # verifico archivo temporal con el ticket de acceso
    TA = os.path.join(PRIVATE_PATH, "TA-%s.xml" % service)
    ttl = 60*60*5
    if not os.path.exists(TA) or os.path.getmtime(TA)+(ttl)<time.time():
        # solicito una nueva autenticación
        # wsaa = pyafipws.wsaa
        cert = os.path.join(PRIVATE_PATH, CERTIFICATE)
        privatekey = os.path.join(PRIVATE_PATH, PRIVATE_KEY)
        # creo un ticket de requerimiento de acceso
        # cambiando a wsfe si es wsfe(v_)
        if "wsfev" in service: service = "wsfe"
        tra = wsaa.create_tra(service=service,ttl=ttl)

        # firmo el ticket de requerimiento de acceso
        cms = wsaa.sign_tra(str(tra),str(cert),str(privatekey))


        # llamo al webservice para obtener el ticket de acceso
        ta_string = wsaa.call_wsaa(cms,WSAA_URL,trace=False)
        # guardo el ticket de acceso obtenido:
        open(TA,"w").write(ta_string)


    # procesar el ticket de acceso y extraer TOKEN y SIGN:
    # from gluon.contrib.pysimplesoap.simplexml import SimpleXMLElement
    
    # agregar librería modificada para aceptar etiquetas vacías
    from pysimplesoap.simplexml import SimpleXMLElement
        
    ta_string=open(TA).read()
    ta = SimpleXMLElement(ta_string)
    token = str(ta.credentials.token)
    sign = str(ta.credentials.sign)
    return token, sign

# Funciones expuestas al usuario:

@auth.requires(auth.has_membership('administrador') or auth.has_membership('emisor'))
def autenticar():
    "Prueba de autenticación"
    response.subtitle = "Prueba de autenticación (%s)" % SERVICE
    token, sign = _autenticar(SERVICE or 'wsfe')
    return dict(token=TOKEN[:10]+"...", sign=SIGN[:10]+"...")


@auth.requires(auth.has_membership('administrador') or auth.has_membership('emisor') or auth.has_membership('invitado'))
def dummy():
    "Obtener el estado de los servidores de la AFIP"
    response.subtitle = "DUMMY: Consulta estado de servidores (%s)" % SERVICE
    try:
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


    except SoapFault,sf:
        db.xml.insert(request = repr(client.xml_request), response = repr(client.xml_response))
        result = {'fault': repr(sf.faultstring), 
            'xml_request': repr(client.xml_request), 
            'xml_response': repr(client.xml_response),
            }
    except ExpatError, ee:
        result = {"resultado" :"Error en el Cliente SOAP. Formato de respuesta inválido."}
      
    return result


@auth.requires(auth.has_membership('administrador') or auth.has_membership('emisor') or auth.has_membership('invitado'))
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
        elif SERVICE=='wsmtxca':
            pass
        else:
            pass
            
    return {'form': form, 'result': result}



def f_ultimo_id(comprobante):
    "Obtener el último ID de transacción AFIP (sin formulario)"
    
    result = {}
    valor = None
    if SERVICE=='wsfe':
        result = client.FEUltNroRequest(
            argAuth = {'Token': TOKEN, 'Sign' : SIGN, 'cuit' : CUIT},
            )['FEUltNroRequestResult']
        valor = result['nro']['value']
        
    elif SERVICE=='wsfex':
        result = client.FEXGetLast_ID(
            Auth={'Token': TOKEN, 'Sign': SIGN, 'Cuit': CUIT,}
            )['FEXGetLast_IDResult']
        valor = result["FEXResultGet"]["Id"]
            
    elif SERVICE=='wsbfe':
        result = client.BFEGetLast_ID(
            Auth={'Token': TOKEN, 'Sign': SIGN, 'Cuit': CUIT,}
            )['BFEGetLast_IDResult']
        valor = result["BFEResultGet"]["Id"]

    elif SERVICE=='wsfev1':
        # último id wsfev1
        result, valor = None, None

    else:
        pass
        

    return (result, valor)


@auth.requires(auth.has_membership('administrador') or auth.has_membership('emisor') or auth.has_membership('invitado'))
def ultimo_numero_comprobante():
    "Obtener el último comprobante autorizado por la AFIP"
    response.subtitle = "Consulta el último número de comprobante autorizado"
    
    form = SQLFORM.factory(
        Field('webservice', type='string', length=6, default='wsfe',
            requires = IS_IN_SET(WEBSERVICES)),
        Field('tipocbte', type='integer',
                requires=IS_IN_DB(db,db.tipocbte.cod,"%(ds)s")),
        Field('punto_vta', type='integer', default=1,
                requires=IS_NOT_EMPTY()),
    )
    
    result = {}
    
    if form.accepts(request.vars, session, keepvalues=True):
      
        try:
            if SERVICE=='wsfe':
                result = client.FERecuperaLastCMPRequest(
                argAuth = {'Token': TOKEN, 'Sign' : SIGN, 'cuit' : CUIT},
                argTCMP={'PtoVta' : form.vars.punto_vta, 'TipoCbte' : form.vars.tipocbte}
                )['FERecuperaLastCMPRequestResult']
            elif SERVICE=='wsfev1':
                result = client.FECompUltimoAutorizado(
                Auth={'Token': TOKEN, 'Sign': SIGN, 'Cuit': CUIT},
                PtoVta=form.vars.punto_vta,
                CbteTipo=form.vars.tipocbte,
                )['FECompUltimoAutorizadoResult']
            elif SERVICE=='wsfex':
                result = client.FEXGetLast_CMP(
                Auth={'Token': TOKEN, 'Sign': SIGN, 'Cuit': CUIT,
                    "Tipo_cbte": form.vars.tipocbte,
                    "Pto_venta": form.vars.punto_vta,}
                )['FEXGetLast_CMPResult']
            elif SERVICE=='wsbfe':
                result = client.BFEGetLast_CMP(
            Auth={"Token": TOKEN, "Sign": SIGN, "Cuit": CUIT,
                  "Tipo_cbte": form.vars.tipocbte,
                  "Pto_venta": form.vars.punto_vta}) 

            elif SERVICE=='wsmtxca':
            # inicializar_y_capturar_execepciones
                result = client.consultarUltimoComprobanteAutorizado(\
                authRequest = {"token": TOKEN, "sign": SIGN, "cuitRepresentada": CUIT}, consultaUltimoComprobanteAutorizadoRequest = {\
                "codigoTipoComprobante" : form.vars.tipocbte, \
                "numeroPuntoVenta" : form.vars.punto_vta})
            # nro = ret.get('numeroComprobante')
            # return nro is not None and str(nro) or 0
          
            else:
                pass

        except SoapFault,sf:
            db.xml.insert(request = repr(client.xml_request), response = repr(client.xml_response))

            result = {'fault': repr(sf.faultstring), 
                'xml_request': repr(client.xml_request), 
                'xml_response': repr(client.xml_response),
                }

        except ExpatError, ee:
            result = "Error en el Cliente SOAP. Formato de respuesta inválido."


    return {'form': form, 'result': result}


# devuelve último cbte
def f_ultimo_numero_comprobante(comprobante):
    "Obtener el último comprobante autorizado por la AFIP (sin formulario)"
    
    valor = None
    result = {}
    try:
        if SERVICE=='wsfe':
            result = client.FERecuperaLastCMPRequest(
                argAuth = {'Token': TOKEN, 'Sign' : SIGN, 'cuit' : CUIT},
                argTCMP={'PtoVta' : comprobante.punto_vta, 'TipoCbte' : comprobante.tipocbte.cod}
                )['FERecuperaLastCMPRequestResult']
            valor = result["cbte_nro"]

        elif SERVICE=='wsfev1':
            result = client.FECompUltimoAutorizado(
                Auth={'Token': TOKEN, 'Sign': SIGN, 'Cuit': CUIT},
                PtoVta=comprobante.punto_vta,
                CbteTipo=comprobante.tipocbte.cod,
                )['FECompUltimoAutorizadoResult']
            valor = result["CbteNro"]            
                
        elif SERVICE=='wsfex':
            result = client.FEXGetLast_CMP(
                Auth={'Token': TOKEN, 'Sign': SIGN, 'Cuit': CUIT,
                    "Tipo_cbte": comprobante.tipocbte.cod,
                    "Pto_venta": comprobante.punto_vta,}
                )['FEXGetLast_CMPResult']
            valor = result["FEXResult_LastCMP"]["Cbte_nro"]

        elif SERVICE=='wsbfe':
            result = client.BFEGetLast_CMP(
            Auth={"Token": TOKEN, "Sign": SIGN, "Cuit": CUIT,
                  "Tipo_cbte": comprobante.tipocbte.cod,
                  "Pto_venta": comprobante.punto_vta})
            valor = result['BFEGetLast_CMPResult']['BFEResult_LastCMP']['Cbte_nro']
                
        elif SERVICE=='wsmtxca':
            # inicializar_y_capturar_execepciones
            result = client.consultarUltimoComprobanteAutorizado(\
                authRequest = {"token": TOKEN, "sign": SIGN, "cuitRepresentada": CUIT}, consultaUltimoComprobanteAutorizadoRequest = {\
                "codigoTipoComprobante" : comprobante.tipocbte.cod, \
                "numeroPuntoVenta" : comprobante.punto_vta})

            try:
                if result["arrayErrores"]:
                    for error in result["arrayErrores"]:
                        if str(error["codigoDescripcion"]["codigo"]) == "1502":
                        # no existen cbtes en la base de datos de AFIP
                            valor = 0
            except KeyError:
                valor = None
                
            if valor != 0: valor = result["numeroComprobante"]

        else:
            pass

    except SoapFault,sf:
        db.xml.insert(request = repr(client.xml_request), response = repr(client.xml_response))

    except ExpatError, ee:
        result = "Error en el Cliente SOAP. Formato de respuesta inválido."


    return (result, valor)

@auth.requires(auth.has_membership('administrador') or auth.has_membership('emisor') or auth.has_membership('invitado'))
def get_param_dstcuit():
    "Recuperador de valores referenciales de CUITs de Paises"
    response = client.FEXGetPARAM_DST_CUIT(
        Auth= {"Token": TOKEN, "Sign": SIGN, "Cuit": long(CUIT)}) 
    
    # if int(response["FEXGetPARAM_DST_CUITResult"]["FEXErr"]["ErrCode"]) != 0:
    # raise FEXError(response.FEXGetPARAM_DST_CUITResult.FEXErr)
    # pass


    return dict(resp = response, dic = repr(response))


def f_get_param_dstcuit(variables):
    "Recuperador de valores referenciales de CUITs de Paises"
    response = client.FEXGetPARAM_DST_CUIT(
        Auth= {"Token": TOKEN, "Sign": SIGN, "Cuit": long(CUIT)}) 

    return response

@auth.requires(auth.has_membership('administrador'))
def crear_cuit_paises():

    try:
        response = f_get_param_dstcuit(variables)
        # return dict(resp = response)
        # si se recuperaron los parámetros eliminar registros y completar la tabla
        if int(response["FEXGetPARAM_DST_CUITResult"]["FEXErr"]["ErrCode"]) == 0:
            db(db.dstcuit.id > 0).delete()
            db.dstcuit.insert(cod="", ds = "(Sin especificar)", cuit = "50000000000")
            for pais in response["FEXGetPARAM_DST_CUITResult"]["FEXResultGet"]:
                db.dstcuit.insert(ds = pais["ClsFEXResponse_DST_cuit"]["DST_Ds"], cuit = pais["ClsFEXResponse_DST_cuit"]["DST_CUIT"])

        else: raise HTTP(500, response["FEXErr"]["ErrMsg"])
    except (TypeError, ValueError, KeyError, AttributeError):
        raise HTTP(500, "Se produjo un error al consultar los registros de AFIP. Se deben configurar previamente las variables de autenticación (Credenciales y CUIT)")
    
    redirect(URL(r=request, c='setup', f='index'))


@auth.requires(auth.has_membership('administrador') or auth.has_membership('emisor'))
def get_param_tipo_expo():
    "Recuperador de valores referenciales de c�digos de Tipo de exportaci�n"
    response = client.FEXGetPARAM_Tipo_Expo(
        auth= {"Token": TOKEN, "Sign": SIGN, "Cuit": CUIT}) 
    
    if int(response["FEXGetPARAM_Tipo_ExpoResult"]["FEXErr"]["ErrCode"]) != 0:
        raise HTTP(500, "Error: " + str(response["FEXGetPARAM_Tipo_ExpoResult"]["FEXErr"]["ErrCode"]) + ". " + response["FEXGetPARAM_Tipo_ExpoResult"]["FEXErr"]["ErrMsg"])

    tipos = [] # tipos de exportaci�n
    for t in response["FEXGetPARAM_Tipo_ExpoResult"]["FEXResultGet"]["ClsFEXResponse_Tex"]:
        tipo = {'id': int(t["Tex_Id"]), 'ds': str(t["Tex_Ds"]).decode('utf8'), 
                'vig_desde': str(t["Tex_vig_desde"]), 
                'vig_hasta': str(t["Tex_vig_hasta"])}
        tipos.append(tipo)
    return dict(tipos = tipos)

@auth.requires(auth.has_membership('administrador') or auth.has_membership('emisor'))
def get_param_zonas():
    # client , TOKEN, SIGN, CUIT
    "Recuperador de valores referenciales de Zonas"
    response = client.BFEGetPARAM_Zonas(
        auth= {"Token": TOKEN, "Sign": SIGN, "Cuit": CUIT}) 
    
    # if int(response.BFEGetPARAM_ZonasResult.BFEErr.ErrCode) != 0:
    #   raise BFEError(response.BFEGetPARAM_ZonasResult.BFEErr)

    zonas = [] # unidades de medida
    """
    for z in response.BFEGetPARAM_ZonasResult.BFEResultGet.ClsBFEResponse_Zon:
        zon = {'id': int(z.Zon_Id), 'ds': unicode(z.Zon_Ds), 
                'vig_desde': str(z.Zon_vig_desde), 
                'vig_hasta': str(z.Zon_vig_hasta)}
        zonas.append(zon)
    """
    return dict(zonas = str(response))


# WSMTXCA
@auth.requires(auth.has_membership('administrador') or auth.has_membership('emisor'))
def consultar_monedas():
    "Este m�todo permite consultar los tipos de comprobantes habilitados en este WS"
    ret = client.consultarMonedas(
        authRequest={'token': TOKEN, 'sign': SIGN, 'cuitRepresentada': CUIT},
        )
    return dict(result = ["%(codigo)s: %(descripcion)s" % p['codigoDescripcion']
             for p in ret['arrayMonedas']])

# WSMTXCA
def consultar_unidades_medida():
    "Este m�todo permite consultar los tipos de comprobantes habilitados en este WS"
    ret = client.consultarUnidadesMedida(
        authRequest={'token': TOKEN, 'sign': SIGN, 'cuitRepresentada': CUIT},
        )
    return dict(result = ["%(codigo)s: %(descripcion)s" % p['codigoDescripcion']
             for p in ret['arrayUnidadesMedida']])



@auth.requires(auth.has_membership('administrador') or auth.has_membership('emisor') or auth.has_membership('auditor') or auth.has_membership('invitado'))
def cotizacion():
    "Obtener cotización de referencia según AFIP"
    response.subtitle = "Consulta cotización de referencia"
    
    form = SQLFORM.factory(
        Field('webservice', type='string', length=6, default='wsfex',
            requires = IS_IN_SET(WEBSERVICES)),
        Field('moneda_id', type='string', default="DOL",
            requires=IS_IN_DB(db,db.moneda.cod,"%(ds)s")),
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


@auth.requires(auth.has_membership('emisor') or auth.has_membership('administrador'))
def autorizar():
    "Facturador (Solicitud de Autorización de Factura Electrónica AFIP)"
    response.subtitle = "Solicitud de Autorización - CAE  (%s)" % SERVICE
    
    comprobante = request.args[1]
    comprobante = db(db.comprobante.id==comprobante).select().first()
    
    detalles = db(db.detalle.comprobante==comprobante).select()

       
    # cálculo de cbte para autorización
    calcular_comprobante(comprobante)
        
    result = {}
    actualizar = {}

    # si el cbte no tiene id_ws o nro => consultar último/s
    if not comprobante.id_ws:
        try:
            comprobante.id_ws = int(f_ultimo_id(comprobante)[1]) +1
        except (AttributeError, ValueError, KeyError, TypeError):
            comprobante.id_ws = None

    if not comprobante.cbte_nro:
        try:
            consulta_cbte = f_ultimo_numero_comprobante(comprobante) 
            cbte_nro = int(consulta_cbte[1])
            comprobante.cbte_nro = cbte_nro +1


        except (AttributeError, KeyError, ValueError, TypeError), e:
            comprobante.cbte_nro = None


    try:
        
        if SERVICE=='wsfe':
            
            result = client.FEAutRequest(
                argAuth={'Token': TOKEN, 'Sign': SIGN, 'cuit': CUIT},
                Fer={
                    'Fecr': {'id': long(comprobante.id_ws)+10000, 'cantidadreg': 1, 
                             'presta_serv': comprobante.concepto==1 and '0' or '1'},
                    'Fedr': {'FEDetalleRequest': {
                        'tipo_doc': comprobante.tipodoc.cod,
                        'nro_doc':  comprobante.nro_doc.replace("-",""),
                        'tipo_cbte': comprobante.tipocbte.cod,
                        'punto_vta': comprobante.punto_vta,
                        'cbt_desde': comprobante.cbte_nro,
                        'cbt_hasta': comprobante.cbte_nro,
                        'imp_total': "%.2f" % comprobante.imp_total,
                        'imp_tot_conc': comprobante.imp_tot_conc or 0.00,
                        'imp_neto': "%.2f" % comprobante.imp_neto,
                        'impto_liq': "%.2f" % comprobante.impto_liq,
                        'impto_liq_rni': 0.00,
                        'imp_op_ex': comprobante.imp_op_ex or 0.00,
                        'fecha_cbte': comprobante.fecha_cbte.strftime("%Y%m%d"),
                        'fecha_venc_pago': comprobante.fecha_venc_pago and comprobante.fecha_venc_pago.strftime("%Y%m%d"), \
                        'fecha_serv_desde': comprobante.fecha_serv_desde and comprobante.fecha_serv_desde.strftime("%Y%m%d"), \
                        'fecha_serv_hasta': comprobante.fecha_serv_hasta and comprobante.fecha_serv_hasta.strftime("%Y%m%d")
                    }}
                }
            )['FEAutRequestResult']
            
            if 'resultado' in result.get('FecResp',{}):
            
                # actualizo el registro del comprobante con el resultado:
                # intento recuperar fecha de vto.
                
                # para operación aprobada reset de id (local)
                if result['FecResp']['resultado'] == "A":
                    session.comprobante = None
                    
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
                    imp_neto=result['FedResp'][0]['FEDetalleResponse']['imp_neto'],
                    imp_total=result['FedResp'][0]['FEDetalleResponse']['imp_total'],
                    impto_liq=result['FedResp'][0]['FEDetalleResponse']['impto_liq'],
                    impto_liq_rni=result['FedResp'][0]['FEDetalleResponse']['impto_liq_rni'],
                    imp_op_ex=result['FedResp'][0]['FEDetalleResponse']['imp_op_ex'],
                    imp_tot_conc=result['FedResp'][0]['FEDetalleResponse']['imp_tot_conc'],
                    webservice = SERVICE
                    )
                elif result['FecResp']['resultado'] == "R":
                    session.comprobante = None
                    actualizar = dict(resultado = "R")
                    
        elif SERVICE=='wsfev1':
            # campos período de servicio: borrar si es tipo 1
            if comprobante.concepto == 1:
                comprobante.fecha_serv_desde = ""
                comprobante.fecha_serv_hasta = ""
                comprobante.fecha_venc_pago = ""      

            if int(comprobante.tipocbte.cod) in [11, 12, 13, 15]:
                items_iva = []
            else:
                items_iva =  [{'AlicIva': {
                            'Id': det["id"],
                            'BaseImp': "%.2f" % det["base_imp"],
                            'Importe': "%.2f" % det["importe"],
                            }}
                for det in comprobante_sumar_iva(comprobante)]

                
            result = client.FECAESolicitar(\
            Auth={'Token': TOKEN, 'Sign': SIGN, 'Cuit': CUIT},
            FeCAEReq={
                'FeCabReq': {'CantReg': 1, 
                    'PtoVta': comprobante.punto_vta, 
                    'CbteTipo': comprobante.tipocbte.cod},
                'FeDetReq': [{'FECAEDetRequest': {
                    'Concepto': comprobante.concepto,
                    'DocTipo': comprobante.tipodoc.cod,
                    'DocNro': comprobante.nro_doc.replace("-",""),
                    'CbteDesde': comprobante.cbte_nro,
                    'CbteHasta': comprobante.cbte_nro,
                    'CbteFch': comprobante.fecha_cbte.strftime("%Y%m%d"),
                    'ImpTotal': "%.2f" % comprobante.imp_total,
                    'ImpTotConc': comprobante.imp_tot_conc or 0.00,
                    'ImpNeto': "%.2f" % comprobante.imp_neto,
                    'ImpOpEx': comprobante.imp_op_ex or 0.00,
                    'ImpTrib': comprobante.imp_iibb or 0.00,
                    'ImpIVA': "%.2f" % comprobante.impto_liq,
                    # Fechas solo se informan si Concepto in (2,3)
                    'FchServDesde': comprobante.fecha_serv_desde and comprobante.fecha_serv_desde.strftime("%Y%m%d"),
                    'FchServHasta': comprobante.fecha_serv_hasta and comprobante.fecha_serv_hasta.strftime("%Y%m%d"),
                    'FchVtoPago': comprobante.fecha_venc_pago and comprobante.fecha_venc_pago.strftime("%Y%m%d"),
                    'MonId': comprobante.moneda_id.cod,
                    'MonCotiz': comprobante.moneda_ctz,                
                    'CbtesAsoc': [
                        {'CbteAsoc': {
                            'Tipo': cbte_asoc.asociado.tipocbte.cod,
                            'PtoVta': cbte_asoc.asociado.punto_vta, 
                            'Nro': cbte_asoc.asociado.cbte_nro}}
                        for cbte_asoc in db(db.comprobanteasociado.comprobante == comprobante).select()],
                    'Tributos': [
                        {'Tributo': {
                            'Id': tributo.tributo.id, 
                            'Desc': tributo.tributo.ds,
                            'BaseImp': None,
                            'Alic': tributo.tributo.aliquota,
                            'Importe': tributo.importe,
                            }}
                        for tributo in db(db.detalletributo.comprobante == comprobante).select()],
                    'Iva': items_iva,
                    }
                }]
            })['FECAESolicitarResult']

            if 'FeCabResp' in result:
                fecabresp = result['FeCabResp']
                fedetresp = result['FeDetResp'][0]['FECAEDetResponse']

                if fedetresp["Resultado"] == "A":
                    session.comprobante = None
                    # aprobado
                    obstmp = str()
                    for obs in fedetresp.get('Observaciones', []):
                        obstmp += "%(Code)s: %(Msg)s. " % obs['Obs']
                    
                    actualizar = dict(
                    obs = obstmp,
                    resultado=fecabresp['Resultado'],
                    cae=fedetresp['CAE'] and str(fedetresp['CAE']) or "",
                    fecha_cbte = ymd2date(fedetresp['CbteFch']),
                    cbte_nro = fedetresp['CbteHasta'],
                    fecha_vto = ymd2date(fedetresp['CAEFchVto']),
                    punto_vta = fecabresp['PtoVta'],
                    webservice = SERVICE 
                    )
                    
                else:
                    # rechazado
                    actualizar = dict(resultado = "R", cbte_nro = None)

                    
                if ('Errors' in result or 'Observaciones' in fedetresp):
                    # almacenar el informe de errores u observaciones
                    db.xml.insert(request = client.xml_request, response = client.xml_response)
                    

        elif SERVICE=='wsfex':

            result = client.FEXAuthorize(Auth={'Token': TOKEN, 'Sign': SIGN, 'Cuit': CUIT},
            Cmp = {\
                # str(db.paisdst[comprobante.dst_cmp].cuit).replace("-", "")\
                'Id': comprobante.id_ws,
                'Fecha_cbte': comprobante.fecha_cbte.strftime("%Y%m%d"),
                'Tipo_cbte': comprobante.tipocbte.cod,
                'Punto_vta': comprobante.punto_vta, 
                'Cbte_nro': comprobante.cbte_nro,
                'Tipo_expo': comprobante.tipo_expo or 1,
                'Permiso_existente': comprobante.permiso_existente,
                'Dst_cmp': comprobante.dst_cmp.cod,
                'Cliente': unicode(comprobante.nombre_cliente, "utf-8"),
                'Cuit_pais_cliente': comprobante.dstcuit.cuit,
                'Domicilio_cliente': unicode(comprobante.domicilio_cliente, "utf-8"), # genera excepción Unicode si se usan caracteres no ASCII
                'Id_impositivo': comprobante.id_impositivo,
                'Moneda_Id': comprobante.moneda_id.cod,
                'Moneda_ctz': comprobante.moneda_ctz,
                'Obs_comerciales': comprobante.obs_comerciales,
                'Imp_total': comprobante.imp_total,
                'Obs': comprobante.obs,
                'Forma_pago': comprobante.forma_pago,
                'Incoterms': comprobante.incoterms,
                'Incoterms_ds': comprobante.incoterms_ds,
                'Idioma_cbte': comprobante.idioma_cbte,

                # listas
                'Items': [{ 'Item': {
                'Pro_codigo': detalle.codigo, 'Pro_ds': unicode(detalle.ds, "utf-8"), 'Pro_qty': detalle.qty, 'Pro_umed': detalle.umed.cod, 'Pro_precio_uni': detalle.precio,
                'Pro_total_item': (detalle.imp_total)
                }} for detalle in db(db.detalle.comprobante == comprobante).select()],
                'Permisos': [{ 'Permiso': { 'Id_permiso': permiso.id_permiso, 'Dst_merc': permiso.dst_merc
                }} for permiso in db(db.permiso.comprobante == comprobante).select()],
                'Cmps_asoc': [{ 'Cmp_asoc': {
                'Cbte_tipo': comprobanteasociado.asociado.tipocbte.cod, 'Cbte_punto': comprobanteasociado.asociado.punto_vta, 'Cbte_numero': comprobanteasociado.asociado.cbte_nro
                }} for comprobanteasociado in db(db.comprobanteasociado.comprobante == comprobante).select()],
            })['FEXAuthorizeResult']
                    
            if 'FEXResultAuth' in result:        
                if result["FEXResultAuth"]["Resultado"] == "A":
                    session.comprobante = None
                    # aprobado
                    actualizar = dict(
                    obs = result["FEXResultAuth"]["Motivos_Obs"],
                    resultado=result["FEXResultAuth"]['Resultado'],
                    cae=result["FEXResultAuth"]["Cae"],
                    fecha_cbte = ymd2date(result["FEXResultAuth"]["Fch_cbte"]),
                    cbte_nro = result["FEXResultAuth"]["Cbte_nro"],
                    fecha_vto = ymd2date(result["FEXResultAuth"]["Fch_venc_Cae"]),
                    punto_vta = result["FEXResultAuth"]["Punto_vta"],
                    reproceso = result["FEXResultAuth"]["Reproceso"],
                    id_ws = result["FEXResultAuth"]["Id"],
                    webservice = SERVICE
                    )
                    
                else:
                    # rechazado
                    actualizar = dict(
                    obs = result["FEXResultAuth"]["Motivos_Obs"],
                    resultado=result["FEXResultAuth"]['Resultado'],
                    id_ws = result["FEXResultAuth"]["Id"],
                    err_code = result["FEXErr"]["ErrCode"],
                    err_msg = result["FEXErr"]["ErrMsg"],
                    webservice = SERVICE
                    )
                    db.xml.insert(request = client.xml_request, response = client.xml_response)
                    session.comprobante = None
                    
                if  result["FEXErr"]["ErrCode"] or result["FEXResultAuth"]["Motivos_Obs"]:
                    # almacenar el informe de errores u observaciones
                    db.xml.insert(request = client.xml_request, response = client.xml_response)
        
          
        elif SERVICE=='wsbfe':

            result = client.BFEAuthorize(\
            Auth={'Token': TOKEN, 'Sign': SIGN, 'Cuit': long(CUIT)},
            Cmp={'Id': comprobante.id_ws,
            'Tipo_doc': comprobante.tipodoc.cod,
            'Nro_doc': str(comprobante.nro_doc).replace("-", ""),
            'Zona': 1,
            'Tipo_cbte': comprobante.tipocbte.cod,
            'Fecha_cbte': comprobante.fecha_cbte.strftime("%Y%m%d"),
            'Punto_vta': comprobante.punto_vta,
            'Cbte_nro': comprobante.cbte_nro,
            'Imp_total': "%.2f" % comprobante.imp_total,
            'Imp_tot_conc': comprobante.imp_tot_conc or 0.00,
            'Imp_neto': "%.2f" % comprobante.imp_neto,
            'Impto_liq': "%.2f" % comprobante.impto_liq,
            'Impto_liq_rni': comprobante.impto_liq_rni or 0.00,
            'Imp_op_ex': comprobante.imp_op_ex or 0.00,
            'Imp_perc':  comprobante.impto_perc or 0.00,
            'Imp_iibb':  comprobante.imp_iibb or 0.00, 
            'Imp_perc_mun':  comprobante.impto_perc_mun or 0.00,
            'Imp_internos':  comprobante.imp_internos or 0.00,
            'Imp_moneda_Id': comprobante.moneda_id.cod,
            'Imp_moneda_ctz': comprobante.moneda_ctz,
            'Items': [{'Item': item} for item in detalles_bono_fiscal(comprobante)],
            }
            )

            if int(result["BFEAuthorizeResult"]["BFEErr"]["ErrCode"]) != 0:
                # hubo error?              
                errortmp = result["BFEAuthorizeResult"]["BFEErr"]
                actualizar = dict(err_code = unicode(errortmp["ErrCode"]), 
                err_msg = unicode(errortmp["ErrMsg"]), resultado = "R")
                session.comprobante = None

            else:
                # extraigo la respuesta (auth y eventos)            
                restmp = result["BFEAuthorizeResult"]["BFEResultAuth"]            
                
                actualizar = dict(
                id_ws=int(restmp["Id"]), 
                cae=str(restmp["Cae"]),
                fecha_cbte=ymd2date(restmp["Fch_cbte"]),
                resultado=str(restmp["Resultado"]),
                fecha_vto=ymd2date(restmp["Fch_venc_Cae"]),
                reproceso=str(restmp["Reproceso"]), 
                obs=str(restmp["Obs"])            
                )
                
                session.comprobante = None


        elif SERVICE=='wsmtxca':
            # campos período de servicio: borrar si es tipo 1
            if comprobante.concepto == 1:
                comprobante.fecha_serv_desde = None
                comprobante.fecha_serv_hasta = None
                comprobante.fecha_venc_pago = None

            fact = {
            'codigoTipoDocumento': comprobante.tipodoc.cod,
            'numeroDocumento':comprobante.nro_doc.replace("-", ""), 
            'codigoTipoComprobante': comprobante.tipocbte.cod,
            'numeroPuntoVenta': comprobante.punto_vta, 
            'numeroComprobante': comprobante.cbte_nro, 
            'importeTotal': comprobante.imp_total, 
            'importeNoGravado': comprobante.imp_tot_conc or "0.00",
            'importeGravado': comprobante.imp_neto, 
            'importeSubtotal': comprobante.imp_subtotal or comprobante.imp_neto, # 'imp_iva': imp_iva,
            'importeOtrosTributos': comprobante.imp_trib or None, 
            'importeExento': comprobante.imp_op_ex or "0.00", 
            'fechaEmision': date2y_m_d(comprobante.fecha_cbte) or None,
            'codigoMoneda': comprobante.moneda_id.cod, 
            'cotizacionMoneda': comprobante.moneda_ctz,
            'codigoConcepto': comprobante.concepto,
            'observaciones': comprobante.obs_comerciales,
            'fechaVencimientoPago': date2y_m_d(comprobante.fecha_venc_pago) or None,
            'fechaServicioDesde': date2y_m_d(comprobante.fecha_serv_desde) or None,
            'fechaServicioHasta': date2y_m_d(comprobante.fecha_serv_hasta) or None,
            'arrayComprobantesAsociados': [{'comprobanteAsociado': {
                'codigoTipoComprobante': cbte_asoc.asociado.tipocbte.cod,
                'numeroPuntoVenta': cbte_asoc.asociado.punto_vta, 
                'numeroComprobante': cbte_asoc.asociado.cbte_nro }} for cbte_asoc in db(db.comprobanteasociado.comprobante == comprobante).select()],
            'arrayOtrosTributos': [ {'otroTributo': {
                'codigo': tributo.tributo.id, 
                'descripcion': tributo.tributo.ds, 
                'baseImponible': tributo.base_imp, 
                'importe': tributo.importe }} for tributo in db(db.detalletributo.comprobante == comprobante).select()],
            'arraySubtotalesIVA': [{'subtotalIVA': { 
                'codigo': iva["id"],
                'importe': iva["importe"],
                }} for iva in comprobante_sumar_iva(comprobante)],
            'arrayItems': [{'item':{
                'unidadesMtx': it.umed.cod,
                'codigoMtx': it.codigomtx or "0000000000000",
                'codigo': it.codigo,                
                'descripcion': it.ds,
                'cantidad': it.qty,
                'codigoUnidadMedida': it.umed.cod,
                'precioUnitario': it.precio,
                'importeBonificacion': it.bonif or "0.00",
                'codigoCondicionIVA': it.iva.cod,
                'importeIVA': it.imp_iva or "0.00",
                'importeItem': it.imp_total or "0.00"}} for it in db(db.detalle.comprobante == comprobante).select()]
            }

            result = client.autorizarComprobante(
            authRequest={'token': TOKEN, 'sign': SIGN, 'cuitRepresentada': CUIT},
            comprobanteCAERequest = fact,
            )
        
            resultado = result['resultado'] # u'A'
            actualizar = {"obs": ""}
            # actualizar = dict()
            obs = []
            if result['resultado'] in ("A", "O"):
                cbteresp = result['comprobanteResponse']              
                fecha_cbte = cbteresp['fechaEmision'],
                fecha_vto = cbteresp['fechaVencimientoCAE'],
                actualizar["cae"] = cbteresp['CAE'], # 60423794871430L,

                if resultado == u"A":
                    session.comprobante = None
                else:
                    response.flash = "El cbte tiene observaciones"
                    session.comprobante = None
                    
            elif result['resultado'] == "R":
                session.comprobante = None
                for error in result["arrayErrores"]:
                    obs.append("%(codigo)s: %(descripcion)s" % (error['codigoDescripcion']))

                
            for error in result.get('arrayObservaciones', []):
               obs.append("%(codigo)s: %(descripcion)s" % (error['codigoDescripcion']))

            for error in obs:
                actualizar["obs"] += "Error %(codigo)s: %(descripcion)s. " % error['codigoDescripcion']

            actualizar["resultado"] = result['resultado']

        else:
            pass


    except SoapFault,sf:
        db.xml.insert(request = client.xml_request, response = client.xml_response)
        return dict( resultado = {'fault': sf.faultstring, 
                'xml_request': client.xml_request, 
                'xml_response': client.xml_response,
        }, pdf = None)

    except ExpatError, ee:
        return dict(resultado = "Error en el Cliente SOAP. Formato de respuesta inválido.", pdf = None)


    except (AttributeError, ValueError, TypeError, KeyError), ee:
        raise        
        db.xml.insert(request = client.xml_request, response = client.xml_response)
        return dict(resultado = {"fault": "Se produjo un error al procesar los datos del comprobante o los datos enviados son insuficientes. %s" % str(ee)}, pdf = None)


    # actualizo el registro del comprobante con el resultado:
    if actualizar:
        cbttmp = comprobante.as_dict()

        for k, v in actualizar.iteritems(): cbttmp[k] = v
        db(db.comprobante.id==comprobante).update(**cbttmp)
        
    return dict(resultado = result, pdf = A('Guardar el comprobante en formato PDF', _href=URL(r = request, c="salida", f="guardar_comprobante", args=[comprobante.id,])))

    
if SERVICE:

    try:
        # solicito autenticación
        if request.controller!="dummy":
    
            TOKEN, SIGN = _autenticar(SERVICE)        
        
        # conecto al webservice
        if SERVICE == "wsmtxca":
            client = SoapClient( 
                    wsdl = WSDL[SERVICE],
                    cache = PRIVATE_PATH,
                    ns = "ser",
                    trace = False,
                    # voidstr = True # comentar esta línea para pysimplesoap sin modificar
                    )
        else:
            client = SoapClient( 
                    wsdl = WSDL[SERVICE],
                    cache = PRIVATE_PATH,
                    trace = False,
                    # voidstr = True # comentar esta línea para pysimplesoap sin modificar
                    )

    except HTTPError, e:
        session.mensaje = "Error al solicitar el ticket de acceso: %s" % str(e)
        redirect(URL(c="default", f="mensaje"))
