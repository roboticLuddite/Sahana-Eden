﻿# -*- coding: utf-8 -*-

module = 'gis'
# Current Module (for sidebar title)
module_name = db(db.s3_module.name==module).select()[0].name_nice
# Options Menu (available in all Functions' Views)
response.menu_options = [
    [T('Map Viewing Client'), False, URL(r=request, f='map_viewing_client')],
    [T('Map Service Catalogue'), False, URL(r=request, f='map_service_catalogue')],
    [T('Bulk Uploader'), False, URL(r=request, f='bulk_upload')],
]

# Model options used in multiple Actions
table = 'gis_location'
db[table].uuid.requires = IS_NOT_IN_DB(db, '%s.uuid' % table)
db[table].name.requires = IS_NOT_EMPTY()    # Placenames don't have to be unique
db[table].name.label = T('Name')
db[table].parent.requires = IS_NULL_OR(IS_ONE_OF(db, 'gis_location.id', '%(name)s'))
db[table].parent.represent = lambda id: (id and [db(db.gis_location.id==id).select()[0].name] or ["None"])[0]
db[table].parent.label = T('Parent')
db[table].gis_feature_type.requires = IS_IN_SET(gis_feature_type_opts)
db[table].gis_feature_type.represent = lambda opt: opt and gis_feature_type_opts[opt]
db[table].gis_feature_type.label = T('Feature Type')
db[table].lat.requires = IS_NULL_OR(IS_LAT())
db[table].lat.label = T('Latitude')
#db[table].lat.comment = DIV(SPAN("*", _class="req"), A(SPAN("[Help]"), _class="tooltip", _title=T("Latitude|Latitude is North-South (Up-Down). Latitude is zero on the equator and positive in the northern hemisphere and negative in the southern hemisphere.")))
CONVERSION_TOOL = T("Conversion Tool")
db[table].lat.comment = DIV(SPAN("*", _class="req"), A(CONVERSION_TOOL, _class='thickbox', _href=URL(r=request, c='gis', f='convert_gps', vars=dict(KeepThis='true'))+"&TB_iframe=true", _target='top', _title=CONVERSION_TOOL), A(SPAN("[Help]"), _class="tooltip", _title=T("Latitude|Latitude is North-South (Up-Down). Latitude is zero on the equator and positive in the northern hemisphere and negative in the southern hemisphere. This needs to be added in Decimal Degrees. Use the popup to convert from either GPS coordinates or Degrees/Minutes/Seconds.")))
db[table].lon.requires = IS_NULL_OR(IS_LON())
db[table].lon.label = T('Longitude')
db[table].lon.comment = DIV(SPAN("*", _class="req"), A(SPAN("[Help]"), _class="tooltip", _title=T("Longitude|Longitude is West - East (sideways). Longitude is zero on the prime meridian (Greenwich Mean Time) and is positive to the east, across Europe and Asia.  Longitude is negative to the west, across the Atlantic and the Americas.  This needs to be added in Decimal Degrees. Use the popup to convert from either GPS coordinates or Degrees/Minutes/Seconds.")))
# WKT validation is done in the onvalidation callback
#db[table].wkt.requires=IS_NULL_OR(IS_WKT())
db[table].wkt.label = T('Well-Known Text')
db[table].wkt.comment = DIV(SPAN("*", _class="req"), A(SPAN("[Help]"), _class="tooltip", _title=T("WKT|The <a href='http://en.wikipedia.org/wiki/Well-known_text' target=_blank>Well-Known Text</a> representation of the Polygon/Line.")))

table = 'gis_metadata'
db[table].uuid.requires = IS_NOT_IN_DB(db, '%s.uuid' % table)
db[table].description.label = T('Description')
db[table].person_id.label = T("Contact")
db[table].source.label = T('Source')
db[table].accuracy.label = T('Accuracy')
db[table].sensitivity.label = T('Sensitivity')
db[table].event_time.requires = IS_NULL_OR(IS_DATETIME())
db[table].event_time.label = T('Event Time')
db[table].expiry_time.requires = IS_NULL_OR(IS_DATETIME())
db[table].expiry_time.label = T('Expiry Time')
db[table].url.requires = IS_NULL_OR(IS_URL())
db[table].url.label = 'URL'
db[table].image.label = T('Image')

table = 'gis_track'
db[table].name.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, '%s.name' % table)]
db[table].name.label = T('Name')
db[table].name.comment = SPAN("*", _class="req")
db[table].track.label = T('GPS Track File')
db[table].track.comment = DIV(SPAN("*", _class="req"), A(SPAN("[Help]"), _class="tooltip", _title=T("Latitude|Latitude is North-South (Up-Down). Latitude is zero on the equator and positive in the northern hemisphere and negative in the southern hemisphere. This needs to be added in Decimal Degrees. Use the popup to convert from either GPS coordinates or Degrees/Minutes/Seconds.")))

# Web2Py Tools functions
def download():
    "Download a file."
    return response.download(request, db) 

# S3 framework functions
def index():
    "Module's Home Page"
    return dict(module_name=module_name)

