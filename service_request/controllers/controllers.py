# -*- coding: utf-8 -*-
from odoo import http

# class ClasseraSchoolAdmission(http.Controller):
#     @http.route('/classera_school_admission/classera_school_admission/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/classera_school_admission/classera_school_admission/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('classera_school_admission.listing', {
#             'root': '/classera_school_admission/classera_school_admission',
#             'objects': http.request.env['classera_school_admission.classera_school_admission'].search([]),
#         })

#     @http.route('/classera_school_admission/classera_school_admission/objects/<model("classera_school_admission.classera_school_admission"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('classera_school_admission.object', {
#             'object': obj
#         })