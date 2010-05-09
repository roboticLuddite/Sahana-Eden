# -*- coding: utf-8 -*-

"""
    CRUD+LSO Method Handlers (Frontend for S3REST)

    @author: Fran Boon
    @author: nursix

    @see: U{http://trac.sahanapy.org/wiki/RESTController}

    HTTP Status Codes: http://www.w3.org/Protocols/rfc2616/rfc2616-sec10.html
"""

# *****************************************************************************
# Constants to ensure consistency

# XSLT Settings
XSLT_FILE_EXTENSION = 'xsl' #: File extension of XSLT templates
XSLT_IMPORT_TEMPLATES = 'static/xslt/import' #: Path to XSLT templates for data import
XSLT_EXPORT_TEMPLATES = 'static/xslt/export' #: Path to XSLT templates for data export

# XSLT available formats
shn_xml_import_formats = ["xml", "lmx", "osm", "pfif", "ushahidi"] #: Supported XML import formats
shn_xml_export_formats = dict(
    xml = "application/xml",
    gpx = "application/xml",
    lmx = "application/xml",
    pfif = "application/xml",
    have = "application/xml",
    osm = "application/xml",
    georss = "application/rss+xml",
    kml = "application/vnd.google-earth.kml+xml"
) #: Supported XML output formats and corresponding response headers

shn_json_import_formats = ["json"] #: Supported JSON import formats
shn_json_export_formats = dict(
    json = "text/x-json",
    geojson = "text/x-json"
) #: Supported JSON output formats and corresponding response headers

# Error messages
UNAUTHORISED = T('Not authorised!')
BADFORMAT = T('Unsupported data format!')
BADMETHOD = T('Unsupported method!')
BADRECORD = T('Record not found!')
INVALIDREQUEST = T('Invalid request!')

# How many rows to show per page in list outputs
ROWSPERPAGE = 20
PRETTY_PRINT = True

# *****************************************************************************
# Load Controllers

exec('from applications.%s.modules.s3xrc import *' % request.application)
exec('from applications.%s.modules.s3rest import *' % request.application)
# Faster for Production (where app-name won't change):
#from applications.sahana.modules.s3xrc import *
#from applications.sahana.modules.s3rest import *

s3xrc = ResourceController(db,
                           domain=request.env.server_name,
                           base_url="%s/%s" % (S3_PUBLIC_URL, request.application),
                           rpp=ROWSPERPAGE,
                           gis=gis)

s3rest = RESTController(rc=s3xrc, auth=auth,
    xml_import_formats = shn_xml_import_formats,
    xml_export_formats = shn_xml_export_formats,
    json_import_formats = shn_json_import_formats,
    json_export_formats = shn_json_export_formats)

# *****************************************************************************
def shn_field_represent(field, row, col):

    """
        Representation of a field
        Used by:
         * export_xls()
         * shn_list()
           .aaData representation for dataTables' Server-side pagination
    """

    # TODO: put this function into XRequest

    try:
        represent = str(field.represent(row[col]))
    except:
        if row[col] is None:
            represent = "None"
        else:
            represent = row[col]
    return represent

def shn_field_represent_sspage(field, row, col, linkto=None):

    """ Represent columns in SSPage responses """

    # TODO: put this function into XRequest

    if col == 'id':
        id = str(row[col])
        # Remove SSPag variables, but keep 'next':
        next = request.vars.next
        request.vars = Storage(next=next)
        # use linkto to produce ID column links:
        try:
            href = linkto(id)
        except TypeError:
            href = linkto % id
        # strip away '.aaData' extension => dangerous!
        href = str(href).replace('.aaData', '')
        href = str(href).replace('.aadata', '')
        return A( shn_field_represent(field, row, col), _href=href).xml()
    else:
        return shn_field_represent(field, row, col)

# *****************************************************************************
# Exports

#
# export_csv ------------------------------------------------------------------
#
def export_csv(resource, query, record=None):

    """ Export record(s) as CSV """

    import gluon.contenttype
    response.headers['Content-Type'] = gluon.contenttype.contenttype('.csv')
    if record:
        filename = "%s_%s_%d.csv" % (request.env.server_name, resource, record)
    else:
        # List
        filename = "%s_%s_list.csv" % (request.env.server_name, resource)
    response.headers['Content-disposition'] = "attachment; filename=%s" % filename
    return str(db(query).select())

#
# export_pdf ------------------------------------------------------------------
#
def export_pdf(table, query):

    """ Export record(s) as Adobe PDF """

    try:
        from reportlab.lib.units import cm
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.enums import TA_CENTER, TA_RIGHT
    except ImportError:
        session.error = T('ReportLab module not available within the running Python - this needs installing for PDF output!')
        redirect(URL(r=request))
    try:
        from geraldo import Report, ReportBand, Label, ObjectValue, SystemField, landscape, BAND_WIDTH
        from geraldo.generators import PDFGenerator
    except ImportError:
        session.error = T('Geraldo module not available within the running Python - this needs installing for PDF output!')
        redirect(URL(r=request))

    objects_list = db(query).select(table.ALL)
    if not objects_list:
        session.warning = T('No data in this table - cannot create PDF!')
        redirect(URL(r=request))

    import StringIO
    output = StringIO.StringIO()

    fields = [table[f] for f in table.fields if table[f].readable]
    _elements = [SystemField(expression='%(report_title)s', top=0.1*cm,
                    left=0, width=BAND_WIDTH, style={'fontName': 'Helvetica-Bold',
                    'fontSize': 14, 'alignment': TA_CENTER})]
    detailElements = []
    COLWIDTH = 2.5
    LEFTMARGIN = 0.2
    for field in fields:
        _elements.append(Label(text=str(field.label)[:16], top=0.8*cm, left=LEFTMARGIN*cm))
        tab, col = str(field).split('.')
        #db[table][col].represent = 'foo'
        detailElements.append(ObjectValue(
            attribute_name=col,
            left=LEFTMARGIN*cm, width=COLWIDTH*cm,
            get_value=lambda instance: str(instance).decode('utf-8')))
        LEFTMARGIN += COLWIDTH

    mod, res = str(table).split('_', 1)
    mod_nice = db(db.s3_module.name==mod).select()[0].name_nice
    _title = mod_nice + ': ' + res.capitalize()

    class MyReport(Report):
        title = _title
        page_size = landscape(A4)
        class band_page_header(ReportBand):
            height = 1.3*cm
            auto_expand_height = True
            elements = _elements
            borders = {'bottom': True}
        class band_page_footer(ReportBand):
            height = 0.5*cm
            elements = [
                Label(text='%s' % request.utcnow.date(), top=0.1*cm, left=0),
                SystemField(expression='Page # %(page_number)d of %(page_count)d', top=0.1*cm,
                    width=BAND_WIDTH, style={'alignment': TA_RIGHT}),
            ]
            borders = {'top': True}
        class band_detail(ReportBand):
            height = 0.5*cm
            auto_expand_height = True
            elements = tuple(detailElements)
    report = MyReport(queryset=objects_list)
    report.generate_by(PDFGenerator, filename=output)

    output.seek(0)
    import gluon.contenttype
    response.headers['Content-Type'] = gluon.contenttype.contenttype('.pdf')
    filename = "%s_%s.pdf" % (request.env.server_name, str(table))
    response.headers['Content-disposition'] = "attachment; filename=\"%s\"" % filename
    return output.read()

#
# export_rss ------------------------------------------------------------------
#
def export_rss(module, resource, query, rss=None, linkto=None):

    """ Export record(s) as RSS feed """

    # This can not work when proxied through Apache (since it's always a local request):
    #if request.env.remote_addr == '127.0.0.1':
        #server = 'http://127.0.0.1:' + request.env.server_port
    #else:
        #server = 'http://' + request.env.server_name + ':' + request.env.server_port

    server = S3_PUBLIC_URL

    tablename = "%s_%s" % (module, resource)
    try:
        title_list = s3.crud_strings[tablename].subtitle_list
    except:
        title_list =  s3.crud_strings.subtitle_list

    if not linkto:
        link = '/%s/%s/%s' % (request.application, module, resource)
    else:
        link = linkto

    entries = []
    table = db[tablename]
    rows = db(query).select(table.ALL)
    if rows:
        for row in rows:
            if rss and 'title' in rss:
                try:
                    title = rss.get('title')(row)
                except TypeError:
                    title = rss.get('title') % row
            else:
                title = row['id']

            if rss and 'description' in rss:
                try:
                    description = rss.get('description')(row)
                except TypeError:
                    description = rss.get('description') % row
            else:
                description = ''

            entries.append(dict(
                title = str(title).decode('utf-8'),
                link = server + link + '/%d' % row.id,
                description = str(description).decode('utf-8'),
                modified_on = row.modified_on))

    import gluon.contrib.rss2 as rss2

    items = [rss2.RSSItem(
        title = entry['title'],
        link = entry['link'],
        description = entry['description'],
        pubDate = entry['modified_on']) for entry in entries]

    rss = rss2.RSS2(
        title = str(title_list).decode('utf-8'),
        link = server + link,
        description = '',
        lastBuildDate = request.utcnow,
        items = items)

    response.headers['Content-Type'] = 'application/rss+xml'
    return rss2.dumps(rss)

