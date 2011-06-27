# -*- coding: utf-8 -*-
# almacenamiento de duplicados de comprobantes RG 1361
import os, csv, datetime, calendar

ARCHIVOS = {"CARPETA_DUPLICADOS": os.path.join("applications",
request.application, "private"), "modelo": {"cabecera":
{1: "registro_cabecera_1.csv", 2: "registro_cabecera_2.csv"}},
"informe": {"cabecera":"CABECERA_AAAAMM.txt"}}

def lista_comprobantes(pedestal, umbral):
    """ Devuelve un listado de la tabla db.comprobante
    ordenado según el período solicitado """
    comprobantes = db((db.comprobante.resultado != None) &
    (db.comprobante.fecha_cbte <= umbral) &
    (db.comprobante.fecha_cbte >= pedestal)).select(
    orderby=db.comprobante.fecha_cbte | db.comprobante.tipocbte |
    db.comprobante.cbte_nro | db.comprobante.punto_vta)
    return comprobantes

def lista_detalles(comprobantes):
    """ Devuelve un listado de la tabla db.detalle
    ordenado según los comprobantes solicitados"""
    detalles = []
    for c in comprobantes:
        detallestmp = db(db.detalle.comprobante == c).select()
        for d in detallestmp: detalles.append(d)
    return detalles

def lista_compras(pedestal, umbral):
    """ Devuelve un listado de la tabla db.compra
    ordenado según el período solicitado """
    compras = db(db.compra).select()
    return compras

def lista_tributos(comprobantes):
    """ Devuelve un listado de la tabla db.compra
    ordenado según el período solicitado """
    tributos = []
    for c in comprobantes:
        tributostmp = db(db.detalletributo.comprobante == c).select()
        for t in tributostmp: tributos.append(t)
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
    
    def __init__(self, pedestal, umbral, comprobantes = None,
    compras = None, archivos = None, variables = None, detalles = None,
    tributos = None):
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
        # objeto para referencia en modelos
        self.obj = None
        # valores parciales para cálculo de informes
        self.parcial_neto = self.parcial_op_ex \
        = self.parcial_conc = self.parcial_liq = 0
        self.errores = []

    def crear_informe(self, nombre):
        contador = 0
        for tr in self.TIPOS_DE_REGISTRO[nombre]:
            self.modelo[nombre][tr] = self.crear_registro(
            os.path.join(self.archivos["CARPETA_DUPLICADOS"], self.archivos["modelo"][nombre][tr]))
            if self.BUCLE[nombre][tr]:
                for ol in self.listas[self.BUCLE[nombre][tr]]:
                    contador +=1
                    self.obj = ol
                    self.registros[nombre][tr][contador] = self.modelo[nombre][tr].copy()
                    self.registros[nombre][tr][contador] = self.procesar_registro(nombre, tr,
                    registro = self.registros[nombre][tr][contador], contador = contador)
            else:
                # 1: Recuperar formato de registro (modelo REGISTRO_CABECERA_2)
                # desde el archivo .csv
                # A: Crear un registro_cabecera_2
                # B: Actualizar el valor de cada campo validando el formato
                self.registros[nombre][tr] = self.modelo[nombre][tr].copy()
                self.registros[nombre][tr] = self.procesar_registro(nombre, tr,
                registro = self.registros[nombre][tr])

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
    contador = None):
        # procesar registro
        camponro = None
        try:
            for k, v in registro.iteritems():
                camponro = v[0]
                registro[k] = self.procesar_campo(campo = v)

        except self.ERRORES_CAMPOS, e:
            self.errores.append([nombre, tipo, contador, camponro, str(e)])

        # fin de procesar registro
        return registro
        
    def procesar_campo(self, campo = None):
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
            valtmp = sum([float(valor) for valor in val if type(valor) in [int, float, long]], 0.00)
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
        except (ValueError, TypeError):
            """ TODO: manejo de errores de cálculo"""
            pass
        return imp

    def fecha(self, f):
        try:
            f = int(f.strftime("%Y%m&d"))
        except self.ERRORES_CAMPOS, e:
            f = 0
        return f

    def cae(self, c):
        try:
            l = long(c.replace("|", ""))
        except self.ERRORES_CAMPOS, e:
            l = "0"
        return l

def informe():
    registros = 0
    nombre = request.args[0]
    periodo = int(request.args[1])
    mes =  int(request.args[2])
    pedestal = datetime.date(periodo, mes, 1)
    umbral = datetime.date(periodo, mes, calendar.monthrange(periodo,
    mes)[1])
    texto = None

    comprobantes = lista_comprobantes(pedestal, umbral)
    tributos = lista_tributos(comprobantes)
    detalles = lista_detalles(comprobantes)
    compras = lista_compras(pedestal, umbral)

    isr = Sired(pedestal, umbral, comprobantes = comprobantes, compras = compras,
    variables = db(db.variables).select().first(), archivos = ARCHIVOS,
    detalles = detalles, tributos = tributos)
    isr.crear_informe(nombre)
    texto = isr.convertir(nombre)
    registros = len(texto.splitlines())
        
    return dict(errores = isr.errores, nombre = nombre, registros = registros,
    texto = TEXTAREA(texto, _class="duplicado"))
    

    