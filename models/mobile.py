# -*- coding: utf-8 -*-

"""
    Mobile Messaging
"""

module = 'mobile'

# Settings
resource = 'settings'
tablename = "%s_%s" % (module, resource)
table = db.define_table(tablename,
                Field('account_name'), # Nametag to remember account
                Field('modem_port'),                              # Port for the modem
                Field('modem_baud', 'integer', default = 115200), # Modem Baud rate
                Field('url', default = 'https://api.clickatell.com/http/sendmsg'), # URL for Gateway
                Field('parameters', default =\
                    'user=yourusername&password=yourpassword&api_id=yourapiid'), # Other Parameters
                Field('message_variable', 'string', default = 'text'), # Variable for message
                Field('to_variable', 'string', default = 'to'), # Variable for message
#                Field('preference', 'integer', default = 5), # Weight for the setting
                migrate=migrate)
table.to_variable.label = T('To variable')
table.message_variable.label = T('Message variable')
table.modem_port.label = T('Port')
table.modem_baud.label = T('Baud')

# SMS store for persistence and scratch pad for combining incoming xform chunks
resource = 'store'
tablename = "%s_%s" % (module, resource)
table = db.define_table(tablename,
                Field('sender','string', length = 20),
                Field('fileno','integer'),
                Field('totalno','integer'),
                Field('partno','integer'),
                Field('message','string', length = 160),
            migrate=migrate)
