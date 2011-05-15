# coding: utf8
# intente algo como

@auth.requires_login()
def index(): return dict(message="hello from abm.py")


@auth.requires(auth.has_membership('administrador') or auth.has_membership('emisor'))
def detalleeditar():
    return dict(form = crud.update(db.detalle, request.args[0]))
