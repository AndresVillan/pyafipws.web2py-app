# -*- coding: utf-8 -*-

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

@auth.requires_login()
def index(): return dict(message="Altas Bajas y Modificaciones")


@auth.requires(auth.has_membership('administrador') or auth.has_membership('emisor'))
def detalleeditar():
    return dict(form = crud.update(db.detalle, request.args[0]))

@auth.requires(auth.has_membership('administrador') or auth.has_membership('emisor'))
def data():
    form = None
    next = None
    admin = False
    # permitir opciones de cbte (reproceso, impresión)
    opciones = False
    cbte_id = None
    
    if auth.has_membership('administrador'): admin = True

    try:
        next = URL(r=request, c="consultas", f="consulta", vars={"table": request.args[1]})
        if request.args[0] == "read":
            form = crud.read(db[request.args[1]], request.args[2])
            opciones = True
            cbte_id = request.args[2]
            
        elif request.args[0] == "update":
            if admin:
                form = crud.update(db[request.args[1]], request.args[2], next = next)
            else:
                response.flash = "Se deshabilitó la función modificar registro (Requiere usuario administrador)."
        elif request.args[0] == "create":
            form = crud.create(db[request.args[1]], next = next)

            
    except (KeyError, TypeError, IndexError, AttributeError):
        response.flash = "No se pudo procesar la solicitud"
    return dict(form = form, opciones = opciones, cbte_id = cbte_id)
