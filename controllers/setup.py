# -*- coding: utf-8 -*-

# try something like

# get/create variables/variablesusuario en una función

# ubicación de archivo de localidades
# archivo csv con encabezado y columnas
# 1: código de localidad
# 2: denominación de localidad
# 3: código de referencia de provincia

# requerir usuario administrador

# TODO: Carga de registros desde csv completa cuando la base de datos es local (mismo host)

import os, csv

fuente_localidades = os.path.join(\
request.env.web2py_path,'applications',\
request.application,'private') + '/localidades.csv'

fuente_aduanas = os.path.join(\
request.env.web2py_path,'applications',\
request.application,'private') + '/aduanas.csv'

fuente_destinaciones = os.path.join(\
request.env.web2py_path,'applications',\
request.application,'private') + '/destinaciones.csv'


""" roles: emisor, auditor, invitado:

emisor: autorización de cbtes, consultas
auditor: consultas cbtes y detalles
invitado: conultas cbtes y demo del sistema

"""

invitado_group_id = db(db.auth_group.role == "invitado").select().first()
emisor_group_id = db(db.auth_group.role == "emisor").select().first()
auditor_group_id = db(db.auth_group.role == "auditor").select().first()
administrador_group_id = db(db.auth_group.role == "administrador").select().first()


def nuevo_administrador():
    return dict(mensaje = "Se configuró la cuenta administrador@localhost con las opciones por defecto.")

if emisor_group_id == None:
    emisor_group_id = db.auth_group.insert(role = "emisor", description = "Autorización de cbtes y consultas")

if auditor_group_id == None:
    auditor_group_id =db.auth_group.insert(role = "auditor", description = "Consultas")

if invitado_group_id == None:
    invitado_group_id = db.auth_group.insert(role = "invitado", description = "Uso limitado")

if administrador_group_id == None:
    administrador_group_id = db.auth_group.insert(role = "administrador", description = "Acceso total")

if len(db(db.auth_membership.group_id == administrador_group_id).select()) < 1:
    db(db.auth_user.email == "administrador@localhost").update(\
    password = db.auth_user.password.validate("facturalibre")[0], \
    first_name = "Administrador", last_name = "FacturaLibre" \
    ) or db.auth_user.insert(\
    password = db.auth_user.password.validate("facturalibre")[0], \
    first_name = "Administrador", last_name = "FacturaLibre", \
    email = "administrador@localhost" \
    )

    id_administrador = db(db.auth_user.email == "administrador@localhost").select().first().id
    db.auth_membership.insert(group_id = administrador_group_id, user_id = id_administrador)
    session.configuracion_administrador = True
    redirect(URL(f="nuevo_administrador"))


@auth.requires(auth.has_membership("administrador"))
def rol_cambiar():
    
    role = db.auth_group[db.auth_membership[request.args[1]].group_id].role
    if role.startswith("user_"):
        form = None
        response.flash = "Rol de sistema / no editable"
    else:
        form = crud.update(db.auth_membership, request.args[1], deletable = False)

    return dict(form = form)


@auth.requires(auth.has_membership("administrador"))
def roles_editar():
    # para todo usuario sin grupo crear/asignar grupo invitado
    
    for usuario in db(db.auth_user).select():
        if (len(db(db.auth_membership.user_id == usuario.id).select()) < 2):
            db.auth_membership.insert(user_id = usuario.id, group_id = invitado_group_id)
    
    tabla = SQLTABLE(db(db.auth_membership).select(), linkto = URL(c="setup", f="rol_cambiar"))
    return dict(tabla = tabla)