#
# export_xls ------------------------------------------------------------------
#
def export_xls(table, query, list_fields=None):

    """ Export record(s) as XLS """

    # TODO: make this function XRequest-aware

    try:
        import xlwt
    except ImportError:
        session.error = T('xlwt module not available within the running Python - this needs installing for XLS output!')
        redirect(URL(r=request))

    import StringIO
    output = StringIO.StringIO()

    items = db(query).select(table.ALL)

    book = xlwt.Workbook(encoding='utf-8')
    sheet1 = book.add_sheet(str(table))
    # Header row
    row0 = sheet1.row(0)
    cell = 0

    fields = None
    if list_fields:
        fields = [table[f] for f in list_fields if table[f].readable]
    if fields and len(fields)==0:
        fields.append(table.id)
    if not fields:
        fields = [table[f] for f in table.fields if table[f].readable]

    for field in fields:
        row0.write(cell, str(field.label), xlwt.easyxf('font: bold True;'))
        cell += 1
    row = 1
    style = xlwt.XFStyle()
    for item in items:
        # Item details
        rowx = sheet1.row(row)
        row += 1
        cell1 = 0
        for field in fields:
            tab, col = str(field).split('.')
            # Check for Date formats
            if db[tab][col].type == 'date':
                style.num_format_str = 'D-MMM-YY'
            elif db[tab][col].type == 'datetime':
                style.num_format_str = 'M/D/YY h:mm'
            elif db[tab][col].type == 'time':
                style.num_format_str = 'h:mm:ss'

            # Check for a custom.represent (e.g. for ref fields)
            represent = shn_field_represent(field, item, col)

            rowx.write(cell1, str(represent), style)
            cell1 += 1
    book.save(output)
    output.seek(0)
    import gluon.contenttype
    response.headers['Content-Type'] = gluon.contenttype.contenttype('.xls')
    filename = "%s_%s.xls" % (request.env.server_name, str(table))
    response.headers['Content-disposition'] = "attachment; filename=\"%s\"" % filename
    return output.read()

#
# export_json -----------------------------------------------------------------
#
def export_json(jr):

    """ Export data as JSON """

    try:
        response.headers['Content-Type'] = shn_json_export_formats[jr.representation]
    except:
        response.headers['Content-Type'] = "text/x-json"

    if jr.representation=="json":
        template = None
    else:
        template_name = "%s.%s" % (jr.representation, XSLT_FILE_EXTENSION)
        template = os.path.join(request.folder, XSLT_EXPORT_TEMPLATES, template_name)
        if not os.path.exists(template):
            session.error = str(T("XSLT Template Not Found: ")) + \
                            XSLT_EXPORT_TEMPLATES + "/" + template_name
            raise HTTP(501, body=json_message(False, 501, session.error))
            #redirect(URL(r=request, f="index"))

    output = jr.export_json(permit=shn_has_permission,
                            audit=shn_audit,
                            template=template,
                            pretty_print=PRETTY_PRINT,
                            filterby=response.s3.filter)

    if not output:
        session.error = str(T("XSLT Transformation Error: ")) + jr.error
        raise HTTP(400, body=json_message(False, 400, session.error))
        #redirect(URL(r=request, f="index"))

    return output

#
# export_xml ------------------------------------------------------------------
#
def export_xml(jr):

    """ Export data as XML """

    try:
        response.headers['Content-Type'] = shn_xml_export_formats[jr.representation]
    except:
        response.headers['Content-Type'] = "application/xml"

    if jr.representation=="xml":
        template = None
    else:
        template_name = "%s.%s" % (jr.representation, XSLT_FILE_EXTENSION)
        template = os.path.join(request.folder, XSLT_EXPORT_TEMPLATES, template_name)
        if not os.path.exists(template):
            session.error = str(T("XSLT Template Not Found: ")) + \
                            XSLT_EXPORT_TEMPLATES + "/" + template_name
            raise HTTP(501, body=json_message(False, 501, session.error))
            #redirect(URL(r=request, f="index"))

    output = jr.export_xml(permit=shn_has_permission,
                           audit=shn_audit,
                           template=template,
                           pretty_print=PRETTY_PRINT,
                           filterby=response.s3.filter)

    if not output:
        session.error = str(T("XSLT Transformation Error: ")) + (jr.error or '')
        raise HTTP(400, body=json_message(False, 400, session.error))
        #redirect(URL(r=request, f="index"))

    return output

# *****************************************************************************
# Imports

#
# import_csv ------------------------------------------------------------------
#
def import_csv(file, table=None):

    """ Import CSV file into Database """

    if table:
        table.import_from_csv_file(file)
    else:
        # This is the preferred method as it updates reference fields
        db.import_from_csv_file(file)
        db.commit()
#
# import_url ------------------------------------------------------------------
#
def import_url(jr, table, method, onvalidation=None, onaccept=None):

    """
        Import GET/URL vars into Database & respond in JSON,
        supported methods: 'create' & 'update'
    """

    record = Storage()
    uuid = None
    original = None

    module, resource, table, tablename = jr.target()

    if jr.component:
        onvalidation = s3xrc.model.get_attr(resource, "onvalidation")
        onaccept = s3xrc.model.get_attr(resource, "onaccept")

    response.headers['Content-Type'] = 'text/x-json'

    for var in request.vars:

        # Skip the Representation
        if var == 'format':
            continue
        elif var == 'uuid':
            uuid = request.vars[var]
        elif table[var].type == 'upload':
            # Handle file uploads (copied from gluon/sqlhtml.py)
            field = table[var]
            fieldname = var
            f = request.vars[fieldname]
            fd = fieldname + '__delete'
            if f == '' or f == None:
                #if request.vars.get(fd, False) or not self.record:
                if request.vars.get(fd, False):
                    record[fieldname] = ''
                else:
                    #record[fieldname] = self.record[fieldname]
                    pass
            elif hasattr(f,'file'):
                (source_file, original_filename) = (f.file, f.filename)
            elif isinstance(f, (str, unicode)):
                ### do not know why this happens, it should not
                (source_file, original_filename) = \
                    (cStringIO.StringIO(f), 'file.txt')
            newfilename = field.store(source_file, original_filename)
            request.vars['%s_newfilename' % fieldname] = record[fieldname] = newfilename
            if field.uploadfield and not field.uploadfield==True:
                record[field.uploadfield] = source_file.read()
        else:
            record[var] = request.vars[var]


    # UUID is required for update
    if method == 'update':
        if uuid:
            try:
                original = db(table.uuid==uuid).select(table.ALL)[0]
            except:
                raise HTTP(404, body=json_message(False, 404, "Record not found!"))
        else:
            # You will never come to that point without having specified a
            # record ID in the request. Nevertheless, we require a UUID to
            # identify the record
            raise HTTP(400, body=json_message(False, 400, "UUID required!"))

    # Validate record
    for var in record:
        if var in table.fields:
            value = record[var]
            (value, error) = s3xrc.xml.validate(table, original, var, value)
        else:
            # Shall we just ignore non-existent fields?
            # del record[var]
            error = "Invalid field name."
        if error:
            raise HTTP(400, body=json_message(False, 400, var + " invalid: " + error))
        else:
            record[var] = value

    form = Storage()
    form.method = method
    form.vars = record

    # Onvalidation callback
    if onvalidation:
        onvalidation(form)

    # Create/update record
    try:
        if jr.component:
            record[jr.fkey]=jr.record[jr.pkey]
        if method == 'create':
            id = table.insert(**dict(record))
            if id:
                error = 201
                item = json_message(True, error, "Created as " + str(jr.other(method=None, record_id=id)))
                form.vars.id = id
                if onaccept:
                    onaccept(form)
            else:
                error = 403
                item = json_message(False, error, "Could not create record!")

        elif method == 'update':
            result = db(table.uuid==uuid).update(**dict(record))
            if result:
                error = 200
                item = json_message(True, error, "Record updated.")
                form.vars.id = original.id
                if onaccept:
                    onaccept(form)
            else:
                error = 403
                item = json_message(False, error, "Could not update record!")

        else:
            error = 501
            item = json_message(False, error, "Unsupported Method!")
    except:
        error = 400
        item = json_message(False, error, "Invalid request!")

    raise HTTP(error, body=item)

# *****************************************************************************
# Authorisation