def apikey():
    "RESTlike CRUD controller"
    resource = 'apikey'
    table = module + '_' + resource
    
    # Model options
    # FIXME
    # We want a THIS_NOT_IN_DB here: http://groups.google.com/group/web2py/browse_thread/thread/27b14433976c0540/fc129fd476558944?lnk=gst&q=THIS_NOT_IN_DB#fc129fd476558944
    db[table].name.requires = IS_IN_SET(['google', 'multimap', 'yahoo']) 
    db[table].name.label = T("Service")
    #db[table].apikey.requires = THIS_NOT_IN_DB(db(db[table].name==request.vars.name), 'gis_apikey.name', request.vars.name,'Service already in use')
    db[table].apikey.requires = IS_NOT_EMPTY()
    db[table].apikey.label = T("Key")

    # CRUD Strings
    title_create = T('Add Key')
    title_display = T('Key Details')
    title_list = T('List Keys')
    title_update = T('Edit Key')
    title_search = T('Search Keys')
    subtitle_create = T('Add New Key')
    subtitle_list = T('Keys')
    label_list_button = T('List Keys')
    label_create_button = T('Add Key')
    msg_record_created = T('Key added')
    msg_record_modified = T('Key updated')
    msg_record_deleted = T('Key deleted')
    msg_list_empty = T('No Keys currently defined')
    s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)
    
    return shn_rest_controller(module, resource, deletable=False, listadd=False)

def config():
    "RESTlike CRUD controller"
    resource = 'config'
    table = module + '_' + resource
    
    # Model options
    db[table].uuid.requires = IS_NOT_IN_DB(db, '%s.uuid' % table)
    db[table].lat.requires = IS_LAT()
    db[table].lat.label = T('Latitude')
    db[table].lat.comment = DIV(SPAN("*", _class="req"), A(SPAN("[Help]"), _class="tooltip", _title=T("Latitude|Latitude is North-South (Up-Down). Latitude is zero on the equator and positive in the northern hemisphere and negative in the southern hemisphere.")))
    db[table].lon.requires = IS_LON()
    db[table].lon.label = T('Longitude')
    db[table].lon.comment = DIV(SPAN("*", _class="req"), A(SPAN("[Help]"), _class="tooltip", _title=T("Longitude|Longitude is West - East (sideways). Longitude is zero on the prime meridian (Greenwich Mean Time) and is positive to the east, across Europe and Asia.  Longitude is negative to the west, across the Atlantic and the Americas.")))
    db[table].zoom.requires = IS_INT_IN_RANGE(0,19)
    db[table].zoom.label = T('Zoom')
    db[table].zoom.comment = DIV(SPAN("*", _class="req"), A(SPAN("[Help]"), _class="tooltip", _title=T("Zoom|How much detail is seen. A high Zoom level means lot of detail, but not a wide area. A low Zoom level means seeing a wide area, but not a high level of detail.")))
    db[table].marker_id.label = T('Default Marker')
    db[table].map_height.requires = [IS_NOT_EMPTY(), IS_ALPHANUMERIC()]
    db[table].map_height.label = T('Map Height')
    db[table].map_height.comment = SPAN("*", _class="req")
    db[table].map_width.requires = [IS_NOT_EMPTY(), IS_ALPHANUMERIC()]
    db[table].map_width.label = T('Map Width')
    db[table].map_width.comment = SPAN("*", _class="req")

    # CRUD Strings
    title_create = T('Add Config')
    title_display = T('Config Details')
    title_list = T('List Configs')
    title_update = T('Edit Config')
    title_search = T('Search Configs')
    subtitle_create = T('Add New Config')
    subtitle_list = T('Configs')
    label_list_button = T('List Configs')
    label_create_button = T('Add Config')
    msg_record_created = T('Config added')
    msg_record_modified = T('Config updated')
    msg_record_deleted = T('Config deleted')
    msg_list_empty = T('No Configs currently defined')
    s3.crud_strings[table] = Storage(title_create=title_create, title_display=title_display, title_list=title_list, title_update=title_update, title_search=title_search, subtitle_create=subtitle_create, subtitle_list=subtitle_list, label_list_button=label_list_button, label_create_button=label_create_button, msg_record_created=msg_record_created, msg_record_modified=msg_record_modified, msg_record_deleted=msg_record_deleted, msg_list_empty=msg_list_empty)
    
    return shn_rest_controller(module, resource, deletable=False, listadd=False)

def feature_class():
    "RESTlike CRUD controller"
    resource = 'feature_class'
    table = module + '_' + resource
    
    # Model options
    db[table].uuid.requires = IS_NOT_IN_DB(db, '%s.uuid' % table)
    db[table].name.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, '%s.name' % table)]
    db[table].name.label = T('Name')
    db[table].name.comment = SPAN("*", _class="req")
    db[table].description.label = T('Description')
    db[table].module.requires = IS_NULL_OR(IS_ONE_OF(db((db.s3_module.enabled=='True') & (~db.s3_module.name.like('default'))), 's3_module.name', '%(name_nice)s'))
    db[table].module.label = T('Module')
    db[table].resource.requires = IS_NULL_OR(IS_IN_SET(resource_opts))
    db[table].resource.label = T('Resource')

    # CRUD Strings
    title_create = T('Add Feature Class')
    title_display = T('Feature Class Details')
    title_list = T('List Feature Classes')
    title_update = T('Edit Feature Class')
    title_search = T('Search Feature Class')
    subtitle_create = T('Add New Feature Class')
    subtitle_list = T('Feature Classes')
    label_list_button = T('List Feature Classes')
    label_create_button = ADD_FEATURE_CLASS
    msg_record_created = T('Feature Class added')
    msg_record_modified = T('Feature Class updated')
    msg_record_deleted = T('Feature Class deleted')
    msg_list_empty = T('No Feature Classes currently defined')
    s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)
    
    return shn_rest_controller(module, resource)

