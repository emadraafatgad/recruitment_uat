{
    'name': 'Restricted administration rights',
    'version': '12.0.1.3.5',
    'author': 'Classera',
    "category": "Access",
    "support": "apps@it-projects.info",
    'website': 'https://apps.odoo.com/apps/modules/12.0/access_restricted/',
    "license": "LGPL-3",
    'depends': ['ir_rule_protected'],
    'data': [
        'security/access_restricted_security.xml',
    ],
    'installable': True
}