#
# shn_has_permission ----------------------------------------------------------
#
def shn_has_permission(name, table_name, record_id = 0):

    """
        S3 framework function to define whether a user can access a record in manner 'name'

        Designed to be called from the RESTlike controller

    """

    if session.s3.security_policy == 1:
        # Simple policy
        # Anonymous users can Read.
        if name == 'read':
            authorised = True
        else:
            # Authentication required for Create/Update/Delete.
            authorised = auth.is_logged_in() or auth.basic()
    else:
        # Full policy
        if auth.is_logged_in() or auth.basic():
            # Administrators are always authorised
            if auth.has_membership(1):
                authorised = True
            else:
                # Require records in auth_permission to specify access
                authorised = auth.has_permission(name, table_name, record_id)
        else:
            # No access for anonymous
            authorised = False
    return authorised

#
# shn_accessible_query --------------------------------------------------------
#
def shn_accessible_query(name, table):

    """
        Returns a query with all accessible records for the current logged in user

        @note: This method does not work on GAE because uses JOIN and IN

    """
    # If using the 'simple' security policy then show all records
    if session.s3.security_policy == 1:
        # simple
        return table.id > 0
    # Administrators can see all data
    if auth.has_membership(1):
        return table.id > 0
    # If there is access to the entire table then show all records
    try:
        user_id = auth.user.id
    except:
        user_id = 0
    if auth.has_permission(name, table, 0, user_id):
        return table.id > 0
    # Filter Records to show only those to which the user has access
    session.warning = T("Only showing accessible records!")
    membership = auth.settings.table_membership
    permission = auth.settings.table_permission
    return table.id.belongs(db(membership.user_id == user_id)\
                       (membership.group_id == permission.group_id)\
                       (permission.name == name)\
                       (permission.table_name == table)\
                       ._select(permission.record_id))

# *****************************************************************************
# Audit
#
# These functions should always return True in order to be chainable
# by 'and' for lambda's as onaccept-callbacks. -- nursix --

#
# shn_audit -------------------------------------------------------------------
#
def shn_audit(operation, module, resource, form=None, record=None, representation=None):

    #print "Audit: %s on %s_%s #%s" % (operation, module, resource, record or 0)

    if operation in ("list", "read"):
        return shn_audit_read(operation, module, resource,
                              record=record, representation=representation)
    elif operation=="create":
        return shn_audit_create(form, module, resource, representation=representation)

    elif operation=="update":
        return shn_audit_update(form, module, resource, representation=representation)

    elif operation=="delete":
        return shn_audit_create(module, resource, record, representation=representation)

    return True

#
# shn_audit_read --------------------------------------------------------------
#
def shn_audit_read(operation, module, resource, record=None, representation=None):

    """ Called during Read operations to enable optional Auditing """

    if session.s3.audit_read:
        db.s3_audit.insert(
                person = auth.user_id,
                operation = operation,
                module = module,
                resource = resource,
                record = record,
                representation = representation,
            )
    return True

#
# shn_audit_create ------------------------------------------------------------
#
def shn_audit_create(form, module, resource, representation=None):

    """
        Called during Create operations to enable optional Auditing

        Called as an onaccept so that it only takes effect when
        saved & can read the new values in::
            onaccept = lambda form: shn_audit_create(form, module, resource, representation)

    """

    if session.s3.audit_write:
        record =  form.vars.id
        new_value = []
        for var in form.vars:
            new_value.append(var + ':' + str(form.vars[var]))
        db.s3_audit.insert(
                person = auth.user_id,
                operation = 'create',
                module = module,
                resource = resource,
                record = record,
                representation = representation,
                new_value = new_value
            )
    return True

#
# shn_audit_update ------------------------------------------------------------
#
def shn_audit_update(form, module, resource, representation=None):

    """
        Called during Create operations to enable optional Auditing

        Called as an onaccept so that it only takes effect when
        saved & can read the new values in::
            onaccept = lambda form: shn_audit_update(form, module, resource, representation)

    """

    if session.s3.audit_write:
        record =  form.vars.id
        new_value = []
        for var in form.vars:
            new_value.append(var + ':' + str(form.vars[var]))
        db.s3_audit.insert(
                person = auth.user_id,
                operation = 'update',
                module = module,
                resource = resource,
                record = record,
                representation = representation,
                #old_value = old_value, # Need to store these beforehand if we want them
                new_value = new_value
            )
    return True

#
# shn_audit_update_m2m --------------------------------------------------------
#
def shn_audit_update_m2m(module, resource, record, representation=None):

    """
        Called during Update operations to enable optional Auditing
        Designed for use in M2M 'Update Qty/Delete' (which can't use crud.settings.update_onaccept)
        shn_audit_update_m2m(resource, record, representation)
    """

    if session.s3.audit_write:
        db.s3_audit.insert(
                person = auth.user_id,
                operation = 'update',
                module = module,
                resource = resource,
                record = record,
                representation = representation,
                #old_value = old_value, # Need to store these beforehand if we want them
                #new_value = new_value  # Various changes can happen, so would need to store dict of {item_id: qty}
            )
    return True

#
# shn_audit_delete ------------------------------------------------------------
#
def shn_audit_delete(module, resource, record, representation=None):

    """ Called during Delete operations to enable optional Auditing """

    if session.s3.audit_write:
        module = module
        table = '%s_%s' % (module, resource)
        old_value = []
        _old_value = db(db[table].id==record).select()[0]
        for field in _old_value:
            old_value.append(field + ':' + str(_old_value[field]))
        db.s3_audit.insert(
                person = auth.user_id,
                operation = 'delete',
                module = module,
                resource = resource,
                record = record,
                representation = representation,
                old_value = old_value
            )
    return True

# *****************************************************************************
# Display Representations

# t2.itemize now deprecated
# but still used for t2.search

#
# shn_represent ---------------------------------------------------------------
#
def shn_represent(table, module, resource, deletable=True, main='name', extra=None):

    """ Designed to be called via table.represent to make t2.search() output useful """

    db[table].represent = lambda table: \
                          shn_list_item(table, resource,
                                        action='display',
                                        main=main,
                                        extra=shn_represent_extra(table,
                                                                  module,
                                                                  resource,
                                                                  deletable,
                                                                  extra))
    return

#
# shn_represent_extra ---------------------------------------------------------
#
def shn_represent_extra(table, module, resource, deletable=True, extra=None):

    """ Display more than one extra field (separated by spaces)"""

    authorised = shn_has_permission('delete', table)
    item_list = []
    if extra:
        extra_list = extra.split()
        for any_item in extra_list:
            item_list.append("TD(db(db.%s_%s.id==%i).select()[0].%s)" % \
                             (module, resource, table.id, any_item))
    if authorised and deletable:
        item_list.append("TD(INPUT(_type='checkbox', _class='delete_row', _name='%s', _id='%i'))" % \
                         (resource, table.id))
    return ','.join( item_list )

#
# shn_list_item ---------------------------------------------------------------
#
def shn_list_item(table, resource, action, main='name', extra=None):

    """ Display nice names with clickable links & optional extra info """

    item_list = [TD(A(table[main], _href=URL(r=request, f=resource, args=[action, table.id])))]
    if extra:
        item_list.extend(eval(extra))
    items = DIV(TABLE(TR(item_list)))
    return DIV(*items)

#
# shn_custom_view -------------------------------------------------------------
#
def shn_custom_view(jr, default_name, format=None):

    """ Check for custom view """

    prefix = jr.request.controller

    if jr.component:

        custom_view = '%s_%s_%s' % (jr.name, jr.component_name, default_name)

        _custom_view = os.path.join(request.folder, 'views', prefix, custom_view)

        if not os.path.exists(_custom_view):
            custom_view = '%s_%s' % (jr.name, default_name)
            _custom_view = os.path.join(request.folder, 'views', prefix, custom_view)

    else:
        if format:
            custom_view = '%s_%s_%s' % (jr.name, default_name, format)
        else:
            custom_view = '%s_%s' % (jr.name, default_name)
        _custom_view = os.path.join(request.folder, 'views', prefix, custom_view)

    if os.path.exists(_custom_view):
        response.view = prefix + '/' + custom_view
    else:
        if format:
            response.view = default_name.replace('.html', '_%s.html' % format)
        else:
            response.view = default_name

#
# shn_convert_orderby ----------------------------------------------------------
#
def shn_get_columns(table):
    return [f for f in table.fields if table[f].readable]

def shn_convert_orderby(table, request, fields=None):
    cols = fields or shn_get_columns(table)

    def colname(i):
        return table._tablename + '.' + cols[int(request.vars['iSortCol_' + str(i)])]

    def rng():
        return xrange(0, int(request.vars['iSortingCols']))

    def direction(i):
        dir = 'sSortDir_' + str(i)
        if dir in request.vars:
            return ' ' + request.vars[dir]
        return ''

    return ', '.join([colname(i) + direction(i) for i in rng()])

#
# shn_build_ssp_filter --------------------------------------------------------
#
def shn_build_ssp_filter(table, request, fields=None):

    cols = fields or shn_get_columns(table)
    context = '%' + request.vars.sSearch + '%'
    context = context.lower()
    searchq = None

    # TODO: use FieldS3 (with representation_field)
    for i in xrange(0, int(request.vars.iColumns)):
        if table[cols[i]].type in ['string','text']:
            if searchq is None:
                searchq = table[cols[i]].lower().like(context)
            else:
                searchq = searchq | table[cols[i]].lower().like(context)
    return searchq