def feature_group():
    "RESTlike CRUD controller"
    resource = 'feature_group'
    table = module + '_' + resource
    
    # Model options
    db[table].uuid.requires = IS_NOT_IN_DB(db, '%s.uuid' % table)
    #db[table].author.requires = IS_ONE_OF(db, 'auth_user.id','%(id)s: %(first_name)s %(last_name)s')
    db[table].name.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, '%s.name' % table)]
    db[table].name.label = T('Name')
    db[table].name.comment = SPAN("*", _class="req")
    db[table].description.label = T('Description')
    #db[table].features.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("Multi-Select|Click Features to select, Click again to Remove. Dark Green is selected."))
    #db[table].feature_classes.comment = A(SPAN("[Help]"), _class="tooltip", _title=T("Multi-Select|Click Features to select, Click again to Remove. Dark Green is selected."))

    # CRUD Strings
    title_create = T('Add Feature Group')
    title_display = T('Feature Group Details')
    title_list = T('List Feature Groups')
    title_update = T('Edit Feature Group')
    title_search = T('Search Feature Groups')
    subtitle_create = T('Add New Feature Group')
    subtitle_list = T('Feature Groups')
    label_list_button = T('List Feature Groups')
    label_create_button = T('Add Feature Group')
    msg_record_created = T('Feature Group added')
    msg_record_modified = T('Feature Group updated')
    msg_record_deleted = T('Feature Group deleted')
    msg_list_empty = T('No Feature Groups currently defined')
    s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)
    
    return shn_rest_controller(module, resource)

def location():
    "RESTlike CRUD controller"
    resource = 'location'
    table = module + '_' + resource
    
    # Model options
    # used in multiple controllers, so at the top of the file

    # CRUD Strings
    title_create = T('Add Location')
    title_display = T('Location Details')
    title_list = T('List Locations')
    title_update = T('Edit Location')
    title_search = T('Search Locations')
    subtitle_create = T('Add New Location')
    subtitle_list = T('Locations')
    label_list_button = T('List Locations')
    label_create_button = ADD_LOCATION
    msg_record_created = T('Location added')
    msg_record_modified = T('Location updated')
    msg_record_deleted = T('Location deleted')
    msg_list_empty = T('No Locations currently available')
    s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)
    
    return shn_rest_controller(module, resource, onvalidation=lambda form: wkt_centroid(form))

def marker():
    "RESTlike CRUD controller"
    resource = 'marker'
    table = module + '_' + resource
    
    # Model options
    db[table].name.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, '%s.name' % table)]
    db[table].name.label = T('Name')
    db[table].name.comment = SPAN("*", _class="req")
    db[table].image.label = T('Image')

    # CRUD Strings
    title_create = T('Add Marker')
    title_display = T('Marker Details')
    title_list = T('List Markers')
    title_update = T('Edit Marker')
    title_search = T('Search Markers')
    subtitle_create = T('Add New Marker')
    subtitle_list = T('Markers')
    label_list_button = T('List Markers')
    label_create_button = ADD_MARKER
    msg_record_created = T('Marker added')
    msg_record_modified = T('Marker updated')
    msg_record_deleted = T('Marker deleted')
    msg_list_empty = T('No Markers currently available')
    s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)
    
    return shn_rest_controller(module, resource)

def metadata():
    "RESTlike CRUD controller"
    resource = 'metadata'
    table = module + '_' + resource
    
    # Model options
    # used in multiple controllers, so at the top of the file

    # CRUD Strings
    title_create = T('Add Metadata')
    title_display = T('Metadata Details')
    title_list = T('List Metadata')
    title_update = T('Edit Metadata')
    title_search = T('Search Metadata')
    subtitle_create = T('Add New Metadata')
    subtitle_list = T('Metadata')
    label_list_button = T('List Metadata')
    label_create_button = T('Add Metadata')
    msg_record_created = T('Metadata added')
    msg_record_modified = T('Metadata updated')
    msg_record_deleted = T('Metadata deleted')
    msg_list_empty = T('No Metadata currently defined')
    s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)
    
    return shn_rest_controller(module, resource)

def projection():
    "RESTlike CRUD controller"
    resource = 'projection'
    table = module + '_' + resource
    
    # Model options
    db[table].uuid.requires = IS_NOT_IN_DB(db, '%s.uuid' % table)
    db[table].name.requires = [IS_NOT_EMPTY(), IS_NOT_IN_DB(db, '%s.name' % table)]
    db[table].name.label = T('Name')
    db[table].name.comment = SPAN("*", _class="req")
    db[table].epsg.requires = IS_NOT_EMPTY()
    db[table].epsg.label = "EPSG"
    db[table].epsg.comment = SPAN("*", _class="req")
    db[table].maxExtent.requires = IS_NOT_EMPTY()
    db[table].maxExtent.label = T('maxExtent')
    db[table].maxExtent.comment = SPAN("*", _class="req")
    db[table].maxResolution.requires = IS_NOT_EMPTY()
    db[table].maxResolution.label = T('maxResolution')
    db[table].maxResolution.comment = SPAN("*", _class="req")
    db[table].units.requires = IS_IN_SET(['m', 'degrees'])
    db[table].units.label = T('Units')

    # CRUD Strings
    title_create = T('Add Projection')
    title_display = T('Projection Details')
    title_list = T('List Projections')
    title_update = T('Edit Projection')
    title_search = T('Search Projections')
    subtitle_create = T('Add New Projection')
    subtitle_list = T('Projections')
    label_list_button = T('List Projections')
    label_create_button = T('Add Projection')
    msg_record_created = T('Projection added')
    msg_record_modified = T('Projection updated')
    msg_record_deleted = T('Projection deleted')
    msg_list_empty = T('No Projections currently defined')
    s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)
    
    return shn_rest_controller(module, resource, deletable=False)

