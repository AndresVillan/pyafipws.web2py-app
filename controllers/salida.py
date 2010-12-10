# coding: utf8
# intente algo como

def pdf():
    from gluon.contrib.pyfpdf import Template
    import os.path
    
    # generate sample invoice (according Argentina's regulations)

    from decimal import Decimal

    # read elements from db 
    
    elements = db(db.pdf_element.pdf_template_id==1).select(orderby=db.pdf_element.priority)

    f = Template(format="A4",
             elements = elements,
             title="Sample Invoice", author="Sample Company",
             subject="Sample Customer", keywords="Electronic TAX Invoice")
    
    comprobante_id = request.args[0]
    comprobante = db(db.comprobante.id==comprobante_id).select().first()
    detalles = db(db.detalle.comprobante_id==comprobante_id).select()
        
    # create some random invoice line items and detail data
    items = []
    for detalle in detalles:
        ds = detalle.ds
        qty = detalle.qty
        price = detalle.precio
        code = detalle.codigo or ''
        items.append(dict(code=code, unit='u',
                          qty=qty, price=price, 
                          amount=qty*price,
                          ds=ds))

    # divide and count lines
    lines = 0
    li_items = []
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

    # split detail into each line description
    if comprobante.obs:
        obs="\n<U>Detail:</U>\n\n" + comprobante.obs
        for ds in f.split_multicell(obs, 'item_description01'):
            li_items.append(dict(code=code, ds=ds, qty=qty, unit=unit, price=None, amount=None))
    
    # calculate pages:
    lines = len(li_items)
    max_lines_per_page = 24
    pages = lines / (max_lines_per_page - 1)
    if lines % (max_lines_per_page - 1): pages = pages + 1

    # fill placeholders for each page
    for page in range(1, pages+1):
        f.add_page()
        f['page'] = 'Página %s de %s' % (page, pages)
        if pages>1 and page<pages:
            s = 'Continua en página %s' % (page+1)
        else:
            s = ''
        f['item_description%02d' % (max_lines_per_page+1)] = s

        f["company_name"] = "Sample Company"
        f["company_logo"] = os.path.join(request.env.web2py_path,"applications",request.application,"static","images","sistemas-agiles.png")
        f["company_header1"] = "Some Address - somewhere -"
        f["company_header2"] = "http://www.example.com"        
        f["company_footer1"] = "Tax Code ..."
        f["company_footer2"] = "Tax/VAT ID ..."
        f['number'] = '%04d-%08d' % (comprobante.punto_vta, comprobante.cbte_nro)
        f['issue_date'] = comprobante.fecha_cbte
        f['due_date'] = comprobante.fecha_venc_pago or ''
        f['customer_name'] = comprobante.nombre_cliente
        f['customer_address'] = comprobante.domicilio_cliente
       
        # print line item...
        li = 0 
        k = 0
        total = Decimal("0.00")
        for it in li_items:
            k = k + 1
            if k > page * (max_lines_per_page - 1):
                break
            if it['amount']:
                total += Decimal("%.6f" % it['amount'])
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
                    f['item_price%02d' % li] = "%0.3f" % it['price']
                if it['amount'] is not None:
                    f['item_amount%02d' % li] = "%0.2f" % it['amount']

        # last page? print totals:
        if pages == page:
            f['net'] = "%0.2f" % (total/Decimal("1.21"))
            f['vat'] = "%0.2f" % (total*(1-1/Decimal("1.21")))
            f['total_label'] = 'Total:'
        else:
            f['total_label'] = 'SubTotal:'
        f['total'] = "%0.2f" % total

    response.headers['Content-Type']='application/pdf'
    return f.render('invoice.pdf', dest='S')