# *****************************************************************************
# REST Method Handlers
#
# These functions are to handle REST methods.
# Currently implemented methods are:
#
#   - import_json
#   - import_xml
#   - list
#   - read
#   - create
#   - update
#   - delete
#   - search
#   - options
#
# Handlers must be implemented as:
#
#   def method_handler(jr, **attr)
#
# where:
#
#   jr - is the XRequest
#   attr - attributes of the call, passed through
#

#
# import_json -----------------------------------------------------------------
#
def import_json(jr, **attr):

    #return json_message(False, 501, "Not implemented!")

    onvalidation = attr.get('onvalidation', None)
    onaccept = attr.get('onaccept', None)

    if "filename" in jr.request.vars:
        source = open(jr.request.vars["filename"])
    elif "fetchurl" in jr.request.vars:
        import urllib
        source = urllib.urlopen(jr.request.vars["fetchurl"])
    else:
        #from StringIO import StringIO
        #source = StringIO(jr.request.body)
        source = jr.request.body

    tree = s3xrc.xml.json2tree(source)

    if hasattr(source, "close"):
        source.close()

    # XSLT Transformation
    if not jr.representation=="json":
        template_name = "%s.%s" % (jr.representation, XSLT_FILE_EXTENSION)
        template_file = os.path.join(request.folder, XSLT_IMPORT_TEMPLATES, template_name)
        if os.path.exists(template_file):
            tree = s3xrc.xml.transform(tree, template_file, domain=s3xrc.domain, base_url=s3xrc.base_url)
            if not tree:
                session.error = str(T("XSL Transformation Error: ")) + str(s3xrc.xml.error)
                redirect(URL(r=request, f="index"))
        else:
            session.error = str(T("XSL Template Not Found: ")) + \
                            XSLT_IMPORT_TEMPLATES + "/" + template_name
            #redirect(URL(r=request, f="index"))
            item = json_message(False, 501, session.error)
            raise HTTP(501)

    # For testing:
    #print s3xrc.xml.tostring(tree)
    #return s3xrc.xml.tree2json(tree)

    success = jr.import_xml(tree,
                            permit=shn_has_permission,
                            audit=shn_audit,
                            onvalidation=onvalidation,
                            onaccept=onaccept)

    if success:
        item = json_message()
    else:
        # TODO: export the whole tree on error
        tree = s3xrc.xml.tree2json(tree)
        item = json_message(False, 400, s3xrc.xml.error, tree=tree)
        raise HTTP(400, body=item)

    return dict(item=item)

#
# import_xml ------------------------------------------------------------------
#
def import_xml(jr, **attr):

    """ Import XML data """

    onvalidation = attr.get('onvalidation', None)
    onaccept = attr.get('onaccept', None)

    if "filename" in jr.request.vars:
        source = jr.request.vars["filename"]
    elif "fetchurl" in jr.request.vars:
        source = jr.request.vars["fetchurl"]
    else:
        source = jr.request.body

    tree = s3xrc.xml.parse(source)
    
    # XSLT Transformation
    if not jr.representation=="xml":
        template_name = "%s.%s" % (jr.representation, XSLT_FILE_EXTENSION)
        template_file = os.path.join(request.folder, XSLT_IMPORT_TEMPLATES, template_name)
        if os.path.exists(template_file):
            tree = s3xrc.xml.transform(tree, template_file, domain=s3xrc.domain, base_url=s3xrc.base_url)
            if not tree:
                session.error = str(T("XSLT Transformation Error: ")) + str(s3xrc.xml.error)
                redirect(URL(r=request, f="index"))
        else:
            session.error = str(T("XSLT Template Not Found: ")) + \
                            XSLT_IMPORT_TEMPLATES + "/" + template_name
            #redirect(URL(r=request, f="index"))
            item = json_message(False, 501, session.error)
            raise HTTP(501)

    success = jr.import_xml(tree,
                            permit=shn_has_permission,
                            audit=shn_audit,
                            onvalidation=onvalidation,
                            onaccept=onaccept)

    if success:
        item = json_message()
    else:
        # TODO: export the whole tree on error
        tree = s3xrc.xml.tree2json(tree)
        item = json_message(False, 400, s3xrc.xml.error, tree=tree)
        raise HTTP(400, body=item)

    return dict(item=item)

#
# shn_read --------------------------------------------------------------------
#
def shn_read(jr, **attr):

    """ Read a single record. """

    onvalidation = attr.get('onvalidation', None)
    onaccept = attr.get('onaccept', None)
    pheader = attr.get('pheader', None)
    editable = attr.get('editable', True)
    deletable = attr.get('deletable', True)
    rss = attr.get('rss', None)

    # TODO: this function not filter-aware!

    module, resource, table, tablename = jr.target()

    if jr.component:

        query = ((table[jr.fkey]==jr.table[jr.pkey]) & (table[jr.fkey]==jr.record[jr.pkey]))
        if jr.component_id:
            query = (table.id==jr.component_id) & query
        if 'deleted' in table:
            query = ((table.deleted==False) | (table.deleted==None)) & query

        try:
            record_id = db(query).select(table.id)[0].id
            href_delete = URL(r=jr.request, f=jr.name, args=[jr.id, resource, 'delete', record_id])
            href_edit = URL(r=jr.request, f=jr.name, args=[jr.id, resource, 'update', record_id])
        except:
            if not jr.multiple:
                redirect(URL(r=jr.request, f=jr.name, args=[jr.id, resource, 'create']))
            else:
                record_id = None
                href_delete = None
                href_edit = None
                session.error = BADRECORD
                redirect(jr.there()) # TODO: this is wrong when no records exist!

        editable = s3xrc.model.get_attr(resource, 'editable')
        deletable = s3xrc.model.get_attr(resource, 'deletable')

        rss = s3xrc.model.get_attr(resource, 'rss')

    else:
        record_id = jr.id
        href_delete = URL(r=jr.request, f=jr.name, args=['delete', record_id])
        href_edit = URL(r=jr.request, f=jr.name, args=['update', record_id])

    authorised = shn_has_permission('update', table, record_id)
    if authorised and jr.representation=="html" and editable:
        return shn_update(jr, **attr)

    authorised = shn_has_permission('read', table, record_id)
    if authorised:

        shn_audit_read(operation='read', module=module, resource=resource, record=record_id, representation=jr.representation)

        if jr.representation=="html":
            shn_custom_view(jr, 'display.html')
            try:
                title = s3.crud_strings[jr.tablename].title_display
            except:
                title = s3.crud_strings.title_display
            output = dict(title=title)
            if jr.component:
                try:
                    subtitle = s3.crud_strings[tablename].title_display
                except:
                    subtitle = s3.crud_strings.title_display
                output.update(subtitle=subtitle)
                if pheader:
                    try:
                        _pheader = pheader(jr.name, jr.id, jr.representation, next=jr.there(), same=jr.same())
                    except:
                        _pheader = pheader
                    if _pheader:
                        output.update(pheader=_pheader)
            item = crud.read(table, record_id)
            if href_edit and editable:
                edit = A(T("Edit"), _href=href_edit, _id='edit-btn')
            else:
                edit = ''
            if href_delete and deletable:
                delete = A(T("Delete"), _href=href_delete, _id='delete-btn')
            else:
                delete = ''
            try:
                label_list_button = s3.crud_strings[tablename].label_list_button
            except:
                label_list_button = s3.crud_strings.label_list_button
            list_btn = A(label_list_button, _href=jr.there(), _id='list-btn')

            output.update(module_name=module_name,
                          item=item,
                          title=title,
                          edit=edit,
                          delete=delete,
                          list_btn=list_btn)

            if jr.component and not jr.multiple:
                del output["list_btn"]

            output.update(jr=jr)
            return(output)

        elif jr.representation == "plain":
            item = crud.read(table, record_id)
            response.view = 'plain.html'
            return dict(item=item, jr=jr)

        elif jr.representation == "csv":
            query = db[table].id == record_id
            return export_csv(resource, query)

        elif jr.representation == "pdf": # TODO: encoding problems, doesn't quite work
            query = db[table].id == record_id
            return export_pdf(table, query)

        elif jr.representation == "xls":
            query = db[table].id == record_id
            return export_xls(table, query)

        elif jr.representation in shn_json_export_formats:
            return export_json(jr)

        elif jr.representation in shn_xml_export_formats:
            return export_xml(jr)

        elif jr.representation == "rss": # TODO: replace by XML export
            query = db[table].id == record_id
            return export_rss(module, resource, query, rss=rss, linkto=jr.here('html'))

        else:
            session.error = BADFORMAT
            redirect(URL(r=request, f='index'))
    else:
        session.error = UNAUTHORISED
        redirect(URL(r=request, c='default', f='user', args='login', vars={'_next': jr.here()}))

