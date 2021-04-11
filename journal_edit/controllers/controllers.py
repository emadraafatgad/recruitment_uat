# -*- coding: utf-8 -*-
from odoo import http

# class JournalEdit(http.Controller):
#     @http.route('/journal_edit/journal_edit/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/journal_edit/journal_edit/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('journal_edit.listing', {
#             'root': '/journal_edit/journal_edit',
#             'objects': http.request.env['journal_edit.journal_edit'].search([]),
#         })

#     @http.route('/journal_edit/journal_edit/objects/<model("journal_edit.journal_edit"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('journal_edit.object', {
#             'object': obj
#         })