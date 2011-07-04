# -*- coding: utf-8 -*-
# almacenamiento de duplicados de comprobantes RG 1361

""" Copyright 2011 Alan Etkin, spametki@gmail.com.

Este programa se distribuye bajo los términos de la licencia AGPLv3.

This program is free software: you can redistribute it and/or modify
it under the terms of the Affero GNU General Public License as published by
the Free Software Foundation, version 3 of the License, or any later
version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the Affero GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
import os, csv, datetime, calendar

hoy = datetime.datetime.now()
mesinforme = hoy.month -1
periodoinforme = hoy.year
if mesinforme == 0:
    mesinforme = 12
    periodoinforme = hoy.year -1

ARCHIVOS = {"CARPETA_DUPLICADOS": os.path.join("applications",
request.application, "private"), "modelo": {"cabecera":
{1: "registro_cabecera_1.csv", 2: "registro_cabecera_2.csv"},
"detalle": {None:"registro_detalle.csv",}, "ventas":
{1: "registro_ventas_1.csv", 2: "registro_ventas_2.csv"}, "compras":
{1: "registro_compras_1.csv", 2: "registro_compras_2.csv"},
"otras_percepciones": {None:"registro_otras_percepciones.csv",}},
"informe": {"cabecera":"CABECERA_AAAAMM.txt",
"detalle":"DETALLE_AAAAMM.txt", "ventas":"VENTAS_AAAAMM.txt",
"compras":"COMPRAS_AAAAMM.txt",
"otras_percepciones":"OTRAS_PERCEPCIONES_AAAAMM.txt"}}
BASEIVA = {1: "imp_tot_conc", 2:"imp_op_ex", 3:"imp_neto", 4:"imp_neto",
5:"imp_neto", 6:"imp_neto"}


# cantidad de alícuotas por cbte. ID=set([None,]) ó ID=set([int1, int2...intn])
alicuotas = {}

def lista_comprobantes(pedestal, umbral):
    """ Devuelve un listado de tuplas de la tabla db.comprobante
    ordenado según el período solicitado """
    comprobantes = db((db.comprobante.resultado != None) &
    (db.comprobante.fecha_cbte <= umbral) &
    (db.comprobante.fecha_cbte >= pedestal)).select(
    orderby=db.comprobante.fecha_cbte | db.comprobante.tipocbte |
    db.comprobante.cbte_nro | db.comprobante.punto_vta)
    try:
        return [(c.id, c) for c in comprobantes]
    except (KeyError, ValueError, TypeError, AttributeError):
        return []

def lista_detalles(comprobantes):
    """ Devuelve un listado de tuplas de la tabla db.detalle
    ordenado según los comprobantes solicitados"""
    detalles = []
    for c in comprobantes:
        detallestmp = db(db.detalle.comprobante == c[1]).select()
        for d in detallestmp: detalles.append((c[1].id, d))
    return detalles
    
def lista_compras(pedestal, umbral):
    """ Devuelve un listado de tuplas de la tabla db.compra
    ordenado según el período solicitado """
    compras = db((db.compra.fecha_cbte <= umbral) &
    (db.compra.fecha_cbte >= pedestal)).select(
    orderby=db.compra.fecha_cbte | db.compra.tipocbte |
    db.compra.cbte_nro | db.compra.punto_vta)
    try:
        return [(c.id, c) for c in compras]
    except (KeyError, ValueError, TypeError, AttributeError):
        return []

def lista_tributos(comprobantes):
    """ Devuelve un listado de tuplas de la tabla db.compra
    ordenado según el período solicitado """
    tributos = []
    for c in comprobantes:
        tributostmp = db(db.detalletributo.comprobante == c[1]).select()
        for t in tributostmp: tributos.append((c[1].id, t))
    return tributos

class Sired():
    CAMPOS_TIPO = {0: None, 1:"ALFABETICO", 2:"NUMERICO",
    3:"ALFANUMERICO", 4:"CARACTER ESPECIAL", 5:None,
    6:None, 7:None, 8:None, 9:"BLANCO"}
    SUBCAMPOS = {0:"INDICE", 1:"DESDE", 2:"HASTA",
    3:"POSICIONES", 4:"TIPO", 5:"DS", 6:"FUNCION", 7:"VALOR"}
    # list de tuplas: (INFORME, TIPO_REGISTRO, NRO_REGISTRO, CAMPONRO, DS)
    ENCABEZADO_ERROR = ["Informe", "Tipo de registro", "Nº de registro",
    "Campo Nº", "Descripción"]
    ERRORES_CAMPOS = (ValueError, KeyError, TypeError,
    ZeroDivisionError, IndexError, AttributeError, NameError)
    TIPOS_DE_REGISTRO = {"cabecera": (1, 2), "detalle": (None,),
    "ventas": (1, 2), "compras": (1, 2), "otras_percepciones": (None,)}
    BUCLE = {"cabecera": {1: "comprobantes", 2: None}, "detalle":
    {None: "detalles",}, "ventas": {1: "comprobantes", 2: None},
    "compras": {1: "compras", 2: None}, "otras_percepciones":
    {None: "tributos",}}

    # Los parámetros de listas(por ejemplo "comprobantes") deben tener
    #  el formato de conjunto de tuplas (ID de ref., instancia) para generar
    # las líneas de registros de cada informe.
    
    def __init__(self, pedestal, umbral, comprobantes = None,
    compras = None, archivos = None, variables = None, detalles = None,
    tributos = None, alicuotas = None, baseiva = None):
        # límites de fecha
        self.pedestal = pedestal; self.umbral = umbral
        self.archivos = archivos; self.variables = variables
        # objetos dict: key numérico: dict registro
        # nombres: dict registro
        self.registros = {"cabecera":{1:{}, 2:{}}, "detalle":{None:{},},
        "ventas":{1:{}, 2:{}}, "compras":{1:{}, 2:{}},
        "otras_percepciones":{None:{},}}
        # matriz dict con n listas de 8 valores (SUBCAMPOS)
        # n = cant. campos del informe (igual tipo 1/2/único)
        self.modelo = {"cabecera": {1:{}, 2:{}}, "detalle": {None:{},},
        "ventas": {1:{}, 2:{}}, "compras": {1:{}, 2:{}},
        "otras_percepciones":{None:{},}}
        # listas de objetos de la base de datos
        self.listas = {"comprobantes": comprobantes, "detalles": detalles,
        "compras": compras, "tributos": tributos}
        # tupla (ID, obj) para referencia en modelos
        self.obj = None
        # valores parciales para cálculo de informes
        self.parcial = {"imp_neto":0, "imp_tot_conc":0, "impto_liq":0,
        "imp_op_ex": 0, "imp_total": 0, "imp_iva": 0, "impto_liq_rni": 0,
        "impto_perc": 0, "imp_iibb": 0, "imp_subtotal": 0, "imp_trib": 0,
        "impto_perc_mun": 0, "imp_internos": 0, "imp_nac": 0,
        "base_imp_iva": 0, "base_imp_tributo": 0, "bonif": 0}
        self.errores = []
        self.alicuotas = alicuotas
        # importe a sumar según alícuota (item de cbte separados por alic.)
        self.baseiva = baseiva

    def borrar_parciales(self):
        for k, v in self.parcial.iteritems():
            v = 0

    def crear_informe(self, nombre):
        contador = 0
        for tr in self.TIPOS_DE_REGISTRO[nombre]:
            self.modelo[nombre][tr] = self.crear_registro(
            os.path.join(self.archivos["CARPETA_DUPLICADOS"],
            self.archivos["modelo"][nombre][tr]))
            if self.BUCLE[nombre][tr]:
                for ol in self.listas[self.BUCLE[nombre][tr]]:
                    contador +=1
                    self.obj = ol
                    if (self.alicuotas) and (nombre  == "ventas"):
                        # repetir registros para las alícuotas
                        if len(self.alicuotas[self.obj[0]]) > 0:
                            contador -= 1
                        # el primer registro del comprobante
                        inicial = True
                        final = False
                        # eliminar parciales
                        self.borrar_parciales()
                        for n, alicuota in enumerate(self.alicuotas[self.obj[0]]):
                            if n+1 == len(self.alicuotas[self.obj[0]]): final = True
                            contador += 1
                            self.registros[nombre][tr][contador] = \
                            self.modelo[nombre][tr].copy()
                            self.registros[nombre][tr][contador] = \
                            self.procesar_registro(nombre, tr, registro = \
                            self.registros[nombre][tr][contador], \
                            contador = contador, inicial = inicial, \
                            final = final, alicuota = alicuota)
                            inicial = False

                    else:
                        self.registros[nombre][tr][contador] = \
                        self.modelo[nombre][tr].copy()
                        self.registros[nombre][tr][contador] = \
                        self.procesar_registro(nombre, tr,
                        registro = self.registros[nombre][tr][contador], \
                        contador = contador)
            else:
                # 1: Recuperar formato de registro (modelo REGISTRO_CABECERA_2)
                # desde el archivo .csv
                # A: Crear un registro_cabecera_2
                # B: Actualizar el valor de cada campo validando el formato
                self.registros[nombre][tr] = self.modelo[nombre][tr].copy()
                self.registros[nombre][tr] = self.procesar_registro(nombre,
                tr, registro = self.registros[nombre][tr])

        return len(self.errores)

    def crear_registro(self, archivo):
        # crear registro en base a un archivo csv
        # abrir csv con módulo intérprete
        archivotmp = open(archivo, "r")
        spamReader = csv.reader(archivotmp)
        registro = dict()
        for linea in spamReader:
            if len(linea) > 0:
                registro[int(linea[0])] = tuple([v for v in linea])
        archivotmp.close()
        return registro

    def procesar_registro(self, nombre, tipo, registro = None,
    contador = None, inicial = False, final = False, alicuota = None):
        # procesar registro
        camponro = None
        try:
            for k, v in registro.iteritems():
                camponro = v[0]
                registro[k] = self.procesar_campo(v, inicial = inicial,
                final = final, alicuota = alicuota)

        except self.ERRORES_CAMPOS, e:
            self.errores.append([nombre, tipo, contador, camponro,
            str(e)])

        # fin de procesar registro
        return registro
        
    def procesar_campo(self, campo, inicial = False, \
    final = False, alicuota = None):
        # comprobante = compra = detalle = tributo = obj
        """ Recibe obj, campo: Calcula el valor según una función
        almacenada en el list y en base al tipo de objeto actualiza
        el valor al formato de RG1361 SIRED"""

        campotmp = list(campo)
        campotmp[7] = eval(campotmp[6])

        # pasar parametros de csv a int (longitud, tipo de valor)
        campotmp[4] = int(campotmp[4])
        campotmp[3] = int(campotmp[3])

        if int(campotmp[4]) in (1, 3):
            # alfabético
            campotmp[7] = str(campotmp[7])[:campotmp[3]].rjust(campotmp[3])

        elif int(campotmp[4]) == 2:
            # numérico
            campotmp[7] = str(campotmp[7])[:campotmp[3]].zfill(campotmp[3])

        elif int(campotmp[4]) == 9:
            # blanco
            campotmp[7] = "".rjust(campotmp[3])

        campo = tuple(campotmp)
        
        return campo

    def crear_csv(self, nombre, informe):
        """ Convertir el informe a formate csv """
        return None

    def convertir(self, nombre):
        """ Convertir el informe en formato para el aplicativo SIRED """
        texto = ""
        for tr in self.TIPOS_DE_REGISTRO[nombre]:
            if self.BUCLE[nombre][tr]:
                for k, v in self.registros[nombre][tr].iteritems():
                    for l, w in v.iteritems():
                        texto += str(w[7])
                    texto += "\r\n"
            else:
                for k, v in self.registros[nombre][tr].iteritems():
                    texto += str(v[7])

        if texto == "": texto = None
        return texto

    def real(self, r):
        # entero que termina con decimales o 0
        # atrapa errores por valores ausentes (None)
        try:
            r = float(r)
        except TypeError, ValueError:
            r = 0.0
        return r

    def texto(self, val):
        if val is None:
            val = ""
        val = str(val).decode("ascii", "replace").replace(u"\ufffd", "?")
        return val

    def numero(self, val):
        try:
            val = long(val)
        except self.ERRORES_CAMPOS, e:
            val = 0
        return val

    def importe(self, val):
        # formato compatible con informes SIAP-SIRED
        # entrada: valor o lista
        valtmp = 0
        if type(val) == list:
            valtmp = sum([float(valor) for valor in val if type(valor) \
            in [int, float, long]], 0.00)
            val = valtmp
        if not (type(val) in (float, int, long)):
            val = 0.00
        val = str(int(val*100))
        return val

    def sumar_importe(self, val, imp):
        try:
            val = float(val)
            imp = float(imp)
            imp += val
            val = imp
        except (ValueError, TypeError):
            """ TODO: manejo de errores de cálculo"""
            pass
        return imp

    def fecha(self, f):
        try:
            f = int(f.strftime("%Y%m%d"))
        except self.ERRORES_CAMPOS, e:
            f = 0
        return f

    def cae(self, c):
        try:
            l = long(c.replace("|", ""))
        except self.ERRORES_CAMPOS, e:
            l = "0"
        return l

@auth.requires_login()
def informe():
    registros = 0
    nombre = request.args[0]
    periodo = int(request.args[1])
    mes =  int(request.args[2])
    pedestal = datetime.date(periodo, mes, 1)
    umbral = datetime.date(periodo, mes, calendar.monthrange(periodo,
    mes)[1])
    texto = None
    
    guardar = request.vars.get("guardar", False)
    if guardar == "False": guardar = False
    elif guardar == "True": guardar = True
    else: guardar = False

    comprobantes = lista_comprobantes(pedestal, umbral)
    tributos = lista_tributos(comprobantes)
    detalles = lista_detalles(comprobantes)
    compras = lista_compras(pedestal, umbral)

    # alícuotas por cbte
    if nombre == "ventas":
        for c in comprobantes:
            # alícuotas del comprobante
            settmp = set([detalle[1].iva.cod for \
            detalle in detalles if detalle[0] == c[0]])
            # para cada alícuota del cbte
            # crear un list con dict: cod: (total_detalles, total sin alícuota,
            # total imp liq, total bonif.)
            alicuotas[c[0]] = dict()
            alicuotastmp = [(int(alic), ( \
            sum([det[1].imp_total \
            for det in detalles if (det[1].comprobante == c[0] \
            and det[1].iva.cod == alic)], 0.00), \
            sum([det[1].precio * det[1].qty \
            for det in detalles if (det[1].comprobante == c[0] \
            and det[1].iva.cod == alic)], 0.00), \
            sum([det[1].imp_iva \
            for det in detalles if (det[1].comprobante == c[0] \
            and det[1].iva.cod == alic)], 0.00), sum([det[1].bonif \
            for det in detalles if (det[1].comprobante == c[0] \
            and det[1].iva.cod == alic)], 0.00))) for alic in settmp]
            for al in alicuotastmp: alicuotas[c[0]][al[0]] = al[1]

            # agregar alícuota al set del cbte. en alicuotas
            alicuotas[c[0]] = alicuotas.get(c[0], set())

    isr = Sired(pedestal, umbral, comprobantes = comprobantes,
    compras = compras, variables = db(db.variables).select().first(),
    archivos = ARCHIVOS, detalles = detalles, tributos = tributos,
    alicuotas = alicuotas, baseiva = BASEIVA)

    isr.crear_informe(nombre)
    texto = isr.convertir(nombre)
    try:
        registros = len(texto.splitlines())
    except AttributeError:
        registros = 0
    if texto is None:
        texto = "No se generaron registros."
    else:
        if guardar:
            nombretmp = isr.archivos["informe"][nombre].replace("AAAA",
            str(periodo).zfill(4)).replace("MM", str(mes).zfill(2))
            archivo = open(os.path.join(isr.archivos["CARPETA_DUPLICADOS"],
            nombretmp), "w")
            archivo.write(texto)
            archivo.close()
            response.flash = "Se guardó el archivo %s" % str(nombretmp)
            # almacenar en db
            db.duplicado.insert(nombre = nombretmp, periodo = periodo,
            mes = mes, texto = texto)

    return dict(errores = isr.errores, nombre = nombre,
    registros = registros, texto = TEXTAREA( \
    texto, _class="duplicado"), alicuotas = alicuotas,
    periodo = periodo, mes = mes)

@auth.requires_login()
def texto():
    try:
        duplicado = db.duplicado[int(request.args[1])]
        txt = duplicado.texto
        nombre = duplicado.nombre
    except (ValueError, TypeError, KeyError, AttributeError, IndexError), e:
        raise HTTP(500, "Error al procesar el texto %s" % e)
    return dict(txt = txt, nombre = nombre)

@auth.requires_login()
def index():
    form = SQLFORM.factory(Field("periodo", "integer",
    requires=IS_IN_SET(range(2000, 2021)), default = periodoinforme),
    Field("mes", "integer", requires=IS_IN_SET({1:"enero", 2:"febrero",
    3:"marzo", 4:"abril", 5:"mayo", 6:"junio", 7:"julio", 8:"agosto",
    9:"septiembre", 10:"octubre", 11:"noviembre", 12:"diciembre"}),
    default = mesinforme), Field("informe", requires=IS_IN_SET(["cabecera",
    "detalle", "ventas", "compras", "otras_percepciones"])),
    Field("guardar", "boolean", default=False))
    
    if form.accepts(request.vars, session):
        redirect(URL(f="informe", args=[form.vars.informe,
        form.vars.periodo.zfill(4), form.vars.mes.zfill(2)],
        vars={"guardar": form.vars.guardar}))
    return dict(form = form)

@auth.requires_login()
def lista():
    try:
        periodo = int(request.vars.periodo)
    except (ValueError, IndexError, TypeError, KeyError, AttributeError):
        periodo = datetime.datetime.now().year
    
    form = SQLFORM.factory(Field("periodo", "integer",
    requires=IS_IN_SET(range(2000, 2021)), default = periodo), keepvalues = True)
    if form.accepts(request.vars, session): periodo = int(form.vars.periodo)

    return dict(duplicados = SQLTABLE(db(db.duplicado.periodo == periodo \
    ).select(limitby=(0,100)), linkto=URL(f="texto", extension="txt")),
    form = form, periodo = periodo)
    