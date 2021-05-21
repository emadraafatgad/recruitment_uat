
from odoo import models,fields,api
class StockLocationUserRoute(models.Model):
    _inherit = 'stock.location.route'
    user_ids = fields.Many2many('res.users')