def track():
    "RESTlike CRUD controller"
    resource = 'track'
    table = module + '_' + resource
    
    # Model options
    # used in multiple controllers, so at the top of the file
    
    # CRUD Strings
    title_create = T('Add Track')
    title_display = T('Track Details')
    title_list = T('List Tracks')
    title_update = T('Edit Track')
    title_search = T('Search Tracks')
    subtitle_create = T('Add New Track')
    subtitle_list = T('Tracks')
    label_list_button = T('List Tracks')
    label_create_button = T('Add Track')
    msg_record_created = T('Track added')
    msg_record_modified = T('Track updated')
    msg_record_deleted = T('Track deleted')
    msg_list_empty = T('No Tracks currently available')
    s3.crud_strings[table] = Storage(title_create=title_create,title_display=title_display,title_list=title_list,title_update=title_update,title_search=title_search,subtitle_create=subtitle_create,subtitle_list=subtitle_list,label_list_button=label_list_button,label_create_button=label_create_button,msg_record_created=msg_record_created,msg_record_modified=msg_record_modified,msg_record_deleted=msg_record_deleted,msg_list_empty=msg_list_empty)
    
    return shn_rest_controller(module, resource)

def layer_openstreetmap():
    "RESTlike CRUD controller"
    resource = 'layer_openstreetmap'
    table = module + '_' + resource
    
    # Model options
    db[table].subtype.requires = IS_IN_SET(gis_layer_openstreetmap_subtypes)

    # CRUD Strings
    title_create = T('Add Layer')
    title_display = T('Layer Details')
    title_list = T('List Layers')
    title_update = T('Edit Layer')
    title_search = T('Search Layers')
    subtitle_create = T('Add New Layer')
    subtitle_list = T('Layers')
    label_list_button = T('List OpenStreetMap Layers')
    label_create_button = T('Add Layer')
    msg_record_created = T('Layer added')
    msg_record_modified = T('Layer updated')
    msg_record_deleted = T('Layer deleted')
    msg_list_empty = T('No OpenStreetMap Layers currently defined')
    s3.crud_strings[table] = Storage(title_create=title_create, title_display=title_display, title_list=title_list, title_update=title_update, title_search=title_search, subtitle_create=subtitle_create, subtitle_list=subtitle_list, label_list_button=label_list_button, label_create_button=label_create_button, msg_record_created=msg_record_created, msg_record_modified=msg_record_modified, msg_record_deleted=msg_record_deleted, msg_list_empty=msg_list_empty)
    
    return shn_rest_controller(module, resource, deletable=False)

def layer_google():
    "RESTlike CRUD controller"
    resource = 'layer_google'
    table = module + '_' + resource
    
    # Model options
    db[table].subtype.requires = IS_IN_SET(gis_layer_google_subtypes)

    # CRUD Strings
    title_create = T('Add Layer')
    title_display = T('Layer Details')
    title_list = T('List Layers')
    title_update = T('Edit Layer')
    title_search = T('Search Layers')
    subtitle_create = T('Add New Layer')
    subtitle_list = T('Layers')
    label_list_button = T('List Google Layers')
    label_create_button = T('Add Layer')
    msg_record_created = T('Layer added')
    msg_record_modified = T('Layer updated')
    msg_record_deleted = T('Layer deleted')
    msg_list_empty = T('No Google Layers currently defined')
    s3.crud_strings[table] = Storage(title_create=title_create, title_display=title_display, title_list=title_list, title_update=title_update, title_search=title_search, subtitle_create=subtitle_create, subtitle_list=subtitle_list, label_list_button=label_list_button, label_create_button=label_create_button, msg_record_created=msg_record_created, msg_record_modified=msg_record_modified, msg_record_deleted=msg_record_deleted, msg_list_empty=msg_list_empty)
    
    return shn_rest_controller(module, resource, deletable=False)

def layer_yahoo():
    "RESTlike CRUD controller"
    resource = 'layer_yahoo'
    table = module + '_' + resource
    
    # Model options
    db[table].subtype.requires = IS_IN_SET(gis_layer_yahoo_subtypes)

    # CRUD Strings
    title_create = T('Add Layer')
    title_display = T('Layer Details')
    title_list = T('List Layers')
    title_update = T('Edit Layer')
    title_search = T('Search Layers')
    subtitle_create = T('Add New Layer')
    subtitle_list = T('Layers')
    label_list_button = T('List Yahoo Layers')
    label_create_button = T('Add Layer')
    msg_record_created = T('Layer added')
    msg_record_modified = T('Layer updated')
    msg_record_deleted = T('Layer deleted')
    msg_list_empty = T('No Yahoo Layers currently defined')
    s3.crud_strings[table] = Storage(title_create=title_create, title_display=title_display, title_list=title_list, title_update=title_update, title_search=title_search, subtitle_create=subtitle_create, subtitle_list=subtitle_list, label_list_button=label_list_button, label_create_button=label_create_button, msg_record_created=msg_record_created, msg_record_modified=msg_record_modified, msg_record_deleted=msg_record_deleted, msg_list_empty=msg_list_empty)
    
    return shn_rest_controller(module, resource, deletable=False)

def layer_bing():
    "RESTlike CRUD controller"
    resource = 'layer_bing'
    table = module + '_' + resource
    
    # Model options
    db[table].subtype.requires = IS_IN_SET(gis_layer_bing_subtypes)

    # CRUD Strings
    title_create = T('Add Layer')
    title_display = T('Layer Details')
    title_list = T('List Layers')
    title_update = T('Edit Layer')
    title_search = T('Search Layers')
    subtitle_create = T('Add New Layer')
    subtitle_list = T('Layers')
    label_list_button = T('List Bing Layers')
    label_create_button = T('Add Layer')
    msg_record_created = T('Layer added')
    msg_record_modified = T('Layer updated')
    msg_record_deleted = T('Layer deleted')
    msg_list_empty = T('No Bing Layers currently defined')
    s3.crud_strings[table] = Storage(title_create=title_create, title_display=title_display, title_list=title_list, title_update=title_update, title_search=title_search, subtitle_create=subtitle_create, subtitle_list=subtitle_list, label_list_button=label_list_button, label_create_button=label_create_button, msg_record_created=msg_record_created, msg_record_modified=msg_record_modified, msg_record_deleted=msg_record_deleted, msg_list_empty=msg_list_empty)
    
    return shn_rest_controller(module, resource, deletable=False)

