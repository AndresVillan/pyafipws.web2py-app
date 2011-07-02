# -*- coding: utf-8 -*- 

#########################################################################
## This scaffolding model makes your app work on Google App Engine too
#########################################################################

if request.env.web2py_runtime_gae:            # if running on Google App Engine
    db = DAL('gae')                           # connect to Google BigTable
    session.connect(request, response, db = db) # and store sessions and tickets there
    ### or use the following lines to store sessions in Memcache
    # from gluon.contrib.memdb import MEMDB
    # from google.appengine.api.memcache import Client
    # session.connect(request, response, db = MEMDB(Client()))
else:                                         # else use a normal relational database
    db = DAL('sqlite://storage.sqlite')       # if not, use SQLite or other DB

## if no need for session
# session.forget()

#########################################################################
## Here is sample code if you need for 
## - email capabilities
## - authentication (registration, login, logout, ... )
## - authorization (role based authorization)
## - services (xml, csv, json, xmlrpc, jsonrpc, amf, rss)
## - crud actions
## (more options discussed in gluon/tools.py)
#########################################################################

from gluon.tools import *
mail = Mail()                                  # mailer
auth = Auth(globals(),db)                      # authentication/authorization
crud = Crud(globals(),db)                      # for CRUD helpers using auth
service = Service(globals())                   # for json, xml, jsonrpc, xmlrpc, amfrpc

# mail.settings.server = 'logging' or 'smtp.gmail.com:587'  # your SMTP server
mail.settings.server = 'smtp.example.com:587'  # your SMTP server
mail.settings.sender = 'usuario@example.com'         # your email
mail.settings.login = 'usuario:contraseña'      # your credentials or None

auth.settings.hmac_key = 'sha512:47d8493b-63b7-4bce-b08c-4b467074acc4'   # before define_tables()
auth.define_tables()                           # creates all needed tables
auth.settings.mailer = mail                    # for user email verification
auth.settings.registration_requires_verification = False
auth.settings.registration_requires_approval = False
auth.messages.verify_email = 'Click on the link http://'+request.env.http_host+URL(r=request,c='default',f='user',args=['verify_email'])+'/%(key)s to verify your email'
auth.settings.reset_password_requires_verification = True
auth.messages.reset_password = 'Click on the link http://'+request.env.http_host+URL(r=request,c='default',f='user',args=['reset_password'])+'/%(key)s to reset your password'

#########################################################################
## If you need to use OpenID, Facebook, MySpace, Twitter, Linkedin, etc.
## register with janrain.com, uncomment and customize following
# from gluon.contrib.login_methods.rpx_account import RPXAccount
# auth.settings.actions_disabled=['register','change_password','request_reset_password']
# auth.settings.login_form = RPXAccount(request, api_key='...',domain='...',
#    url = "http://localhost:8000/%s/default/user/login" % request.application)
## other login methods are in gluon/contrib/login_methods
#########################################################################

crud.settings.auth = None                      # =auth to enforce authorization on crud

#########################################################################
## Define your tables below (or better in another model file) for example
##
## >>> db.define_table('mytable',Field('myfield','string'))
##
## Fields can be 'string','text','password','integer','double','boolean'
##       'date','time','datetime','blob','upload', 'reference TABLENAME'
## There is an implicit 'id integer autoincrement' field
## Consult manual for more options, validators, etc.
##
## More API examples for controllers:
##
## >>> db.mytable.insert(myfield='value')
## >>> rows=db(db.mytable.myfield=='value').select(db.mytable.ALL)
## >>> for row in rows: print row.id, row.myfield
#########################################################################

# función que controla el evento de autenticación
def autenticacion_usuario(form):
    try:
        user_id = db(db.auth_user.email == form.vars.email).select().first().id
    except (AttributeError, KeyError, ValueError):
        user_id = None

    if user_id != None:
        # si es un usuario nuevo crear variables y asociar como invitado
        if db(db.variablesusuario.usuario == user_id).select().first() == None:
            variables = db(db.variables).select().first()
            if variables != None:
                db.variablesusuario.insert(\
                usuario = user_id, puntodeventa = variables.puntodeventa, \
                moneda = variables.moneda, webservice = variables.webservice, \
                tipocbte = variables.tipocbte \
                )
        
        grupos_usuario = db(db.auth_membership.user_id == user_id).select()
        if len(grupos_usuario) < 2:
            # no se asoció el usuario a grupos de facturalibre
            grupo_emis = db(db.auth_group.role == "emisor").select().first()
            if grupo_emis != None:
                db.auth_membership.insert(user_id = user_id, group_id = grupo_emis.id)
        
    return None
    
auth.settings.login_onaccept = autenticacion_usuario
auth.settings.register_onaccept = autenticacion_usuario

# dirigir las consultas crud a abm.py
crud.settings.controller = "abm"

# webgrid
webgrid = local_import('webgrid')