@auth.requires_login()
def index():
    """ panel de control del setup """
    mensajes = ""
    if session.configuracion_administrador:
        mensajes += "Se reinició la configuración del usuario administrador: administrador@localhost (contraseña por defecto). "
        session.configuracion_administrador = False
        
    puntos_de_venta = 0

    # proteger visualización de variables (restringir a administrador)
    variables = db(db.variables).select().first()

    
    variablesusuario = db(db.variablesusuario.usuario == auth.user_id).select().first()
    pdvs = db(db.puntodeventa).select()
    if not pdvs.first():
        id_pdv = db.puntodeventa.insert(numero = 1, nombre = "Punto de venta 1")
        mensajes += "Nuevo punto de venta (1). "
        puntos_de_venta += 1
    if not variables:
        id_variables = db.variables.insert(puntodeventa = db(db.puntodeventa).select().first())
        variables = db(db.variables).select().first()        
        mensajes += "Se creó el registro de variables. "
    if not variablesusuario:
        id_variablesusuario = db.variablesusuario.insert(usuario = auth.user_id, \
        puntodeventa = variables.puntodeventa, \
        moneda = variables.moneda, \
        webservice = variables.webservice, \
        tipocbte = variables.tipocbte, \
        venc_pago = variables.venc_pago, \
        forma_pago = variables.forma_pago)
        
    if len(mensajes) > 0: response.flash = mensajes

    roles = []
    try:
        los_roles = db(db.auth_group).select()
        for rol in los_roles:
            roles.append(rol.role)
        
    except (KeyError, AttributeError, ValueError):
        roles = ["No se han creado roles para usuarios",]
        
    puntos_de_venta += len(pdvs)
    tipos_doc = len(db(db.tipodoc).select())
    tipos_cbte = len(db(db.tipocbte).select())
    monedas = len(db(db.moneda).select())   
    ivas = len(db(db.iva).select())
    idiomas = len(db(db.idioma).select())
    umedidas = len(db(db.umed).select())
    paises = len(db(db.paisdst).select())
    provincias = len(db(db.provincia).select())
    localidades = len(db(db.localidad).select())
    condiciones_iva = len(db(db.condicioniva).select())
    cuit_paises = len(db(db.dstcuit).select())
    clientes = len(db(db.cliente).select())
    tributos = len(db(db.tributo).select())
    productos = len(db(db.producto).select())
    plantilla_base = db(db.pdftemplate).select().first()

    esadmin = auth.has_membership("administrador")
    if not esadmin: variables = None
    return dict(tipos_doc = tipos_doc, tipos_cbte = tipos_cbte, \
                monedas = monedas, ivas = ivas, idiomas = idiomas, \
                umedidas = umedidas, paises = paises, \
                provincias = provincias, localidades = localidades, \
                puntos_de_venta = puntos_de_venta, variables = variables, \
                variablesusuario = variablesusuario, \
                condiciones_iva = condiciones_iva, roles = roles, \
                cuit_paises = cuit_paises, clientes = clientes, \
                productos = productos, tributos = tributos, plantilla_base = plantilla_base)


@auth.requires(auth.has_membership("administrador"))
def variables():
    form = crud.update(db.variables, db(db.variables).select().first())
    return dict(form = form)

@auth.requires_login()
def variablesusuario():
    variablesusuario = db(db.variablesusuario.usuario == auth.user_id).select().first()
    if not variablesusuario:
        id = db.variablesusuario.insert(usuario = auth.user_id)
        try:
            variables = db(db.variables).select().first()
            db.variablesusuario[id].update(\
                puntodeventa = variables.puntodeventa, \
                moneda = variables.moneda, \
                webservice = variables.webservice, \
                tipocbte = variables.tipocbte, \
                venc_pago = variables.venc_pago, \
                forma_pago = variables.forma_pago
            )
        except (KeyError, AttributeError, ValueError):
            response.flash = "No se configuraron las variables de facturación"
            pass
        
    variablesusuario = db(db.variablesusuario.usuario == auth.user_id).select().first()
    
    form = crud.update(db.variablesusuario, variablesusuario, deletable = False)
    
    # cancelar cbte actual
    session.comprobante = None
    
    return dict(form = form)


@auth.requires(auth.has_membership("administrador"))
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
    db(db.tipodoc.id>0).delete()
    l = []
    for d in data.split("\n"):
        i, ds = d.split(" - ")
        db.tipodoc.insert(cod=i, ds=ds)
    return dict(ret=SQLTABLE(db(db.tipodoc.id>0).select()), \
                lista = A('Ver lista', _href=URL(r=request, c='setup', f='index')))

