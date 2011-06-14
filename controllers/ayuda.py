# coding: utf8
# intente algo como

def index():
    try:
        articulo = request.args[0]
    except (ValueError, KeyError, TypeError, IndexError, AttributeError):
        articulo = "inicio"
        request.flash = "No se encontró el artículo"
    return dict(articulo=articulo)

def inicio():
    return dict()

def configuracion():
    return dict()

def emision():
    return dict()