# Module-specific functions
def convert_gps():
    " Provide a form which converts from GPS Coordinates to Decimal Coordinates "
    return dict()

def shn_latlon_to_wkt(lat, lon):
    """Convert a LatLon to a WKT string
    >>> shn_latlon_to_wkt(6, 80)
    'POINT(80 6)'
    """
    WKT = 'POINT(%d %d)' % (lon, lat)
    return WKT

# Onvalidation callback
def wkt_centroid(form):
    """GIS
    If a Point has LonLat defined: calculate the WKT.
    If a Line/Polygon has WKT defined: validate the format & calculate the LonLat of the Centroid
    Centroid calculation is done using Shapely, which wraps Geos.
    A nice description of the algorithm is provided here: http://www.jennessent.com/arcgis/shapes_poster.htm
    """
    #shapely_error = str(A('Shapely', _href='http://pypi.python.org/pypi/Shapely/', _target='_blank')) + str(T(" library not found, so can't find centroid!"))
    shapely_error = T("Shapely library not found, so can't find centroid!")
    if form.vars.gis_feature_type == '1':
        # Point
        if form.vars.lon == None:
            form.errors['lon'] = T("Invalid: Longitude can't be empty!")
            return
        if form.vars.lat == None:
            form.errors['lat'] = T("Invalid: Latitude can't be empty!")
            return
        form.vars.wkt = 'POINT(%(lon)f %(lat)f)' % form.vars
    elif form.vars.gis_feature_type == '2':
        # Line
        try:
            from shapely.wkt import loads
            try:
                line = loads(form.vars.wkt)
            except:
                form.errors['wkt'] = T("Invalid WKT: Must be like LINESTRING(3 4,10 50,20 25)!")
                return
            centroid_point = line.centroid
            form.vars.lon = centroid_point.wkt.split('(')[1].split(' ')[0]
            form.vars.lat = centroid_point.wkt.split('(')[1].split(' ')[1][:1]
        except:
            form.errors.gis_feature_type = shapely_error
    elif form.vars.gis_feature_type == '3':
        # Polygon
        try:
            from shapely.wkt import loads
            try:
                polygon = loads(form.vars.wkt)
            except:
                form.errors['wkt'] = T("Invalid WKT: Must be like POLYGON((1 1,5 1,5 5,1 5,1 1),(2 2, 3 2, 3 3, 2 3,2 2))!")
                return
            centroid_point = polygon.centroid
            form.vars.lon = centroid_point.wkt.split('(')[1].split(' ')[0]
            form.vars.lat = centroid_point.wkt.split('(')[1].split(' ')[1][:1]
        except:
            form.errors.gis_feature_type = shapely_error
    else:
        form.errors.gis_feature_type = T('Unknown type!')
    return

# Features
# - experimental!
def feature_create_map():
    "Show a map to draw the feature"
    title = T("Add GIS Feature")
    form = crud.create('gis_location', onvalidation=lambda form: wkt_centroid(form))
    _projection = db(db.gis_config.id==1).select()[0].projection_id
    projection = db(db.gis_projection.id==_projection).select()[0].epsg

    # Layers
    baselayers = layers()

    return dict(title=title, module_name=module_name, form=form, projection=projection, openstreetmap=baselayers.openstreetmap, google=baselayers.google, yahoo=baselayers.yahoo, bing=baselayers.bing)
    
