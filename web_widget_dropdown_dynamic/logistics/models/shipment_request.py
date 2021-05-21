from odoo import models, fields, api

class ContainerRequest(models.Model):
     _name = 'shipment.request'
     _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
     _description = 'Shipment Request'
     _rec_name = 'bill_of_lading'

     state = fields.Selection([('draft', 'Draft') ,('waiting', 'Waiting'),('confirmed', 'Confirmed')], default='draft')
     bill_of_lading = fields.Char('Bill Of Lading')
     container_no = fields.Integer('Container No')
     product_id = fields.Many2one('product.product',string='Product')
     partner_id = fields.Many2one('res.partner',string='Shipment Company')
     customer = fields.Many2one('res.partner',string='Customer')
     request_date = fields.Datetime('Request Date', readonly=True,default=fields.Datetime.now)
     delivery_date = fields.Date('Delivery Date')
     from_port = fields.Many2one('container.port', string='From Port')
     to_port = fields.Many2one('container.port', string='To Port')



     @api.multi
     def action_confirm(self):
          self.state = 'confirmed'


