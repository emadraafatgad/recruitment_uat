from odoo import models,fields,api
class StockLocation(models.Model):
    _inherit = 'stock.location'
    _sql_constraints = [('user_uniq', 'unique(user)', 'User must be unique!')]
    user = fields.Many2one('res.users')
    @api.constrains('user')
    def location_user(self):
        if self.user:
            user = self.env['res.users'].search(
                [('id', '=', self.user.id)])
            user.restrict_locations= True
            l = []
            l.append(self.id)
            user.stock_location_ids = l

