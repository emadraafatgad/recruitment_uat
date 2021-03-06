{
    'name': 'Show settings menu for non-admin',
    "summary": """Set up non-admin users rights so they can see the ``[[ Settings ]]`` menu""",
    'version': '12.0.1.0.2',
    'author': 'Classera',
    "category": "Access",
    "support": "apps@it-projects.info",
    'website': 'https://twitter.com/yelizariev',
    "license": "LGPL-3",
    'price': 10.00,
    'currency': 'EUR',
    'depends': [
        'access_apps'
    ],
    'data': [
        'security/access_settings_menu_security.xml',
    ],
    'demo': [
        'security/access_settings_menu_security_demo.xml',
    ],
    'installable': True
}