#
# shn_linkto ------------------------------------------------------------------
#
def shn_linkto(jr):

    """ Helper function to generate links in list views """

    def shn_list_linkto(field, jr=jr):
        if jr.component:
            authorised = shn_has_permission('update', jr.component.table)
            if authorised:
                return jr.component.attr.linkto_update or \
                       URL(r=request, args=[jr.id, jr.component_name, 'update', field],
                           vars={"_next":URL(r=request, args=request.args, vars=request.vars)})
            else:
                return jr.component.attr.linkto or \
                       URL(r=request, args=[jr.id, jr.component_name, field],
                           vars={"_next":URL(r=request, args=request.args, vars=request.vars)})
        else:
            authorised = shn_has_permission('update', jr.table)
            if authorised:
                return response.s3.linkto_update or \
                       URL(r=request, args=['update', field],
                           vars={"_next":URL(r=request, args=request.args, vars=request.vars)})
            else:
                return response.s3.linkto or \
                       URL(r=request, args=[field],
                           vars={"_next":URL(r=request, args=request.args, vars=request.vars)})

    return shn_list_linkto

#
# shn_list --------------------------------------------------------------------
#
def shn_list(jr, **attr):

    """ List records matching the request """

    # Get the target table
    module, resource, table, tablename = jr.target()

    # Get request arguments
    pheader = attr.get('pheader', None)
    _attr = jr.component and jr.component.attr or attr

    onvalidation = _attr.get('onvalidation', None)
    onaccept = _attr.get('onaccept', None)
    editable = _attr.get('editable', True)
    deletable = _attr.get('deletable', True)
    rss = _attr.get('rss', None)
    list_fields = _attr.get('list_fields', None)
    listadd = _attr.get('listadd', True)
    main = _attr.get('main', None)
    extra = _attr.get('extra', None)
    orderby = _attr.get('orderby', None)
    sortby = _attr.get('sortby', None)

    # Provide the ability to get a subset of records
    if request.vars.limit:
        limit = int(request.vars.limit)
        if request.vars.start:
            start = int(request.vars.start)
            limitby = (start, start + limit)
        else:
            limitby = (0, limit)
    else:
        limitby = None

    # Get the initial query
    query = shn_accessible_query('read', table)

    # Get qualified query and create link
    if jr.component:
        if jr.record:
            query = ((table[jr.fkey]==jr.table[jr.pkey]) & \
                     (table[jr.fkey]==jr.record[jr.pkey])) & query
        else:
            query = (table[jr.fkey]==jr.table[jr.pkey]) & query
        if jr.component_id:
            query = (table.id==jr.component_id) & query
        href_add = URL(r=jr.request, f=jr.name, args=[jr.id, resource, 'create'])
    else:
        href_add = URL(r=jr.request, f=jr.name, args=['create'])

    # SSPag filter handling
    if jr.representation == "html":
        # HTML call sets/clears the filter
        session.s3.filter = response.s3.filter
    elif jr.representation.lower() == "aadata":
        # aaData call uses the filter, if present
        if session.s3.filter is not None:
            response.s3.filter = session.s3.filter

    # Add filter to query
    if response.s3.filter:
        query = response.s3.filter & query

    # Filter deleted records
    if 'deleted' in table:
        query = ((table.deleted == False) | (table.deleted == None)) & query

    # Call audit
    shn_audit_read(operation='list',
                   module=module,
                   resource=resource,
                   representation=jr.representation)

    # dataTables representation
    # Migrate to an XSLT in future?
    if jr.representation.lower()=="aadata":

        if "iDisplayStart" in request.vars:
            start = int(request.vars.iDisplayStart)
        else:
            start = 0
        if "iDisplayLength" in request.vars:
            limit = int(request.vars.iDisplayLength)
        else:
            limit = None

        # Which fields do we display?
        fields = None

        if jr.component:
            list_fields = jr.component.attr.list_fields
        if list_fields:
            fields = [f for f in list_fields if table[f].readable]

        if fields and len(fields)==0:
            fields.append('id')

        if not fields:
            fields = [f for f in table.fields if table[f].readable]

        if "iSortingCols" in request.vars and orderby is None:
            orderby = shn_convert_orderby(table, request, fields=fields)

        if request.vars.sSearch and request.vars.sSearch <> "":
            squery = shn_build_ssp_filter(table, request, fields=fields)
            if squery is not None:
                query = squery & query

        sEcho = int(request.vars.sEcho)

        totalrows = db(query).count()
        if limit:
            rows = db(query).select(table.ALL, limitby = (start, start + limit), orderby = orderby)
        else:
            rows = db(query).select(table.ALL, orderby = orderby)

        # Where to link the ID column?
        linkto = shn_linkto(jr)

        r = dict(sEcho = sEcho,
               iTotalRecords = len(rows),
               iTotalDisplayRecords = totalrows,
               aaData = [[shn_field_represent_sspage(table[f], row, f, linkto=linkto)
                          for f in fields] for row in rows])

        from gluon.serializers import json
        return json(r)

    if jr.representation=="html":
        output = dict(module_name=module_name, main=main, extra=extra, sortby=sortby)

        if jr.component:
            try:
                title = s3.crud_strings[jr.tablename].title_display
            except:
                title = s3.crud_strings.title_display
            try:
                subtitle = s3.crud_strings[tablename].subtitle_list
            except:
                subtitle = s3.crud_strings.subtitle_list

            if pheader:
                try:
                    _pheader = pheader(jr.name, jr.id, jr.representation,
                                       next=jr.there(),
                                       same=jr.same())
                except:
                    _pheader = pheader
                if _pheader:
                    output.update(pheader=_pheader)
        else:
            try:
                title = s3.crud_strings[tablename].title_list
            except:
                title = s3.crud_strings.title_list
            try:
                subtitle = s3.crud_strings[tablename].subtitle_list
            except:
                subtitle = s3.crud_strings.subtitle_list

        output.update(title=title, subtitle=subtitle)

        # Which fields do we display?
        fields = None

        if jr.component:
            list_fields = jr.component.attr.list_fields or []
            _fields = [jr.component.table[f] for f in list_fields if f in jr.component.table.fields]
            if _fields:
                fields = [f for f in _fields if f.readable]
            else:
                fields = None
        elif list_fields:
            fields = [table[f] for f in list_fields if table[f].readable]

        if fields and len(fields)==0:
            fields.append(table.id)

        if not fields:
            fields = [table[f] for f in table.fields if table[f].readable]

        # Column labels: use custom or prettified label
        headers = dict(map(lambda f: (str(f), f.label), fields))

        if response.s3.pagination and not limitby:
            # Server-side pagination, so only download 1 record initially & let the view request what it wants via AJAX
            limitby = (0, 1)

        linkto = shn_linkto(jr)

        items = crud.select(table, query=query,
            fields=fields,
            orderby=orderby,
            limitby=limitby,
            headers=headers,
            linkto=linkto,
            truncate=48, _id='list', _class='display')

        if not items:
            try:
                items = s3.crud_strings[tablename].msg_list_empty
            except:
                items = s3.crud_strings.msg_list_empty

        # Update the Return with common items
        output.update(dict(items=items))

        authorised = shn_has_permission('create', table)
        if authorised and listadd:

            # Block join field
            if jr.component:
                _comment = table[jr.fkey].comment
                table[jr.fkey].comment = None
                table[jr.fkey].default = jr.record[jr.pkey]
                table[jr.fkey].writable = False

            if onaccept:
                _onaccept = lambda form: \
                            shn_audit_create(form, module, resource, jr.representation) and \
                            s3xrc.store_session(session, module, resource, 0) and \
                            onaccept(form)
            else:
                _onaccept = lambda form: \
                            shn_audit_create(form, module, resource, jr.representation) and \
                            s3xrc.store_session(session, module, resource, 0)

            try:
                message = s3.crud_strings[tablename].msg_record_created
            except:
                message = s3.crud_strings.msg_record_created

            # Display the Add form above List
            form = crud.create(table,
                               onvalidation=onvalidation,
                               onaccept=_onaccept,
                               message=message,
                               next=jr.there())

            #form[0].append(TR(TD(), TD(INPUT(_type="reset", _value="Reset form"))))
            if response.s3.cancel:
                form[0][-1][1].append(INPUT(_type="button", _value="Cancel", _onclick="window.location='%s';" % response.s3.cancel))

            if jr.component:
                table[jr.fkey].comment = _comment

            try:
                addtitle = s3.crud_strings[tablename].subtitle_create
            except:
                addtitle = s3.crud_strings.subtitle_create

            # Check for presence of Custom View
            shn_custom_view(jr, 'list_create.html')

            # Add specificities to Return
            output.update(dict(form=form, addtitle=addtitle))

        else:
            # List only with create button below
            if listadd:
                try:
                    label_create_button = s3.crud_strings[tablename].label_create_button
                except:
                    label_create_button = s3.crud_strings.label_create_button
                add_btn = A(label_create_button, _href=href_add, _id='add-btn')
            else:
                add_btn = ''

            # Add specificities to Return
            output.update(dict(add_btn=add_btn))

            # Check for presence of Custom View
            shn_custom_view(jr, 'list.html')

        return output

    elif jr.representation=="ext":
        output = dict(module_name=module_name, main=main, extra=extra, sortby=sortby)

        if jr.component:
            try:
                title = s3.crud_strings[jr.tablename].title_display
            except:
                title = s3.crud_strings.title_display
        else:
            try:
                title = s3.crud_strings[tablename].title_list
            except:
                title = s3.crud_strings.title_list

        # Add to Return
        output.update(title=title)

        # Block join field
        if jr.component:
            _comment = table[jr.fkey].comment
            table[jr.fkey].comment = None
            table[jr.fkey].default = jr.record[jr.pkey]
            table[jr.fkey].writable = False

        if onaccept:
            _onaccept = lambda form: \
                        shn_audit_create(form, module, resource, jr.representation) and \
                        s3xrc.store_session(session, module, resource, form.vars.id) and \
                        onaccept(form)
        else:
            _onaccept = lambda form: \
                        shn_audit_create(form, module, resource, jr.representation) and \
                        s3xrc.store_session(session, module, resource, form.vars.id)

        try:
            message = s3.crud_strings[tablename].msg_record_created
        except:
            message = s3.crud_strings.msg_record_created

        # Form is used to build the initial list view
        form = crud.create(table,
                           onvalidation=onvalidation,
                           onaccept=_onaccept,
                           message=message,
                           next=jr.there())

        if jr.component:
            table[jr.fkey].comment = _comment

        # Update the Return with the Form
        output.update(form=form, pagesize=ROWSPERPAGE)

        authorised = shn_has_permission('update', table)
        if authorised:
            # Provide an Editable Grid

            # Check for presence of Custom View
            shn_custom_view(jr, 'list_create.html', format='ext')

        else:
            # Provide a read-only Ext grid
            # (We could do this from the HTML table using TableGrid, but then we wouldn't have client-side pagination)

            if listadd:
                try:
                    label_create_button = s3.crud_strings[tablename].label_create_button
                except:
                    label_create_button = s3.crud_strings.label_create_button
                add_btn = A(label_create_button, _href=href_add, _id='add-btn')
            else:
                add_btn = ''

            # Add to Return
            output.update(dict(add_btn=add_btn))

            # Check for presence of Custom View
            shn_custom_view(jr, 'list.html', format='ext')

        return output

    elif jr.representation == "plain":
        items = crud.select(table, query, truncate=24)
        response.view = 'plain.html'
        return dict(item=items, jr=jr)

    elif jr.representation == "csv":
        return export_csv(resource, query)

    elif jr.representation == "pdf":
        return export_pdf(table, query)

    elif jr.representation == "xls":
        return export_xls(table, query)

    elif jr.representation in shn_json_export_formats:
        return export_json(jr)

    elif jr.representation in shn_xml_export_formats:
        return export_xml(jr)

    elif jr.representation == "rss":
        return export_rss(module, resource, query, rss=rss, linkto=jr.there('html'))

    else:
        session.error = BADFORMAT
        redirect(URL(r=request, f='index'))