# Feature Groups
def feature_group_contents():
    "Many to Many CRUD Controller"
    if len(request.args) == 0:
        session.error = T("Need to specify a feature group!")
        redirect(URL(r=request, f='feature_group'))
    feature_group = request.args[0]
    tables = [db.gis_feature_class_to_feature_group, db.gis_location_to_feature_group]
    authorised = shn_has_permission('update', tables[0]) and shn_has_permission('update', tables[1])
    
    title = db.gis_feature_group[feature_group].name
    feature_group_description = db.gis_feature_group[feature_group].description
    # Start building the Return with the common items
    output = dict(module_name=module_name, title=title, description=feature_group_description)
    # Audit
    shn_audit_read(operation='list', resource='feature_group_contents', record=feature_group, representation='html')
    item_list = []
    even = True
    if authorised:
        # Audit
        crud.settings.create_onaccept = lambda form: shn_audit_create(form, module, 'feature_group_contents', 'html')
        # Display a List_Create page with checkboxes to remove items
        
        # Feature Classes
        query = (tables[0].feature_group_id == feature_group) & (tables[0].deleted == False)
        sqlrows = db(query).select()
        for row in sqlrows:
            if even:
                theclass = "even"
                even = False
            else:
                theclass = "odd"
                even = True
            id = row.feature_class_id
            name = db.gis_feature_class[id].name
            description = db.gis_feature_class[id].description
            id_link = A(id, _href=URL(r=request, f='feature_class', args=['read', id]))
            checkbox = INPUT(_type="checkbox", _value="on", _name='feature_class_' + str(id), _class="remove_item")
            item_list.append(TR(TD(id_link), TD(name, _align='left'), TD(description, _align='left'), TD(checkbox, _align='center'), _class=theclass, _align='right'))
            
        # Features
        query = (tables[1].feature_group_id == feature_group) & (tables[1].deleted == False)
        sqlrows = db(query).select()
        for row in sqlrows:
            if even:
                theclass = "even"
                even = False
            else:
                theclass = "odd"
                even = True
            id = row.location_id
            name = db.gis_location[id].name
            # Metadata is M->1 to Features
            metadata = db(db.gis_metadata.location_id==id & db.gis_metadata.deleted==False).select()
            if metadata:
                # We just read the description of the 1st one
                description = metadata[0].description
            else:
                description = ''
            id_link = A(id, _href=URL(r=request, f='location', args=['read', id]))
            checkbox = INPUT(_type="checkbox", _value="on", _name='feature_' + str(id), _class="remove_item")
            item_list.append(TR(TD(id_link), TD(name, _align='left'), TD(description, _align='left'), TD(checkbox, _align='center'), _class=theclass, _align='right'))
        
        table_header = THEAD(TR(TH('ID'), TH('Name'), TH(T('Description')), TH(T('Remove'))))
        table_footer = TFOOT(TR(TD(INPUT(_id='submit_button', _type='submit', _value=T('Update')))), _colspan=3, _align='right')
        items = DIV(FORM(TABLE(table_header, TBODY(item_list), table_footer, _id="table-container"), _name='custom', _method='post', _enctype='multipart/form-data', _action=URL(r=request, f='feature_group_update_items', args=[feature_group])))
        subtitle = T("Contents")
        
        crud.messages.submit_button=T('Add')
        # Check for duplicates before Item is added to DB
        crud.settings.create_onvalidation = lambda form: feature_group_dupes(form)
        crud.messages.record_created = T('Feature Group Updated')
        form1 = crud.create(tables[0], next=URL(r=request, args=[feature_group]))
        form1[0][0].append(TR(TD(T('Type:')), TD(LABEL(T('Feature Class'), INPUT(_type="radio", _name="fg1", _value="FeatureClass", value="FeatureClass")), LABEL(T('Feature'), INPUT(_type="radio", _name="fg1", _value="Feature", value="FeatureClass")))))
        form2 = crud.create(tables[1], next=URL(r=request, args=[feature_group]))
        form2[0][0].append(TR(TD(T('Type:')), TD(LABEL(T('Feature Class'), INPUT(_type="radio", _name="fg2", _value="FeatureClass", value="Feature")), LABEL(T('Feature'), INPUT(_type="radio", _name="fg2", _value="Feature", value="Feature")))))
        addtitle = T("Add to Feature Group")
        response.view = '%s/feature_group_contents_list_create.html' % module
        output.update(dict(subtitle=subtitle, items=items, addtitle=addtitle, form1=form1, form2=form2, feature_group=feature_group))
    else:
        # Display a simple List page
        # Feature Classes
        query = (tables[0].feature_group_id == feature_group) & (tables[0].deleted == False)
        sqlrows = db(query).select()
        for row in sqlrows:
            if even:
                theclass = "even"
                even = False
            else:
                theclass = "odd"
                even = True
            id = row.feature_class_id
            name = db.gis_feature_class[id].name
            description = db.gis_feature_class[id].description
            id_link = A(id, _href=URL(r=request, f='feature_class', args=['read', id]))
            item_list.append(TR(TD(id_link), TD(name, _align='left'), TD(description, _align='left'), _class=theclass, _align='right'))
            
        # Features
        query = (tables[1].feature_group_id == feature_group) & (tables[1].deleted == False)
        sqlrows = db(query).select()
        for row in sqlrows:
            if even:
                theclass = "even"
                even = False
            else:
                theclass = "odd"
                even = True
            id = row.location_id
            name = db.gis_location[id].name
            # Metadata is M->1 to Features
            metadata = db(db.gis_metadata.location_id==id & db.gis_metadata.deleted==False).select()
            if metadata:
                # We just read the description of the 1st one
                description = metadata[0].description
            else:
                description = ''
            id_link = A(id, _href=URL(r=request, f='location', args=['read', id]))
            item_list.append(TR(TD(id_link), TD(name, _align='left'), TD(description, _align='left'), _class=theclass, _align='right'))
        
        table_header = THEAD(TR(TH('ID'), TH('Name'), TH(T('Description'))))
        items = DIV(TABLE(table_header, TBODY(item_list), _id="table-container"))
        
        add_btn = A(T('Edit Contents'), _href=URL(r=request, c='default', f='user', args='login'), _id='add-btn')
        response.view = '%s/feature_group_contents_list.html' % module
        output.update(dict(items=items, add_btn=add_btn))
    return output
	
def feature_group_dupes(form):
    "Checks for duplicate Feature/FeatureClass before adding to DB"
    feature_group = form.vars.feature_group
    if 'feature_class_id' in form.vars:
        feature_class_id = form.vars.feature_class_id
        table = db.gis_feature_class_to_feature_group
        query = (table.feature_group==feature_group) & (table.feature_class_id==feature_class_id)
    elif 'location_id' in form.vars:
        location_id = form.vars.location_id
        table = db.gis_location_to_feature_group
        query = (table.feature_group==feature_group) & (table.location_id==location_id)
    else:
        # Something went wrong!
        return
    items = db(query).select()
    if items:
        session.error = T("Already in this Feature Group!")
        redirect(URL(r=request, args=feature_group))
    else:
        return
    
def feature_group_update_items():
    "Update a Feature Group's items (Feature Classes & Features)"
    if len(request.args) == 0:
        session.error = T("Need to specify a feature group!")
        redirect(URL(r=request, f='feature_group'))
    feature_group = request.args[0]
    tables = [db.gis_feature_class_to_feature_group, db.gis_location_to_feature_group]
    authorised = shn_has_permission('update', tables[0]) and shn_has_permission('update', tables[1])
    if authorised:
        for var in request.vars:
            if 'feature_class_id' in var:
                # Delete
                feature_class_id = var[14:]
                query = (tables[0].feature_group==feature_group) & (tables[0].feature_class_id==feature_class_id)
                db(query).delete()
            elif 'location_id' in var:
                # Delete
                location_id = var[8:]
                query = (tables[1].feature_group==feature_group) & (tables[1].location_id==location_id)
                db(query).delete()
        # Audit
        shn_audit_update_m2m(resource='feature_group_contents', record=feature_group, representation='html')
        session.flash = T("Feature Group updated")
    else:
        session.error = T("Not authorised!")
    redirect(URL(r=request, f='feature_group_contents', args=[feature_group]))

