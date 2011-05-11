# coding: utf8
# intente algo como
def index(): return dict(message="hello from abm.py")

def detalleeditar():
    return dict(form = crud.update(db.detalle, request.args[0]))
