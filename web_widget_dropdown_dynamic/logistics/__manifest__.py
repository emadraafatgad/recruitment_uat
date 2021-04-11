# -*- coding: utf-8 -*-
{
    'name': "Elwaha Logistics ...",

    'summary': """
       create operation plan for contacts 
       create related fields 
       
       """,

    'description': """
       all users add new operation and shipment plan and containers
    """,

    'author': "Emad ",
    'website': "http://www.emad.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'logistics',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','mail','contract','stock'],

    # always loaded
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        #'views/shipment_request.xml',
        'views/delivery_plan.xml',
        'views/operation.xml',
        'views/operation_order_mrp.xml',
        'views/customs_clearance.xml',
        'views/order_report.xml',
        'views/invoice_report.xml',
        'views/account_invoice.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}