# coding: utf8
# try something like

# ubicación de archivo de localidades
# archivo csv con encabezado y columnas
# 1: código de localidad
# 2: denominación de localidad
# 3: código de referencia de provincia
import os, csv

fuente_localidades = os.path.join(\
request.env.web2py_path,'applications',\
request.application,'static') + '/localidades.csv'

def index():
    """ panel de control del setup """
    mensajes = ""
    puntos_de_venta = 0
    variables = db(db.variables).select().first()
    pdvs = db(db.punto_de_venta).select()
    if not pdvs.first():
        id_pdv = db.punto_de_venta.insert(numero = 1, nombre = "Punto de venta 1")
        mensajes += "Nuevo punto de venta (1). "
        puntos_de_venta += 1
    if not variables:
        id_variables = db.variables.insert(punto_de_venta = db(db.punto_de_venta).select().first())
        variables = db(db.variables).select().first()        
        mensajes += "Se creó el registro de variables. "
        
    if len(mensajes) > 0: response.flash = mensajes

    puntos_de_venta += len(pdvs)
    tipos_doc = len(db(db.tipo_doc).select())
    tipos_cbte = len(db(db.tipo_cbte).select())
    monedas = len(db(db.moneda).select())   
    ivas = len(db(db.iva).select())
    idiomas = len(db(db.idioma).select())
    umedidas = len(db(db.umed).select())
    paises = len(db(db.pais_dst).select())
    provincias = len(db(db.provincia).select())
    localidades = len(db(db.localidad).select())
    condiciones_iva = len(db(db.condicion_iva).select())
    return dict(tipos_doc = tipos_doc, tipos_cbte = tipos_cbte, \
                monedas = monedas, ivas = ivas, idiomas = idiomas, \
                umedidas = umedidas, paises = paises, \
                provincias = provincias, localidades = localidades, \
                puntos_de_venta = puntos_de_venta, variables = variables, \
                condiciones_iva = condiciones_iva)

def variables():
    form = crud.update(db.variables, db(db.variables).select().first())
    return dict(form = form)

def crear_tipos_doc():
    "Crear inicialmente los tipos de documento más usados"
    data = """\
80 - CUIT
86 - CUIL
87 - CDI
89 - LE
90 - LC
92 - en trámite
96 - DNI
94 - Pasaporte
99 - Consumidor Final"""
    db(db.tipo_doc.cod>0).delete()
    l = []
    for d in data.split("\n"):
        i, desc = d.split(" - ")
        db.tipo_doc.insert(cod=i, desc=desc)
    return dict(ret=SQLTABLE(db(db.tipo_doc.cod>0).select()), \
                lista = A('Ver lista', _href=URL(r=request, c='setup', f='index')))

def crear_tipos_cbte():
    "Crear inicialmente los tipos de comprobantes más usados"
    data = """\
1 - Factura A - True
2 - Nota de Débito A - False
3 - Nota de Crédito A - False
4 - Recibo A - False
6 - Factura B - False
7 - Nota de Débito B - False
8 - Nota de Crédito B - False
9 - Recibo B - False
11 - Factura C - False
12 - Nota de Débito C - False
13 - Nota de Crédito C - False
15 - Recibo C - False
19 - Factura E - False
20 - Nota de Débito E - False
21 - Nota de Crédito E - False
51 - Factura M - True
52 - Nota de Débito M - False
53 - Nota de Crédito M - False
54 - Recibo M - False"""
    db(db.tipo_cbte.cod>0).delete()
    l = []
    for d in data.split("\n"):
        i, desc, discriminar = d.split(" - ")

        if discriminar == "False": discriminar = False
        elif discriminar == "True": discriminar = True
        else: discriminar = None

        db.tipo_cbte.insert(cod=i, desc=desc, discriminar=discriminar)
    return dict(ret=SQLTABLE(db(db.tipo_cbte.cod>0).select()),\
                lista = A('Ver lista', _href=URL(r=request, c='setup', f='index')))

