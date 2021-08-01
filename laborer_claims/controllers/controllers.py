# -*- coding: utf-8 -*-
from odoo import http

# class LaborerClaims(http.Controller):
#     @http.route('/laborer_claims/laborer_claims/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/laborer_claims/laborer_claims/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('laborer_claims.listing', {
#             'root': '/laborer_claims/laborer_claims',
#             'objects': http.request.env['laborer_claims.laborer_claims'].search([]),
#         })

#     @http.route('/laborer_claims/laborer_claims/objects/<model("laborer_claims.laborer_claims"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('laborer_claims.object', {
#             'object': obj
#         })