JURIIBB = {1: u'C.A.B.A.',2: u'Buenos Aires', 3: u'Catamarca', 4: u'Córdoba',5: u'Corrientes', 25: u'Entre Ríos', 10:
u'Jujuy', 13: u'Mendoza', 12: u'La Rioja', 17: u'Salta', 18: u'San Juan', 19:
u'San Luis', 21: u'Santa Fe', 22: u'Santiago del Estero', 24:
u'Tucuman', 6: u'Chaco', 7: u'Chubut', 9: u'Formosa', 14: u'Misiones', 15:
u'Neuquen', 11: u'La Pampa', 16: u'Río Negro', 20: u'Santa Cruz', 23: u'Tierra del Fuego'}


def crear_tributos():
    "Crear inicialmente los tributos más usados"
    data = """\
1 - IIBB C.A.B.A. - 99
2 - IIBB Buenos Aires  - 99
3 - IIBB Catamarca  - 99
4 - IIBB Córdoba  - 99
5 - IIBB Corrientes  - 99
8 - IIBB Entre Ríos  - 99
10 - IIBB Jujuy  - 99
13 - IIBB Mendoza  - 99
12 - IIBB La Rioja  - 99
17 - IIBB Salta  - 99
18 - IIBB San Juan  - 99
19 - IIBB San Luis  - 99
21 - IIBB Santa Fe  - 99
22 - IIBB Santiago del Estero  - 99
24 - IIBB Tucumán  - 99
6 - IIBB Chaco  - 99
7 - IIBB Chubut  - 99
9 - IIBB Formosa  - 99
14 - IIBB Misiones  - 99
15 - IIBB Neuquén  - 99
11 - IIBB La Pampa  - 99
16 - IIBB Río Negro  - 99
20 - IIBB Santa Cruz  - 99
23 - IIBB Tierra del Fuego  - 99"""
    db(db.tributo.id>0).delete()
    l = []
    for d in data.split("\n"):
        i, ds, cod = d.split(" - ")
        db.tributo.insert(aliquota=1, juriibb=int(i), ds=ds, iibb = True, cod = int(cod))
    return dict(ret=SQLTABLE(db(db.tributo.id>0).select()), \
                lista = A('Ver lista', _href=URL(r=request, c='setup', f='index')))


@auth.requires(auth.has_membership("administrador"))
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
    db(db.tipocbte.id>0).delete()
    l = []
    for d in data.split("\n"):
        i, ds, discriminar = d.split(" - ")

        if discriminar == "False": discriminar = False
        elif discriminar == "True": discriminar = True
        else: discriminar = None

        db.tipocbte.insert(cod=i, ds=ds, discriminar=discriminar)
    return dict(ret=SQLTABLE(db(db.tipocbte.id>0).select()),\
                lista = A('Ver lista', _href=URL(r=request, c='setup', f='index')))

@auth.requires(auth.has_membership("administrador"))
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
        i, ds = d.split(" - ")
        db.moneda.insert(cod=i, ds=ds)
    return dict(ret=SQLTABLE(db(db.moneda.id>0).select()), \
                lista = A('Ver lista', _href=URL(r=request, c='setup', f='index')))


@auth.requires(auth.has_membership("administrador"))
def crear_iva():
    "Crear inicialmente las alícuotas de IVA más usados"
    data = """\
1 - No gravado - None
2 - Exento - None
3 - 0% - 0.00
4 - 10.5% - 0.105
5 - 21% - 0.210
6 - 27% - 0.270"""
    db(db.iva.id>0).delete()
    l = []
    for d in data.split("\n"):
        i, ds, aliquota = d.split(" - ")
        try:
            aliquota = float(aliquota)
        except ValueError, e:
            aliquota = None
        
        db.iva.insert(cod=i, ds=ds, aliquota=aliquota)
    return dict(ret=SQLTABLE(db(db.iva.id>0).select()), \
                lista = A('Ver lista', _href=URL(r=request, c='setup', f='index')))