def crear_monedas():
    "Crear inicialmente las monedas más usadas"
    data = """\
PES - Pesos Argentinos
DOL - Dólar Estadounidense
012 - Real
019 - Yens
060 - Euro"""
    db(db.moneda.id>0).delete()
    l = []
    for d in data.split("\n"):
        i, desc = d.split(" - ")
        db.moneda.insert(cod=i, desc=desc)
    return dict(ret=SQLTABLE(db(db.moneda.id>0).select()), \
                lista = A('Ver lista', _href=URL(r=request, c='setup', f='index')))


def crear_iva():
    "Crear inicialmente las alícuotas de IVA más usados"
    data = """\
1 - No gravado - None
2 - Exento - None
3 - 0% - 0.00
4 - 10.5% - 0.105
5 - 21% - 0.210
6 - 27% - 0.270"""
    db(db.iva.cod>0).delete()
    l = []
    for d in data.split("\n"):
        i, desc, aliquota = d.split(" - ")
        try:
            aliquota = float(aliquota)
        except ValueError, e:
            aliquota = None
        db.iva.insert(cod=i, desc=desc, aliquota=aliquota)
    return dict(ret=SQLTABLE(db(db.iva.cod>0).select()), \
                lista = A('Ver lista', _href=URL(r=request, c='setup', f='index')))

def crear_idiomas():
    "Crear inicialmente los idiomas"
    data = """\
1 - Español
2 - Inglés
3 - Portugués"""
    db(db.idioma.id>0).delete()
    l = []
    for d in data.split("\n"):
        i, desc = d.split(" - ")
        db.idioma.insert(cod=int(i), desc=desc)
    return dict(ret=SQLTABLE(db(db.idioma.id>0).select()), \
                lista = A('Ver lista', _href=URL(r=request, c='setup', f='index')))

def crear_umedidas():
    data = """\
1 - kilogramos
5 - litros
7 - unidades
2 - metros
3 - metros cuadrados
4 - metros cúbicos
0 -  """

    db(db.umed.cod>=0).delete()
    l = []
    for d in data.split("\n"):
        i, desc = d.split(" - ")
        db.umed.insert(cod=i, desc=desc)
    return dict(ret=SQLTABLE(db(db.umed.id>0).select()), \
                lista = A('Ver lista', _href=URL(r=request, c='setup', f='index')))

def crear_paises():
    data = {200: u'ARGENTINA', 202: u'BOLIVIA', 203: u'BRASIL', 204: u'CANADA', 205: u'COLOMBIA', 206: u'COSTA RICA', 207: u'CUBA', 208: u'CHILE', 210: u'ECUADOR', 211: u'EL SALVADOR', 212: u'ESTADOS UNIDOS',  218: u'MEXICO', 221: u'PARAGUAY', 222: u'PERU', 225: u'URUGUAY', 226: u'VENEZUELA', 250: u'AAE Tierra del Fuego - ARGENTINA', 251: u'ZF La Plata - ARGENTINA', 252: u'ZF Justo Daract - ARGENTINA', 253: u'ZF R\xedo Gallegos - ARGENTINA', 254: u'Islas Malvinas - ARGENTINA', 255: u'ZF Tucum\xe1n - ARGENTINA', 256: u'ZF C\xf3rdoba - ARGENTINA', 257: u'ZF Mendoza - ARGENTINA', 258: u'ZF General Pico - ARGENTINA', 259: u'ZF Comodoro Rivadavia - ARGENTINA', 260: u'ZF Iquique', 261: u'ZF Punta Arenas', 262: u'ZF Salta - ARGENTINA', 263: u'ZF Paso de los Libres - ARGENTINA', 264: u'ZF Puerto Iguaz\xfa - ARGENTINA', 265: u'SECTOR ANTARTICO ARG.', 270: u'ZF Col\xf3n - REP\xdaBLICA DE PANAM\xc1', 271: u'ZF Winner (Sta. C. de la Sierra) - BOLIVIA', 280: u'ZF Colonia - URUGUAY', 281: u'ZF Florida - URUGUAY', 282: u'ZF Libertad - URUGUAY', 283: u'ZF Zonamerica - URUGUAY', 284: u'ZF Nueva Helvecia - URUGUAY', 285: u'ZF Nueva Palmira - URUGUAY', 286: u'ZF R\xedo Negro - URUGUAY', 287: u'ZF Rivera - URUGUAY', 288: u'ZF San Jos\xe9 - URUGUAY', 291: u'ZF Manaos - BRASIL', }
    db(db.pais_dst.cod>=0).delete()
    for k,v in data.items():
        db.pais_dst.insert(cod=k, desc=v)
    return dict(ret=SQLTABLE(db(db.pais_dst.id>0).select()), \
                lista = A('Ver lista', _href=URL(r=request, c='setup', f='index')))

