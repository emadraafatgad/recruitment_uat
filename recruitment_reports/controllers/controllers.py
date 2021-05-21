# -*- coding: utf-8 -*-
from odoo import http

# class RecruitmentReports(http.Controller):
#     @http.route('/recruitment_reports/recruitment_reports/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/recruitment_reports/recruitment_reports/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('recruitment_reports.listing', {
#             'root': '/recruitment_reports/recruitment_reports',
#             'objects': http.request.env['recruitment_reports.recruitment_reports'].search([]),
#         })

#     @http.route('/recruitment_reports/recruitment_reports/objects/<model("recruitment_reports.recruitment_reports"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('recruitment_reports.object', {
#             'object': obj
#         })