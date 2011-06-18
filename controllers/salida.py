# -*- coding: utf-8 -*-
# intente algo como

import os

WSDESC = {"wsmtxca": u"Exportación", "wsfev1": "Mercado interno", "wsfex": u"Factura electrónica MTXCA", "wsbfe": "Bonos fiscales"}

def utftolatin(text):
    try:
        return unicode(text, "utf-8").encode("latin-1")
    except TypeError:
        # None es ""
        return ""

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
    
    titulo = utftolatin(db.tipocbte[comprobante.tipocbte].ds) + " " + str(comprobante.cbte_nro) + " - " + "Punto de venta " + str(comprobante.punto_vta)
    
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
        
    # pdf.write_html(utftolatin(XML(CENTER(chart), sanitize=False)))
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


# fpdf demo
def crear_factura_base():
    from gluon.contrib.pyfpdf.template import Template

    mensaje = ""
    # Si no se creó la demo agregar a la base de datos
    template = db(db.pdftemplate.title == "Demo invoice pyfpdf").select().first()

    if not template:
        template = db.pdftemplate.insert(title="Demo invoice pyfpdf", format = "A4")
        mensaje += "Se creó el template por defecto. "
        
    else:
        mensaje += "El template ya existe en la base de datos. "

    # eliminar todos los elementos del template por defecto.
    db(db.pdfelement.pdftemplate == template.id).delete()

    f = Template()
    f.parse_csv(infile=os.path.join(request.env.web2py_path,'applications', request.application, 'private', 'invoice.csv'), delimiter=";", decimal_sep=",")
    nro = 0
    creados = 0
    for k, v in f.elements.items():
        nro += 1
        try:
            v['align']= {'I':'L','D':'R','C':'C','J':'J',"":""}.get(v['align'], 'L')
            v['pdftemplate'] = template.id
            db.pdfelement.insert(**v)
            creados += 1

        except (AttributeError, ValueError, KeyError, TypeError), e:
            mensaje += "Error en elemento nro: " + str(nro) + " - " + str(e) + ". "

    mensaje += "Se crearon %s elementos" % str(creados)

    return dict(mensaje = mensaje)


