# -*- coding: utf-8 -*-
from odoo import http

# class UserRouting(http.Controller):
#     @http.route('/user_routing/user_routing/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/user_routing/user_routing/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('user_routing.listing', {
#             'root': '/user_routing/user_routing',
#             'objects': http.request.env['user_routing.user_routing'].search([]),
#         })

#     @http.route('/user_routing/user_routing/objects/<model("user_routing.user_routing"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('user_routing.object', {
#             'object': obj
#         })