def map_service_catalogue():
    """Map Service Catalogue.
    Allows selection of which Layers are active."""

    title = T('Map Service Catalogue')
    subtitle = T('List Layers')
    # Start building the Return with the common items
    output = dict(module_name=module_name, title=title, subtitle=subtitle)
    
    # Hack: We control all perms from this 1 table
    table = db.gis_layer_openstreetmap
    authorised = shn_has_permission('update', table)
    item_list = []
    even = True
    if authorised:
        # List View with checkboxes to Enable/Disable layers
        for type in gis_layer_types:
            table = db['gis_layer_%s' % type]
            query = table.id > 0
            sqlrows = db(query).select()
            for row in sqlrows:
                if even:
                    theclass = "even"
                    even = False
                else:
                    theclass = "odd"
                    even = True
                if row.description:
                    description = row.description
                else:
                    description = ''
                label = type + '_' + str(row.id)
                if row.enabled:
                    enabled = INPUT(_type="checkbox", value=True, _name=label)
                else:
                    enabled = INPUT(_type="checkbox", _name=label)
                item_list.append(TR(TD(row.name), TD(description), TD(enabled), _class=theclass))
                
        table_header = THEAD(TR(TH('Layer'), TH('Description'), TH('Enabled?')))
        table_footer = TFOOT(TR(TD(INPUT(_id='submit_button', _type='submit', _value=T('Update')), _colspan=3)), _align='right')
        items = DIV(FORM(TABLE(table_header, TBODY(item_list), table_footer, _id="table-container"), _name='custom', _method='post', _enctype='multipart/form-data', _action=URL(r=request, f='layers_enable')))

    else:
        # Simple List View
        for type in gis_layer_types:
            table = db['gis_layer_%s' % type]
            query = table.id > 0
            sqlrows = db(query).select()
            for row in sqlrows:
                if even:
                    theclass = "even"
                    even = False
                else:
                    theclass = "odd"
                    even = True
                if row.description:
                    description = row.description
                else:
                    description = ''
                if row.enabled:
                    enabled = INPUT(_type="checkbox", value='on', _disabled="disabled")
                else:
                    enabled = INPUT(_type="checkbox", _disabled="disabled")
                item_list.append(TR(TD(row.name), TD(description), TD(enabled), _class=theclass))
                
        table_header = THEAD(TR(TH('Layer'), TH('Description'), TH('Enabled?')))
        items = DIV(TABLE(table_header, TBODY(item_list), _id="table-container"))

    output.update(dict(items=items))
    return output

def layers():
    "Provide the Enabled Layers"

    layers = Storage()

    # OpenStreetMap
    layers.openstreetmap = Storage()
    layers_openstreetmap = db(db.gis_layer_openstreetmap.enabled==True).select(db.gis_layer_openstreetmap.ALL)
    for layer in layers_openstreetmap:
        for subtype in gis_layer_openstreetmap_subtypes:
            if layer.subtype == subtype:
                layers.openstreetmap['%s' % subtype] = layer.name
    
    # Google
    layers.google = Storage()
    # Check for Google Key
    try:
        layers.google.key = db(db.gis_apikey.name=='google').select(db.gis_apikey.apikey)[0].apikey
        layers_google = db(db.gis_layer_google.enabled==True).select(db.gis_layer_google.ALL)
        for layer in layers_google:
            for subtype in gis_layer_google_subtypes:
                if layer.subtype == subtype:
                    layers.google['%s' % subtype] = layer.name
                    layers.google.enabled = 1
    except:
        # Redirect to Key entry screen
        session.warning = T('Please enter a Google Key if you wish to use Google Layers')
        redirect(URL(r=request, f=apikey))
            
    # Yahoo
    layers.yahoo = Storage()
    # Check for Yahoo Key
    try:
        layers.yahoo.key = db(db.gis_apikey.name=='yahoo').select(db.gis_apikey.apikey)[0].apikey
        layers_yahoo = db(db.gis_layer_yahoo.enabled==True).select(db.gis_layer_yahoo.ALL)
        for layer in layers_yahoo:
            for subtype in gis_layer_yahoo_subtypes:
                if layer.subtype == subtype:
                    layers.yahoo['%s' % subtype] = layer.name
                    layers.yahoo.enabled = 1
    except:
        # Redirect to Key entry screen
        session.warning = T('Please enter a Yahoo Key if you wish to use Yahoo Layers')
        redirect(URL(r=request, f=apikey))
        
    # Bing (Virtual Earth)
    layers.bing = Storage()
    layers_bing = db(db.gis_layer_bing.enabled==True).select(db.gis_layer_bing.ALL)
    for layer in layers_bing:
        for subtype in gis_layer_bing_subtypes:
            if layer.subtype == subtype:
                layers.bing['%s' % subtype] = layer.name
                
    return layers
    
