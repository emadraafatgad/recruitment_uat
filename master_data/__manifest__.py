# -*- coding: utf-8 -*-
{
    'name': "Recruitment",

    'summary': """
        Create Labor -
        Create Broker - 
        Create Agent -
        """,
    'description': """
        Long description of module's purpose
    """,

    'author': "Emad Raafat",

    'category': 'HR',
    'version': '0.1',
    'depends': ['base','account','product','hr','mail','report_xlsx','muk_web_searchpanel'],
    'data': [
        'security/registeration_security.xml',
        'views/menus.xml',
        'security/sequence.xml',
        'security/ir.model.access.csv',
        "views/labor_skills.xml",
        "views/training_center.xml",
        "views/partner_form.xml",
        "views/labor_profile.xml",
        'views/passport_request.xml',
        'views/nira_letter.xml',
        'views/nira_broker.xml',
        'views/interpol_request.xml',
        'views/passport_make_invoice.xml',
        'views/configration.xml',
        'views/passport_broker.xml',
        'views/interpol_broker.xml',
        'views/laborer_specification.xml',
        'views/labor_address.xml',
        'views/big_medical.xml',
        'views/big_medical_interpol.xml',
        'views/medical_list.xml',
        'views/specify_agency.xml',
        'views/enjaz_stamping.xml',
        'views/stamping_list.xml',
        'views/clearance.xml',
        'views/clearance_list.xml',
        'views/travel_company.xml',
        'views/travel_list.xml',
        'views/labor_process.xml',
        #'views/embassy.xml',
        #'views/embassy_list.xml',
        'report/cv_report.xml',
        'report/passport_broker_report.xml',
        'report/interpol_broker_report.xml',
        'report/report_ids.xml',
        'views/labour_accommodation.xml',
        'views/pcr_exam.xml',
        'views/pcr_exam_list.xml',
        'views/accommodation_list.xml',
        'views/labor_profile_inherit.xml',
    ],

}
