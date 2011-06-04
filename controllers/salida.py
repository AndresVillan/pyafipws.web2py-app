# -*- coding: utf-8 -*-
# intente algo como

import os

def crear_pdf(comprobante):
    """ pdf básico con el detalle del comprobante para la demo """
    pdf = None

    if comprobante:
        detalles = db(db.detalle.comprobante == comprobante.id).select()
        tributos = db(db.detalletributo.comprobante == comprobante.id).select()
        asociados = db(db.comprobanteasociado.comprobante == comprobante.id).select()
        permisos = db(db.permiso.comprobante == comprobante.id).select()
    
    else:
        return None
    
    titulo = str(db.tipocbte[comprobante.tipocbte].ds) + " " + str(comprobante.cbte_nro) + " - " + "Punto de venta " + str(comprobante.punto_vta)
    
    # include a google chart (download it dynamically!)
    # url = "http://chart.apis.google.com/chart?cht=p3&chd=t:60,40&chs=500x200&chl=Hello|World&.png"
    # chart = IMG(_src=url, _width="250",_height="100")
    
    tablas = []

    if len(detalles) > 0:
        # create a small table with some data:
        rows = (THEAD(TR(TH("COD",_width="10%"), TH("CANT",_width="10%"), \
        TH("DESCRIPCION",_width="60%"), TH("PRECIO",_width="10%"), \
        TH("IVA",_width="10%"))), TBODY([TR(TD(d.codigo),TD(d.qty), \
        TD(d.ds),TD(d.precio),TD(d.iva.ds)) for d in detalles]))
        tablas.append((H3("Detalles del cbte"), TABLE(rows, _border="0", _align="center", _width="90%")))

    if len(asociados) > 0:
        # create a small table with some data:
        rows = (THEAD(TR(TH("A",_width="10%"), TH("B",_width="10%"), TH("C",_width="60%"), TH("D",_width="10%"), TH("E",_width="10%"))),
        TBODY([TR(TD(p.id),TD(p.id),TD(p.id),TD(p.id),TD(p.id)) for p in asociados]))
        
        tablas.append((H3("Cbtes, asociados"), TABLE(rows, _border="0", _align="center", _width="50%")))

    if len(permisos) > 0:
        # create a small table with some data:
        rows = (THEAD(TR(TH("A",_width="10%"), TH("B",_width="10%"), TH("C",_width="60%"), TH("D",_width="10%"), TH("E",_width="10%"))),
        TBODY([TR(TD(p.id),TD(p.id),TD(p.id),TD(p.id),TD(p.id)) for p in permisos]))
            
        tablas.append((H3("Permisos"), TABLE(rows, _border="0", _align="center", _width="90%")))

    if len(tributos) > 0:
        # create a small table with some data:
        rows = (THEAD(TR(TH("A",_width="10%"), TH("B",_width="10%"), TH("C",_width="60%"), TH("D",_width="10%"), TH("E",_width="10%"))),
        TBODY([TR(TD(p.id),TD(p.id),TD(p.id),TD(p.id),TD(p.id)) for p in tributos]))
            
        tablas.append((H3("Tributos"), TABLE(rows, _border="0", _align="center", _width="90%")))

    
    from gluon.contrib.pyfpdf import FPDF, HTMLMixin
    # create a custom class with the required functionalities 
    class MyFPDF(FPDF, HTMLMixin):
        def header(self): 
            "hook to draw custom page header (logo and title)"
            # logo=os.path.join(request.env.web2py_path,"gluon","contrib","pyfpdf","tutorial","logo_pb.png")
            # self.image(logo,10,8,33)
            
            # self.set_font('Arial','B',15)
            # self.cell(30) # padding
            # self.cell(50,20,response.title,0,0,'C')
            # self.ln(20)
               
        def footer(self):
            "hook to draw custom page footer (printing page numbers)"
            self.set_y(-15)
            self.set_font('Arial','I',8)
            txt = 'Page %s of %s' % (self.page_no(), self.alias_nb_pages())
            self.cell(0,10,txt,0,0,'C')
                    
    pdf=MyFPDF()
    # create a page and serialize/render HTML objects
    for t in tablas:
        pdf.add_page()
        pdf.write_html(str(XML(DIV(H1("FacturaLibre")), sanitize=False)))
        pdf.write_html(str(XML(DIV(H1(titulo)), sanitize=False)))            
        pdf.write_html(str(XML(DIV(t[0], t[1]), sanitize=False)))
        # 
        
    pdf.write_html(str(XML(P("Importe total: $" + str(comprobante.imp_total)), sanitize=False)))
        
    # pdf.write_html(str(XML(CENTER(chart), sanitize=False)))
    # prepare PDF to download:

    return pdf


@auth.requires_login()
def comprobante():
    # tomado de demo report copyright proyecto pyfpdf http://code.google.com/p/pyfpdf/
    try:
        cbte = int(request.vars.cbte)
    except (AttributeError, KeyError, ValueError):
        cbte = None
    comprobante = db(db.comprobante.id == cbte).select().first()
    if not comprobante:
        raise HTTP(500, "Comprobante inexistente")

    else:
        pdf = crear_pdf(comprobante)
    
    response.headers['Content-Type']='application/pdf'
    return pdf.output(dest='S')
    
        

@auth.requires(auth.has_membership('administrador') or auth.has_membership('emisor'))        
def guardar_comprobante():
    COMPROBANTES_PATH = os.path.join(request.env.web2py_path,'applications',request.application,'private', 'comprobantes')  
    # tomado de demo report copyright proyecto pyfpdf http://code.google.com/p/pyfpdf/
    comprobante = db(db.comprobante.id == request.args[0]).select().first()
    if not comprobante:
        raise HTTP(500, "Comprobante inexistente")
    else:
        pdf = crear_pdf(comprobante)
      
    archivo = open(COMPROBANTES_PATH + "/" + str(comprobante.id) + ".pdf", "w")
    archivo.write(pdf.output(dest='S'))
    archivo.close()
    
    return dict(mensaje = "Se guardó el archivo " + str(comprobante.id) + ".pdf" )