def crear_provincias():
    data = {0: u"C.A.B.A.",1: u"Buenos Aires", 2: u"Catamarca", 3: u"Córdoba",4: u"Corrientes", 5: u"Entre Ríos", 6:
u"Jujuy", 7: u"Mendoza", 8: u"La Rioja", 9: u"Salta", 10: u"San Juan", 11:
u"San Luis", 12: u"Santa Fe", 13: u"Santiago del Estero", 14:
u"Tucuman", 16: u"Chaco", 17: u"Chubut", 18: u"Formosa", 19: u"Misiones", 20:
u"Neuquen", 21: u"La Pampa", 22: u"Río Negro", 23: u"Santa Cruz", 24: u"Tierra del Fuego"}
    db(db.provincia.cod>=0).delete()
    for k,v in data.items():
        db.provincia.insert(cod=k, desc=v)
    return dict(ret=SQLTABLE(db(db.provincia.id>-1).select()), \
                lista = A('Ver lista', _href=URL(r=request, c='setup', f='index')))

   
def crear_localidades():
    """ crea localidades en la base de datos
    """
    provincias = [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,16,17,18,19,20,21,22,23,24]
    # 1) abrir csv con módulo intérprete
    spamReader = csv.reader(open(fuente_localidades, "r"))
    # 2) para cada registro de csv crear un registro de la base
    # utilizando código de localidad y de provincia (referencia)
    errores = list()
    registros = 0
    db(db.localidad.id > -1).delete()
    db.commit()
    contador = 0
    for linea in spamReader:
        contador +=1
        try:
            if (int(linea[0]) and (len(linea[1]) > 0) and (int(linea[2]) in provincias)):
                # modificar (una consulta por registro)
                la_provincia = db(db.provincia.cod == linea[2]).select().first().id            
                db.localidad.insert(cod=str(int(linea[0])), desc=linea[1], provincia=la_provincia)
                registros += 1
        except (ValueError, AttributeError, TypeError), e:
            errores.append(str(e) + " (Fila %s)" % contador)
    return dict(registros = registros, errores = errores, \
                lista = A('Ver lista', _href=URL(r=request, c='setup', f='index')))


def crear_condiciones_iva():
    data = {'IVA Responsable Inscripto': 1, 'IVA Responsable no Inscripto': 2, 'IVA no Responsable': 3,'IVA Sujeto Exento': 4,'Consumidor Final': 5, 'Responsable Monotributo': 6, 'Sujeto no Categorizado': 7, 'Importador del Exterior': 8, 'Cliente del Exterior': 9, 'IVA Liberado - Ley Nº 19.640': 10, 'IVA Responsable Inscripto - Agente de Percepción': 11}
    db(db.condicion_iva.codigo>=0).delete()
    for k,v in data.items():
        db.condicion_iva.insert(codigo=v, desc=k)
    return dict(ret=SQLTABLE(db(db.condicion_iva.id>-1).select()), \
                lista = A('Ver lista', _href=URL(r=request, c='setup', f='index')))