@auth.requires(auth.has_membership("administrador"))
def crear_idiomas():
    "Crear inicialmente los idiomas"
    data = """\
1 - Español
2 - Inglés
3 - Portugués"""
    db(db.idioma.id>0).delete()
    l = []
    for d in data.split("\n"):
        i, ds = d.split(" - ")
        db.idioma.insert(cod=int(i), ds=ds)
    return dict(ret=SQLTABLE(db(db.idioma.id>0).select()), \
                lista = A('Ver lista', _href=URL(r=request, c='setup', f='index')))

@auth.requires(auth.has_membership("administrador"))
def crear_umedidas():
    data = """\
1 - kilogramos
5 - litros
7 - unidades
2 - metros
3 - metros cuadrados
4 - metros cúbicos
0 -  """

    db(db.umed.id>=0).delete()
    l = []
    for d in data.split("\n"):
        i, ds = d.split(" - ")
        db.umed.insert(cod=i, ds=ds)
    return dict(ret=SQLTABLE(db(db.umed.id>0).select()), \
                lista = A('Ver lista', _href=URL(r=request, c='setup', f='index')))

@auth.requires(auth.has_membership("administrador"))
def crear_paises():
    data = {200: u'ARGENTINA', 202: u'BOLIVIA', 203: u'BRASIL', 204: u'CANADA', 205: u'COLOMBIA', 206: u'COSTA RICA', 207: u'CUBA', 208: u'CHILE', 210: u'ECUADOR', 211: u'EL SALVADOR', 212: u'ESTADOS UNIDOS',  218: u'MEXICO', 221: u'PARAGUAY', 222: u'PERU', 225: u'URUGUAY', 226: u'VENEZUELA', 250: u'AAE Tierra del Fuego - ARGENTINA', 251: u'ZF La Plata - ARGENTINA', 252: u'ZF Justo Daract - ARGENTINA', 253: u'ZF R\xedo Gallegos - ARGENTINA', 254: u'Islas Malvinas - ARGENTINA', 255: u'ZF Tucum\xe1n - ARGENTINA', 256: u'ZF C\xf3rdoba - ARGENTINA', 257: u'ZF Mendoza - ARGENTINA', 258: u'ZF General Pico - ARGENTINA', 259: u'ZF Comodoro Rivadavia - ARGENTINA', 260: u'ZF Iquique', 261: u'ZF Punta Arenas', 262: u'ZF Salta - ARGENTINA', 263: u'ZF Paso de los Libres - ARGENTINA', 264: u'ZF Puerto Iguaz\xfa - ARGENTINA', 265: u'SECTOR ANTARTICO ARG.', 270: u'ZF Col\xf3n - REP\xdaBLICA DE PANAM\xc1', 271: u'ZF Winner (Sta. C. de la Sierra) - BOLIVIA', 280: u'ZF Colonia - URUGUAY', 281: u'ZF Florida - URUGUAY', 282: u'ZF Libertad - URUGUAY', 283: u'ZF Zonamerica - URUGUAY', 284: u'ZF Nueva Helvecia - URUGUAY', 285: u'ZF Nueva Palmira - URUGUAY', 286: u'ZF R\xedo Negro - URUGUAY', 287: u'ZF Rivera - URUGUAY', 288: u'ZF San Jos\xe9 - URUGUAY', 291: u'ZF Manaos - BRASIL', }
    db(db.paisdst.id>=0).delete()
    for k,v in data.items():
        db.paisdst.insert(cod=k, ds=v)
    return dict(ret=SQLTABLE(db(db.paisdst.id>0).select()), \
                lista = A('Ver lista', _href=URL(r=request, c='setup', f='index')))