#
# shn_create ------------------------------------------------------------------
#
def shn_create(jr, **attr):

    """ Create new records """

    onvalidation = attr.get('onvalidation', None)
    onaccept = attr.get('onaccept', None)
    pheader = attr.get('pheader', None)
    main = attr.get('main', None)

    module, resource, table, tablename = jr.target()

    if jr.component:

        onvalidation = s3xrc.model.get_attr(resource, "onvalidation")
        onaccept = s3xrc.model.get_attr(resource, "onaccept")

        main = s3xrc.model.get_attr(resource, "main")
        extra = s3xrc.model.get_attr(resource, "extra")

    if jr.representation == "html":

        # Check for presence of Custom View
        shn_custom_view(jr, 'create.html')

        output = dict(module_name=module_name, module=module, resource=resource, main=main)

        if jr.component:
            try:
                title = s3.crud_strings[jr.tablename].title_display
            except:
                title = s3.crud_strings.title_display
            try:
                subtitle = s3.crud_strings[tablename].subtitle_create
            except:
                subtitle = s3.crud_strings.subtitle_create
            output.update(subtitle=subtitle)

            if pheader:
                try:
                    _pheader = pheader(jr.name, jr.id, jr.representation,
                                       next=jr.there(),
                                       same=jr.same())
                except:
                    _pheader = pheader
                if _pheader:
                    output.update(pheader=_pheader)
        else:
            try:
                title = s3.crud_strings[tablename].title_create
            except:
                title = s3.crud_strings.title_create

        try:
            label_list_button = s3.crud_strings[tablename].label_list_button
        except:
            label_list_button = s3.crud_strings.label_list_button
        list_btn = A(label_list_button, _href=jr.there(), _id='list-btn')

        output.update(title=title, list_btn=list_btn)

        if jr.component:
            # Block join field
            _comment = table[jr.fkey].comment
            table[jr.fkey].comment = None
            table[jr.fkey].default = jr.record[jr.pkey]
            table[jr.fkey].writable = False
            # Save callbacks
            create_onvalidation = crud.settings.create_onvalidation
            create_onaccept = crud.settings.create_onaccept
            create_next = crud.settings.create_next
            # Neutralize callbacks
            crud.settings.create_onvalidation = None
            crud.settings.create_onaccept = None
            crud.settings.create_next = s3xrc.model.get_attr(jr.component_name, 'create_next') or jr.there()
        else:
            if not crud.settings.create_next:
                crud.settings.create_next = jr.there()
            if not onvalidation:
                onvalidation = crud.settings.create_onvalidation
            if not onaccept:
                onaccept = crud.settings.create_onaccept

        if onaccept:
            _onaccept = lambda form: \
                        shn_audit_create(form, module, resource, jr.representation) and \
                        s3xrc.store_session(session, module, resource, form.vars.id) and \
                        onaccept(form)

        else:
            _onaccept = lambda form: \
                        shn_audit_create(form, module, resource, jr.representation) and \
                        s3xrc.store_session(session, module, resource, form.vars.id)

        try:
            message = s3.crud_strings[tablename].msg_record_created
        except:
            message = s3.crud_strings.msg_record_created

        form = crud.create(table,
                           message=message,
                           onvalidation=onvalidation,
                           onaccept=_onaccept)


        #form[0].append(TR(TD(), TD(INPUT(_type="reset", _value="Reset form"))))
        if response.s3.cancel:
            form[0][-1][1].append(INPUT(_type="button", _value="Cancel", _onclick="window.location='%s';" % response.s3.cancel))

        if jr.component:
            # Restore comment
            table[jr.fkey].comment = _comment
            # Restore callbacks
            crud.settings.create_onvalidation = create_onvalidation
            crud.settings.create_onaccept = create_onaccept
            crud.settings.create_next = create_next

        output.update(form=form)

        if jr.component and not jr.multiple:
            del output["list_btn"]

        output.update(jr=jr)
        return output

    elif jr.representation == "plain":
        if onaccept:
            _onaccept = lambda form: \
                        shn_audit_create(form, module, resource, jr.representation) and \
                        onaccept(form)
        else:
            _onaccept = lambda form: \
                        shn_audit_create(form, module, resource, jr.representation)

        form = crud.create(table, onvalidation=onvalidation, onaccept=_onaccept)
        response.view = 'plain.html'
        return dict(item=form, jr=jr)

    elif jr.representation == "ext":
        shn_custom_view(jr, 'create.html', format='ext')
        return dict()

    elif jr.representation == "popup":
        if onaccept:
            _onaccept = lambda form: \
                        shn_audit_create(form, module, resource, jr.representation) and \
                        onaccept(form)
        else:
            _onaccept = lambda form: \
                        shn_audit_create(form, module, resource, jr.representation)

        form = crud.create(table, onvalidation=onvalidation, onaccept=_onaccept)
        # Check for presence of Custom View
        shn_custom_view(jr, 'popup.html')
        return dict(module_name=module_name, form=form, module=module,
                    resource=resource, main=main, caller=request.vars.caller)

    elif jr.representation == "url":
        return import_url(jr, table, method="create", onvalidation=onvalidation, onaccept=onaccept)

    elif jr.representation == "csv":
        # Read in POST
        import csv
        csv.field_size_limit(1000000000)
        infile = open(request.vars.filename, 'rb')
        #try:
        import_csv(infile, table)
        session.flash = T('Data uploaded')
        #except:
            #session.error = T('Unable to parse CSV file!')
        redirect(jr.there())

    elif jr.representation in shn_json_import_formats:
        response.view = 'plain.html'
        return import_json(jr, onvalidation=onvalidation, onaccept=onaccept)

    elif jr.representation in shn_xml_import_formats:
        response.view = 'plain.html'
        return import_xml(jr, onvalidation=onvalidation, onaccept=onaccept)

    else:
        session.error = BADFORMAT
        redirect(URL(r=request, f='index'))