def invoice():
    from gluon.contrib.pyfpdf import Template
    import os.path

    # generate sample invoice (according Argentina's regulations)

    el_cbte = db.comprobante[request.args[1]]
    los_detalles = db(db.detalle.comprobante == el_cbte.id).select()
    las_variables = db(db.variables).select().first()
    
    import random
    from decimal import Decimal

    # read elements from db
    template = db(db.pdftemplate.title == "Demo invoice pyfpdf").select().first()
    elements = db(db.pdfelement.pdftemplate==template.id).select(orderby=db.pdfelement.priority)

    f = Template(format="A4",
             elements = elements,
             title=utftolatin(el_cbte.nombre_cliente), author=utftolatin(las_variables.empresa),
             subject=utftolatin(db.tipocbte[el_cbte.tipocbte].ds), keywords="Electronic TAX Invoice")

    if el_cbte.obs_comerciales:
        detail = el_cbte.obs_comerciales
    else:
        detail = ""
        
    items = []

    i = 0
    
    for detalle in los_detalles:
        i += 1
        ds = utftolatin(detalle.ds)
        qty = str(detalle.qty)
        price = str(detalle.precio)
        code = str(detalle.codigo)
        items.append(dict(code=code, unit=str(detalle.umed.ds[:1]),
                          qty=qty, price=price,
                          amount=str(detalle.imp_total),
                          ds="%s: %s" % (i,ds)))

    # divide and count lines
    lines = 0
    li_items = []

    unit = qty = code = None

    for it in items:
        qty = it['qty']
        code = it['code']
        unit = it['unit']
        for ds in f.split_multicell(it['ds'], 'item_description01'):
            # add item description line (without price nor amount)
            li_items.append(dict(code=code, ds=ds, qty=qty, unit=unit, price=None, amount=None))
            # clean qty and code (show only at first)
            unit = qty = code = None
        # set last item line price and amount
        li_items[-1].update(amount = it['amount'],
                            price = it['price'])

    obs="\n<U>Detalle:</U>\n\n" + detail
    for ds in f.split_multicell(obs, 'item_description01'):
        li_items.append(dict(code=code, ds=ds, qty=qty, unit=unit, price=None, amount=None))

    # calculate pages:
    lines = len(li_items)
    max_lines_per_page = 24
    pages = lines / (max_lines_per_page - 1)
    if lines % (max_lines_per_page - 1): pages = pages + 1

    # completo campos y hojas
    for page in range(1, pages+1):
        f.add_page()
        f['page'] = u'Página %s de %s' % (page, pages)
        if pages>1 and page<pages:
            s = u'Continúa en la página %s' % (page+1)
        else:
            s = ''
        f['item_description%02d' % (max_lines_per_page+1)] = s

        

        try:
            if not las_variables.logo:
                logo = os.path.join(request.env.web2py_path,"applications",request.application,"static","images", "logo_fpdf.png")

            else:
                # path al logo
                logo = os.path.join(request.env.web2py_path,"applications",request.application,"uploads", las_variables.logo)

        except (AttributeError, ValueError, KeyError, TypeError):
            logo = os.path.join(request.env.web2py_path,"applications",request.application,"static","images", "logo_fpdf.png")



        f["company_name"] = utftolatin(las_variables.empresa)
        f["company_logo"] = logo
        f["company_header1"] = utftolatin(las_variables.domicilio)
        f["company_header2"] = "CUIT " + str(las_variables.cuit)
        f["company_footer1"] = utftolatin(el_cbte.tipocbte.ds)
        
        try:
            f["company_footer2"] = WSDESC[el_cbte.webservice]
        except KeyError:
            f["company_footer2"] = u"Factura electrónica"
            
        f['number'] = str(el_cbte.punto_vta).zfill(4) + "-" + str(el_cbte.cbte_nro).zfill(7)
        f['payment'] = utftolatin(el_cbte.forma_pago)
        f['document_type'] = el_cbte.tipocbte.ds[-1:]

        try:
            cae = str(el_cbte.cae)
            if cae == "None": cae = "0000000000"
            elif "|" in cae: cae = cae.strip("|")
            f['barcode'] = cae
            f['barcode_readable'] = "CAE: " + cae
        except (TypeError, ValueError, KeyError, AttributeError):
            f['barcode'] = "0000000000"
            f['barcode_readable'] = u"CAE: no registrado" 
            
        try:
            issue_date = el_cbte.fecha_cbte.strftime("%d-%m-%Y")
        except (TypeError, AttributeError):
            issue_date = ""

        try:
            due_date = el_cbte.fecha_vto.strftime("%d-%m-%Y")
        except (TypeError, AttributeError):
            due_date = ""
            
        f['issue_date'] = issue_date
        
        f['due_date'] = due_date

        f['customer_name'] = utftolatin(el_cbte.nombre_cliente)
        f['customer_address'] = utftolatin(el_cbte.domicilio_cliente)
        f['customer_vat'] = utftolatin(el_cbte.cp_cliente)
        f['customer_phone'] = utftolatin(el_cbte.telefono_cliente)
        f['customer_city'] = utftolatin(el_cbte.localidad_cliente)
        f['customer_taxid'] = utftolatin(el_cbte.nro_doc)

        # print line item...
        li = 0
        k = 0
        total = Decimal("0.00")
        for it in li_items:
            k = k + 1
            if k > page * (max_lines_per_page - 1):
                break
            if it['amount']:
                total += Decimal("%.6f" % float(it['amount']))
            if k > (page - 1) * (max_lines_per_page - 1):
                li += 1
                if it['qty'] is not None:
                    f['item_quantity%02d' % li] = it['qty']
                if it['code'] is not None:
                    f['item_code%02d' % li] = it['code']
                if it['unit'] is not None:
                    f['item_unit%02d' % li] = it['unit']
                f['item_description%02d' % li] = it['ds']
                if it['price'] is not None:
                    f['item_price%02d' % li] = "%0.3f" % float(it['price'])
                if it['amount'] is not None:
                    f['item_amount%02d' % li] = "%0.2f" % float(it['amount'])

        if pages == page:
            f['net'] = "%0.2f" % (total/Decimal("1.21"))
            f['vat'] = "%0.2f" % (total*(1-1/Decimal("1.21")))
            f['total_label'] = 'Total:'
        else:
            f['total_label'] = 'SubTotal:'
        f['total'] = "%0.2f" % float(total)

    response.headers['Content-Type']='application/pdf'
    return f.render('invoice.pdf', dest='S')