@auth.requires(auth.has_membership("administrador"))
def crear_provincias():
    data = {0: u"C.A.B.A.",1: u"Buenos Aires", 2: u"Catamarca", 3: u"Córdoba",4: u"Corrientes", 5: u"Entre Ríos", 6:
u"Jujuy", 7: u"Mendoza", 8: u"La Rioja", 9: u"Salta", 10: u"San Juan", 11:
u"San Luis", 12: u"Santa Fe", 13: u"Santiago del Estero", 14:
u"Tucuman", 16: u"Chaco", 17: u"Chubut", 18: u"Formosa", 19: u"Misiones", 20:
u"Neuquen", 21: u"La Pampa", 22: u"Río Negro", 23: u"Santa Cruz", 24: u"Tierra del Fuego"}
    db(db.provincia.id>=0).delete()
    for k,v in data.items():
        db.provincia.insert(cod=k, ds=v)
    return dict(ret=SQLTABLE(db(db.provincia.id>0).select()), \
                lista = A('Ver lista', _href=URL(r=request, c='setup', f='index')))

@auth.requires(auth.has_membership("administrador"))
def crear_localidades():
    """ crea localidades en la base de datos
    """

    provincias = [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,16,17,18,19,20,21,22,23,24]
    errores = 0
    registros = 0
    db(db.localidad.id > -1).delete()
    contador = 0

    # 1) para cada registro de csv crear un registro de la base
    # utilizando código de localidad y de provincia (referencia)
    
    # 2) abrir csv con módulo intérprete
    spamReader = csv.reader(open(fuente_localidades, "r"))
    
    db.commit()
    # No usar sin sqlite: no sirve para bases de datos remotas (consulta extensa)
    for linea in spamReader:
        contador +=1
        try:
            if (int(linea[0]) and (len(linea[1]) > 0) and (int(linea[2]) in provincias)):
                # modificar (una consulta por registro)
                la_provincia = db(db.provincia.cod == linea[2]).select().first().id
                db.localidad.insert(cod=str(int(linea[0])), ds=linea[1], provincia=la_provincia)
                registros += 1
        except (ValueError, AttributeError, TypeError), e:
            errores += 1

    """
    # reemplazar por carga de csv en bases de datos remotas
    try:
        caba = db(db.provincia.cod == 0).select().first().id
    except (ValueError, TypeError, KeyError, AttributeError):
        raise HTTP(500, "Se deben crear los registros de provincias.")

    db.localidad.insert(cod=0, ds="Ciudad Autónoma de Buenos Aires", provincia=caba)
    registros +=1
    """

    return dict(ret = "Total: " + str(registros) + " localidades", errores = str(errores) + " errores.", \
                lista = A('Ver lista', _href=URL(r=request, c='setup', f='index')))


@auth.requires(auth.has_membership("administrador"))
def crear_aduanas():
    """ crea aduanas en la base de datos
    """

    errores = 0
    registros = 0
    db(db.aduana.id > -1).delete()
    contador = 0

    # 1) para cada registro de csv crear un registro de la base
    # utilizando código de aduana

    # 2) abrir csv con módulo intérprete
    spamReader = csv.reader(open(fuente_aduanas, "r"))

    db.commit()
    # No usar sin sqlite: no sirve para bases de datos remotas (consulta extensa)
    for linea in spamReader:
        contador +=1
        try:
            if (int(linea[0]) and (len(linea[1]) > 0)):
                # modificar (una consulta por registro)
                db.aduana.insert(cod=str(int(linea[0])), ds=linea[1])
                registros += 1
        except (ValueError, AttributeError, TypeError), e:
            errores += 1

    return dict(registros = registros, errores = errores, \
                lista = A('Ver lista', _href=URL(r=request, c='setup', f='index')))


@auth.requires(auth.has_membership("administrador"))
def crear_destinaciones():
    """ crea aduanas en la base de datos
    """

    errores = 0
    registros = 0
    db(db.destinacion.id > -1).delete()
    contador = 0

    # 1) para cada registro de csv crear un registro de la base
    # utilizando código de aduana

    # 2) abrir csv con módulo intérprete
    spamReader = csv.reader(open(fuente_destinaciones, "r"))

    lista_errores = []

    db.commit()
    # No usar sin sqlite: no sirve para bases de datos remotas (consulta extensa)
    for linea in spamReader:
        contador +=1
        try:
            if (linea[0] and (len(linea[1]) > 0)):
                # modificar (una consulta por registro)
                db.destinacion.insert(cod=str(linea[0]), ds=linea[1])
                registros += 1
        except (ValueError, AttributeError, TypeError), e:
            errores += 1
            lista_errores.append(str(e))

    return dict(registros = registros, errores = errores, \
                lista = A('Ver lista', _href=URL(r=request, c='setup', f='index')), lista_errores = lista_errores)