#
# shn_update ------------------------------------------------------------------
#
def shn_update(jr, **attr):

    """ Update an existing record """

    onvalidation = attr.get('onvalidation', None)
    onaccept = attr.get('onaccept', None)
    pheader = attr.get('pheader', None)
    editable = attr.get('editable', True)
    deletable = attr.get('deletable', True)

    module, resource, table, tablename = jr.target()

    if jr.component:

        if jr.multiple and not jr.component_id:
            return shn_create(jr, pheader)

        query = (table[jr.fkey]==jr.record[jr.pkey])
        if jr.component_id:
            query = (table.id==jr.component_id) & query
        if 'deleted' in table:
            query = ((table.deleted==False) | (table.deleted==None)) & query

        try:
            record_id = db(query).select(table.id)[0].id
        except:
            record_id = None
            href_delete = None
            href_edit = None
            session.error = BADRECORD
            redirect(jr.there())

        onvalidation = s3xrc.model.get_attr(resource, 'onvalidation')
        onaccept = s3xrc.model.get_attr(resource, 'onaccept')
        editable = s3xrc.model.get_attr(resource, 'editable')
        deletable = s3xrc.model.get_attr(resource, 'deletable')

    else:
        record_id = jr.id
        deletable = deletable and shn_has_permission('delete', table, record_id)

    if not editable and jr.representation=="html":
        return shn_read(jr, **attr)

    authorised = shn_has_permission('update', table, record_id)
    if authorised:
        crud.settings.update_deletable = deletable

        if jr.representation == "html":

            shn_custom_view(jr, 'update.html')

            output = dict(module_name=module_name)

            if jr.component:
                try:
                    title = s3.crud_strings[jr.tablename].title_display
                except:
                    title = s3.crud_strings.title_display
                try:
                    subtitle = s3.crud_strings[tablename].title_update
                except:
                    subtitle = s3.crud_strings.title_update
                output.update(subtitle=subtitle)

                if pheader:
                    try:
                        _pheader = pheader(jr.name, jr.id, jr.representation,
                                           next=jr.there(),
                                           same=jr.same())
                    except:
                        _pheader = pheader
                    if _pheader:
                        output.update(pheader=_pheader)
            else:
                try:
                    title = s3.crud_strings[tablename].title_update
                except:
                    title = s3.crud_strings.title_update

            try:
                label_list_button = s3.crud_strings[tablename].label_list_button
            except:
                label_list_button = s3.crud_strings.label_list_button
            list_btn = A(label_list_button, _href=jr.there(), _id='list-btn')

            if deletable:
                del_href = jr.other(method='delete', representation=jr.representation)
                if tablename in s3.crud_strings and "label_delete_button" in s3.crud_strings[tablename]:
                    label_del_button = s3.crud_strings[tablename].label_delete_button
                else:
                    label_del_button = None
                if label_del_button is None:
                    label_del_button = s3.crud_strings.label_delete_button
                del_btn = A(label_del_button, _href=del_href, _id='delete-btn')
                output.update(del_btn=del_btn)

            output.update(title=title, list_btn=list_btn)

            if jr.component:
                # Block join field
                _comment = table[jr.fkey].comment
                table[jr.fkey].comment = None
                table[jr.fkey].default = jr.record[jr.pkey]
                table[jr.fkey].writable = False
                # Save callbacks
                update_onvalidation = crud.settings.update_onvalidation
                update_onaccept = crud.settings.update_onaccept
                update_next = crud.settings.update_next
                # Neutralize callbacks
                crud.settings.update_onvalidation = None
                crud.settings.update_onaccept = None
                crud.settings.update_next = s3xrc.model.get_attr(jr.component_name, 'update_next') or \
                                            jr.there()
            else:
                if not crud.settings.update_next:
                    crud.settings.update_next = jr.here()
                if not onvalidation:
                    onvalidation = crud.settings.update_onvalidation
                if not onaccept:
                    onaccept = crud.settings.update_onaccept

            try:
                message = s3.crud_strings[tablename].msg_record_modified
            except:
                message = s3.crud_strings.msg_record_modified

            if onaccept:
                _onaccept = lambda form: \
                    shn_audit_update(form, module, resource, jr.representation) and \
                    s3xrc.store_session(session, module, resource, form.vars.id) and \
                    onaccept(form)
            else:
                _onaccept = lambda form: \
                    shn_audit_update(form, module, resource, jr.representation) and \
                    s3xrc.store_session(session, module, resource, form.vars.id)

            form = crud.update(table, record_id,
                               message=message,
                               onvalidation=onvalidation,
                               onaccept=_onaccept,
                               deletable=False) # TODO: add extra delete button to form

            #form[0].append(TR(TD(), TD(INPUT(_type="reset", _value="Reset form"))))
            if response.s3.cancel:
                form[0][-1][1].append(INPUT(_type="button", _value="Cancel", _onclick="window.location='%s';" % response.s3.cancel))

            if jr.component:
                # Restore comment
                table[jr.fkey].comment = _comment
                # Restore callbacks
                crud.settings.update_onvalidation = update_onvalidation
                crud.settings.update_onaccept = update_onaccept
                crud.settings.update_next = update_next

            output.update(form=form, jr=jr)

            if jr.component and not jr.multiple:
                del output["list_btn"]

            return(output)

        elif jr.representation == "plain":
            if onaccept:
                _onaccept = lambda form: \
                            shn_audit_update(form, module, resource, jr.representation) and \
                            onaccept(form)
            else:
                _onaccept = lambda form: \
                            shn_audit_update(form, module, resource, jr.representation)

            form = crud.update(table, record_id,
                               onvalidation=onvalidation,
                               onaccept=_onaccept,
                               deletable=False)

            response.view = 'plain.html'
            return dict(item=form, jr=jr)

        elif jr.representation == "ext":
            shn_custom_view(jr, 'update.html', format='ext')
            return dict()

        elif jr.representation == "url":
            return import_url(jr, table, method="update", onvalidation=onvalidation, onaccept=onaccept)

        elif jr.representation in shn_json_import_formats:
            response.view = 'plain.html'
            return import_json(jr, onvalidation=onvalidation, onaccept=onaccept)

        elif jr.representation in shn_xml_import_formats:
            response.view = 'plain.html'
            return import_xml(jr, onvalidation=onvalidation, onaccept=onaccept)

        else:
            session.error = BADFORMAT
            redirect(URL(r=request, f='index'))

    else:
        session.error = UNAUTHORISED
        redirect(URL(r=request, c='default', f='user', args='login', vars={'_next': jr.here()}))
#
# shn_delete ------------------------------------------------------------------
#
def shn_delete(jr, **attr):

    """ Delete record(s) """

    module, resource, table, tablename = jr.target()

    if jr.component:
        onvalidation = s3xrc.model.get_attr(resource, "delete_onvalidation")
        onaccept = s3xrc.model.get_attr(resource, "delete_onaccept")

        query = ((table[jr.fkey]==jr.table[jr.pkey]) & (table[jr.fkey]==jr.record[jr.pkey]))
        if jr.component_id:
            query = (table.id==jr.component_id) & query
        if 'deleted' in table:
            query = (table.deleted==False) & query
    else:
        query = (table.id==jr.id)

    if 'deleted' in table:
        query = (table.deleted==False) & query

    # Get target records
    rows = db(query).select(table.ALL)

    # Nothing to do? Return here!
    if not rows or len(rows)==0:
        session.confirmation = T('No records to delete')
        return

    try:
        message = s3.crud_strings[tablename].msg_record_deleted
    except:
        message = s3.crud_strings.msg_record_deleted

    if jr.component:
        # Save callback settings
        delete_onvalidation = crud.settings.delete_onvalidation
        delete_onaccept = crud.settings.delete_onaccept
        delete_next = crud.settings.delete_next

        # Set resource specific callbacks, if any
        crud.settings.delete_onvalidation = onvalidation
        crud.settings.delete_onaccept = onaccept
        crud.settings.delete_next = None # do not set here!

    # Delete all accessible records
    numrows = 0
    for row in rows:
        if shn_has_permission('delete', table, row.id):
            numrows += 1
            shn_audit_delete(module, resource, row.id, jr.representation)
            if "deleted" in db[table] and \
               db(db.s3_setting.id==1).select()[0].archive_not_delete:
                if crud.settings.delete_onvalidation:
                    crud.settings.delete_onvalidation(row)
                # Avoid collisions of values in unique fields between deleted records and
                # later new records => better solution could be: move the deleted data to
                # a separate table (e.g. in JSON) and delete from this table (that would
                # also eliminate the need for special deletion status awareness throughout
                # the system). Should at best be solved in the DAL.
                deleted = dict(deleted=True)
                for f in table.fields:
                    if f not in ('id', 'uuid') and table[f].unique:
                        deleted.update({f:None}) # not good => data loss!
                db(db[table].id == row.id).update(**deleted)
                if crud.settings.delete_onaccept:
                    crud.settings.delete_onaccept(row)
            else:
                # Do not CRUD.delete! (it never returns, but redirects)
                if crud.settings.delete_onvalidation:
                    crud.settings.delete_onvalidation(row)
                del db[table][row.id]
                if crud.settings.delete_onaccept:
                    crud.settings.delete_onaccept(row)
        else:
            continue

    if jr.component:
        # Restore callback settings
        crud.settings.delete_onvalidation = delete_onvalidation
        crud.settings.delete_onaccept = delete_onaccept
        crud.settings.delete_next = delete_next

        delete_next =  jr.component.attr.delete_next

    # Confirm and return
    if numrows > 1:
        session.confirmation = "%s %s" % ( numrows, T('records deleted'))
    else:
        session.confirmation = message

    if jr.component and delete_next: # but redirect here!
        redirect(delete_next)

    item = json_message()
    response.view = 'plain.html'
    output = dict(item=item)

    return output