def layers_enable():
    "Enable/Disable Layers"
    
    # Hack: We control all perms from this 1 table
    table = db.gis_layer_openstreetmap
    authorised = shn_has_permission('update', table)
    if authorised:
        for type in gis_layer_types:
            resource = 'gis_layer_%s' % type
            table = db[resource]
            query = table.id > 0
            sqlrows = db(query).select()
            for row in sqlrows:
                query_inner = table.id==row.id
                var = '%s_%i' % (type, row.id)
                # Read current state
                if db(query_inner).select()[0].enabled:
                    # Old state: Enabled
                    if var in request.vars:
                        # Do nothing
                        pass
                    else:
                        # Disable
                        db(query_inner).update(enabled=False)
                        # Audit
                        shn_audit_update_m2m(resource=resource, record=row.id, representation='html')
                else:
                    # Old state: Disabled
                    if var in request.vars:
                        # Enable
                        db(query_inner).update(enabled=True)
                        # Audit
                        shn_audit_update_m2m(resource=resource, record=row.id, representation='html')
                    else:
                        # Do nothing
                        pass
        session.flash = T("Layers updated")
    else:
        session.error = T("Not authorised!")
    redirect(URL(r=request, f='map_service_catalogue'))

def map_viewing_client():
    """Map Viewing Client.
    Main user UI for viewing the Maps."""
    
    title = T('Map Viewing Client')
    response.title = title

    # Start building the Return with the Framework
    output = dict(title=title, module_name=module_name)
    
    # Config
    width = db(db.gis_config.id==1).select()[0].map_width
    height = db(db.gis_config.id==1).select()[0].map_height
    _projection = db(db.gis_config.id==1).select()[0].projection_id
    projection = db(db.gis_projection.id==_projection).select()[0].epsg
    if 'lat' in request.vars:
        lat = request.vars.lat
    else:
        lat = db(db.gis_config.id==1).select()[0].lat
    if 'lon' in request.vars:
        lon = request.vars.lon
    else:
        lon = db(db.gis_config.id==1).select()[0].lon
    if 'zoom' in request.vars:
        zoom = request.vars.zoom
    else:
        zoom = db(db.gis_config.id==1).select()[0].zoom
    units = db(db.gis_projection.epsg==projection).select()[0].units
    maxResolution = db(db.gis_projection.epsg==projection).select()[0].maxResolution
    maxExtent = db(db.gis_projection.epsg==projection).select()[0].maxExtent
    marker_default = db(db.gis_config.id==1).select()[0].marker_id
    
    # Add the Config to the Return
    output.update(dict(width=width, height=height, projection=projection, lat=lat, lon=lon, zoom=zoom, units=units, maxResolution=maxResolution, maxExtent=maxExtent))
    
    # Layers
    baselayers = layers()
    # Add the Layers to the Return
    output.update(dict(openstreetmap=baselayers.openstreetmap, google=baselayers.google, yahoo=baselayers.yahoo, bing=baselayers.bing))

    # Internal Features
    features = Storage()
    # Features are displayed in a layer per FeatureGroup
    feature_groups = db(db.gis_feature_group.enabled == True).select()
    for feature_group in feature_groups:
        # FIXME: Use OL's Cluster Strategy to ensure no more than 200 features displayed to prevent overloading the browser!
        # - better than doing a server-side spatial query to show ones visible within viewport on every Pan/Zoom!
        groups = db.gis_feature_group
        locations = db.gis_location
        classes = db.gis_feature_class
        metadata = db.gis_metadata
        # Which Features are added to the Group directly?
        link = db.gis_location_to_feature_group
        features1 = db(link.feature_group_id == feature_group.id).select(groups.ALL, locations.ALL, classes.ALL, left=[groups.on(groups.id == link.feature_group_id), locations.on(locations.id == link.location_id), classes.on(classes.id == locations.feature_class_id)])
        # FIXME?: Extend JOIN for Metadata (sortby, want 1 only), Markers (complex logic), Resource_id (need to find from the results of prev query)
        # Which Features are added to the Group via their FeatureClass?
        link = db.gis_feature_class_to_feature_group
        features2 = db(link.feature_group_id == feature_group.id).select(groups.ALL, locations.ALL, classes.ALL, left=[groups.on(groups.id == link.feature_group_id), classes.on(classes.id == link.feature_class_id), locations.on(locations.feature_class_id == link.feature_class_id)])
        # FIXME?: Extend JOIN for Metadata (sortby, want 1 only), Markers (complex logic), Resource_id (need to find from the results of prev query)
        features[feature_group.id] = features1 | features2
        for feature in features[feature_group.id]:
            feature.module = feature.gis_feature_class.module
            feature.resource = feature.gis_feature_class.resource
            if feature.module and feature.resource:
                feature.resource_id = db(db['%s_%s' % (feature.module, feature.resource)].location_id == feature.gis_location.id).select()[0].id
            else:
                feature.resource_id = None
            # 1st choice for a Marker is the Feature's
            marker = feature.gis_location.marker_id
            if not marker:
                # 2nd choice for a Marker is the Feature Class's
                marker = feature.gis_feature_class.marker_id
            if not marker:
                # 3rd choice for a Marker is the default
                marker = marker_default
            feature.marker = db(db.gis_marker.id == marker).select()[0].image
            
            try:
                # Metadata is M->1 to Features
                # We use the most recent one
                query = (db.gis_metadata.location_id == feature.gis_location.id) & (db.gis_metadata.deleted == False)
                metadata = db(query).select(orderby=~db.gis_metadata.event_time)[0]
            except:
                metadata = None
            feature.metadata = metadata

    # Add the Features to the Return
    #output.update(dict(features=features, features_classes=feature_classes, features_markers=feature_markers, features_metadata=feature_metadata))
    output.update(dict(feature_groups=feature_groups, features=features))
    
    return output

def bulk_upload():
    """Custom view to allow bulk uploading of photos which are made into GIS Features.
    Lat/Lon can be pulled from an associated GPX track with timestamp correlation."""
    
    form = crud.create(db.gis_metadata)
    
    form1 = crud.create(db.gis_location)
    
    form_gpx = crud.create(db.gis_track)

    response.title = T('Bulk Uploader')
    
    return dict(form=form, form_gpx=form_gpx, form1=form1)
 