@auth.requires(auth.has_membership("administrador"))
def crear_condiciones_iva():
    data = {'IVA Responsable Inscripto': 1, 'IVA Responsable no Inscripto': 2, 'IVA no Responsable': 3,'IVA Sujeto Exento': 4,'Consumidor Final': 5, 'Responsable Monotributo': 6, 'Sujeto no Categorizado': 7, 'Importador del Exterior': 8, 'Cliente del Exterior': 9, 'IVA Liberado - Ley Nº 19.640': 10, 'IVA Responsable Inscripto - Agente de Percepción': 11}
    db(db.condicioniva.id>0).delete()
    for k,v in data.items():
        db.condicioniva.insert(cod=v, ds=k)
    return dict(ret=SQLTABLE(db(db.condicioniva.id>-1).select()), \
                lista = A('Ver lista', _href=URL(r=request, c='setup', f='index')))

@auth.requires(auth.has_membership("administrador"))
def modificar():
    """ Listas de objetos de la base de datos """

    clientes = SQLTABLE(db(db.cliente).select(), linkto = URL(f="modificar_objeto"), columns=["cliente.id", "cliente.nombre_cliente", "cliente.email", "cliente.domicilio_cliente", "cliente.nro_doc"], headers = {"cliente.id": "Editar", "cliente.nombre_cliente": "Nombre", "cliente.email": "Email", "cliente.domicilio_cliente": "Domicilio", "cliente.nro_doc": "Nro. Doc."})

    productos = SQLTABLE(db(db.producto).select(), linkto = URL(f="modificar_objeto"), columns = ["producto.id", "producto.codigo", "producto.ds", "producto.precio" ], headers = {"producto.id": "Editar", "producto.codigo": "Código", "producto.ds": "Descripción", "producto.precio": "Precio"})

    tributos = SQLTABLE(db(db.tributo).select(), linkto = URL(f="modificar_objeto"), columns = ["tributo.id", "tributo.ds", "tributo.aliquota"], headers = {"tributo.id": "Editar", "tributo.ds": "Descripción", "tributo.aliquota": "Alícuota"})

    puntos_de_venta = SQLTABLE(db(db.puntodeventa).select(), linkto = URL(f="modificar_objeto"), columns = ["puntodeventa.id", "puntodeventa.numero", "puntodeventa.nombre"], headers = {"puntodeventa.id": "Editar", "puntodeventa.numero": "Número", "puntodeventa.nombre": "Nombre"})

    return dict(clientes = clientes, tributos = tributos, productos = productos, puntos_de_venta = puntos_de_venta)

@auth.requires(auth.has_membership("administrador"))
def modificar_objeto():
    return dict(form = crud.update(request.args[0], request.args[1], next = URL(f="modificar")), nombre = str(request.args[0]).replace("_", " "))

@auth.requires(auth.has_membership("administrador"))
def crear_cliente():
    form = crud.create(db.cliente, next = URL(r = request, f="index"))
    return dict(form = form)

@auth.requires(auth.has_membership("administrador"))
def crear_tributo():
    form = crud.create(db.tributo, next = URL(r = request, f="index"))
    return dict(form = form)

@auth.requires(auth.has_membership("administrador"))
def crear_producto():
    form = crud.create(db.producto, next = URL(r = request, f="index"))
    return dict(form = form)

@auth.requires(auth.has_membership("administrador"))
def crear_puntodeventa():
    form = crud.create(db.puntodeventa, next = URL(r = request, f="index"))
    return dict(form = form)