#
# shn_options -----------------------------------------------------------------
#
def shn_options(jr, **attr):

    if jr.representation=="xml":
        response.headers["Content-Type"] = "text/xml"
        response.view = "plain.html"
        return jr.options_xml(pretty_print=PRETTY_PRINT)

    elif jr.representation=="json":
        response.headers['Content-Type'] = 'text/x-json'
        response.view = "plain.html"
        return jr.options_json(pretty_print=PRETTY_PRINT)

    else:
        session.error = BADFORMAT
        redirect(URL(r=request, f='index'))

#
# shn_search ------------------------------------------------------------------
#
def shn_search(jr, **attr):

    """ Search function responding in JSON """

    deletable = attr.get('deletable', True)
    main = attr.get('main', None)
    extra = attr.get('extra', None)

    request = jr.request

    # Filter Search list to just those records which user can read
    query = shn_accessible_query('read', jr.table)

    # Filter search to items which aren't deleted
    if 'deleted' in jr.table:
        query = (jr.table.deleted==False) & query

    # Respect response.s3.filter
    if response.s3.filter:
        query = response.s3.filter & query

    if jr.representation == "html":

        shn_represent(jr.table, jr.prefix, jr.name, deletable, main, extra)
        search = t2.search(jr.table, query=query)

        # Check for presence of Custom View
        shn_custom_view(jr, 'search.html')

        # CRUD Strings
        title = s3.crud_strings.title_search

        output = dict(module_name=module_name, search=search, title=title)

    elif jr.representation == "json":

        # JQuery Autocomplete uses 'q' instead of 'value'
        value = request.vars.value or request.vars.q or None

        if request.vars.field and request.vars.filter and value:
            field = str.lower(request.vars.field)

            # Optional fields
            if 'field2' in request.vars:
                field2 = str.lower(request.vars.field2)
            else:
                field2 = None
            if 'field3' in request.vars:
                field3 = str.lower(request.vars.field3)
            else:
                field3 = None
            if 'extra_string' in request.vars:
                extra_string = str.lower(request.vars.extra_string)
            else:
                extra_string = None
            if 'parent' in request.vars:
                parent = int(request.vars.parent)
            else:
                parent = None
            if 'exclude' in request.vars:
                import urllib
                exclude = urllib.unquote(request.vars.exclude)
            else:
                exclude = None

            filter = request.vars.filter
            if filter == '~':
                if field2 and field3:

                    # pr_person name search
                    if ' ' in value:
                        value1, value2 = value.split(' ', 1)
                        query = query & ((jr.table[field].like('%' + value1 + '%')) & \
                                        (jr.table[field2].like('%' + value2 + '%')) | \
                                        (jr.table[field3].like('%' + value2 + '%')))
                    else:
                        query = query & ((jr.table[field].like('%' + value + '%')) | \
                                        (jr.table[field2].like('%' + value + '%')) | \
                                        (jr.table[field3].like('%' + value + '%')))

                elif extra_string:

                    # gis_location hierarchical search
                    if parent:
                        query = query & (jr.table.parent == parent) & \
                                        (jr.table[field].like('%' + value + '%')) & \
                                        (jr.table[field].like('%' + extra_string + '%'))
                    else:
                        query = query & (jr.table[field].like('%' + value + '%')) & \
                                        (jr.table[field].like('%' + extra_string + '%'))

                elif exclude:

                    # gis_location without Admin Areas
                    query = query & ~(jr.table[field].like(exclude)) & \
                                    (jr.table[field].like('%' + value + '%'))

                else:
                    # Normal single-field
                    query = query & (jr.table[field].like('%' + value + '%'))

                limit = int(request.vars.limit or 0)
                if limit:
                    item = db(query).select(limitby=(0, limit)).json()
                else:
                    item = db(query).select().json()

            elif filter == '=':
                query = query & (jr.table[field] == value)
                item = db(query).select().json()

            elif filter == '<':
                query = query & (jr.table[field] < value)
                item = db(query).select().json()

            elif filter == '>':
                query = query & (jr.table[field] > value)
                item = db(query).select().json()

            else:
                item = json_message(False, 400, "Unsupported filter! Supported filters: ~, =, <, >")
                raise HTTP(400, body=item)
        else:
            item = json_message(False, 400, "Search requires specifying Field, Filter & Value!")
            raise HTTP(400, body=item)

        response.view = 'plain.html'
        output = dict(item=item)

    else:
        raise HTTP(501, body=BADFORMAT)

    return output

# *****************************************************************************
# Main controller function

#
# shn_rest_controller ---------------------------------------------------------
#
def shn_rest_controller(module, resource, **attr):

    """
        RESTlike controller function
        ============================

        Provides CRUD operations for the given module/resource.

        Supported Representations:
        ==========================

        Representation is recognized from the extension of the target resource.
        You can still pass a "?format=" to override this.

            - B{html}: is the default (including full layout)
            - B{plain}: is HTML with no layout
                - can be inserted into DIVs via AJAX calls
                - can be useful for clients on low-bandwidth or small screen sizes
            - B{ext}: is Ext layouts (experimental)
            - B{json}: JSON export/import using XSLT
            - B{xml}: XML export/import using XSLT
            - B{csv}: useful for synchronization/database migration
                - List/Display/Create for now
            - B{pdf}: list/read only
            - B{rss}: list only
            - B{xls}: list/read only
            - B{ajax}: designed to be run asynchronously to refresh page elements
            - B{url}: designed to be accessed via JavaScript
                - responses in JSON format
                - create/update/delete done via simple GET vars (no form displayed)
            - B{popup}: designed to be used inside popups
            - B{aaData}: used by dataTables for server-side pagination

        Request options:
        ================

            - B{response.s3.filter}: contains custom query to filter list views (primary resources)
            - B{response.s3.jfilter}: contains custom query to filter list views (joined resources)
            - B{response.s3.cancel}: adds a cancel button to forms & provides a location to direct to upon pressing
            - B{response.s3.pagination}: enables server-side pagination (detected by view which then calls REST via AJAX)

        Description:
        ============

        @param deletable: provide visible options for deletion (optional, default=True)
        @param editable: provide visible options for editing (optional, default=True)
        @param listadd: provide an add form in the list view (optional, default=True)

        @param main:
            the field used for the title in RSS output (optional, default="name")
        @param extra:
            the field used for the description in RSS output & in Search AutoComplete
            (optional, default=None)

        @param orderby:
            the sort order for server-side paginated list views (optional, default=None), e.g.::
                db.mytable.myfield1|db.mytable.myfield2

        @param sortby:
            the sort order for client-side paginated list views (optional, default=None), e.g.::
                [[1, "asc"], [2, "desc"]]

            see: U{http://datatables.net/examples/basic_init/table_sorting.html}

        @param onvalidation: callback processed B{before} DB IO
        @type onvalidation:
            lambda form:, function(form)

        @param onaccept: callback processed B{after} DB IO
        @type onaccept:
            lambda form:, function(form)

        @param pheader: function to produce a page header for the primary resource
        @type pheader:
            function(resource, record_id, representation, next=None, same=None)

        @author: Fran Boon
        @author: nursix

        @todo:
            - Alternate Representations
            - CSV update
            - SMS, LDIF

    """

    s3rest.set_handler('import_xml', import_xml)
    s3rest.set_handler('import_json', import_json)
    s3rest.set_handler('list', shn_list)
    s3rest.set_handler('read', shn_read)
    s3rest.set_handler('create', shn_create)
    s3rest.set_handler('update', shn_update)
    s3rest.set_handler('delete', shn_delete)
    s3rest.set_handler('search', shn_search)
    s3rest.set_handler('options', shn_options)

    output = s3rest(session, request, response, module, resource, **attr)
    return output

# END
# *****************************************************************************