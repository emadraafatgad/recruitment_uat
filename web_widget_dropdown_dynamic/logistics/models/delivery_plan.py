from odoo import models, fields, api,_
from odoo.exceptions import ValidationError

class DeliveryPLan(models.Model):
    _name = 'delivery.plan'
    _description = 'Delivery Plan'
    _rec_name = 'origin'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']

    name =fields.Char('Plan ref',default='New',readonly=True)
    origin =fields.Char("Contract Ref")
    state = fields.Selection([('new', 'New'),('shipment', 'Confirmed')],string="status", default='new', track_visibility="onchange")
    partner_id = fields.Many2one('res.partner',string='Client',readonly=True, required=True,domain=[('partner_type','=','client')])
    # product_id = fields.Many2many('product.product', string='Commodity', required=True)
    shipment_company = fields.Many2one('res.partner',readonly=True,string="Forwarder",domain=[('partner_type','=','forwarder')])
    line_ids = fields.One2many('operation.order','shipment_plan')
    shipment_lines = fields.One2many('delivery.plan.line','shipment_plan')
    locked = fields.Boolean(compute='compute_lock')
    contract_id = fields.Many2one('sale.order')
    partial_shipment = fields.Selection([
        ('allowed', 'Allowed'),
        ('not_allowed', 'Not Allowed')], required=True)
    company_id = fields.Many2one('res.company')

    @api.depends('line_ids')
    def compute_lock(self):
        qty = 0.0
        for line in self.line_ids:
            qty += line.total_weight
        if qty == self.quantity:
           self.locked = True
        else:
            self.locked = False


    @api.multi
    def action_confirm(self):
        if not self.company_id:
            raise ValidationError(_('You must enter company.'))
        self.state = 'shipment'

    @api.multi
    def create_order(self):
        view_id = self.env.ref('logistics.view_operation_order_form')
        return {
            'name': _('New Operation Order'),
            'type': 'ir.actions.act_window',
            'res_model': 'operation.order',
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
            'view_id': view_id.id,
            'views': [(view_id.id, 'form')],
            'context': {
                'default_shipment_plan': self.id,
                'default_forwarder': self.shipment_company.id,
                'default_contract_no': self.origin,
                'default_company_id': self.company_id.id,

            }

        }

    @api.multi
    def unlink(self):
        for rec in self:
            if rec.origin:
                raise ValidationError(_('You cannot delete %s as it comes from contract') % rec.name)
            if rec.state != 'new':
                raise ValidationError(_('You cannot delete %s as it is confirmed') % rec.name)
        return super(DeliveryPLan, self).unlink()

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('delivery.plan')
        return super(DeliveryPLan, self).create(vals)

class LoadingPlace(models.Model):
    _name = 'loading.place'
    _description = 'Loading Place'
    name = fields.Char(required=True)


class DeliveryPlanLine(models.Model):
    _name = 'delivery.plan.line'
    _description = 'Delivery Plan Line'
    _rec_name = 'product_id'

    shipment_plan = fields.Many2one('delivery.plan')
    product_id = fields.Many2one('product.product', string='Commodity', required=True)
    description = fields.Char()
    quantity = fields.Float(required=True, string="QTY")
    price_unit = fields.Float(string="Unit Rate", required=True)
    delivery_date = fields.Many2one('estimated.date', string="ETD", required=True)
    from_port = fields.Many2one('container.port', string='POL', required=True)
    to_port = fields.Many2one('container.port', string='POD', required=True)
    packing = fields.Many2one('product.packing', string='Packing', required=True)
    contract_id = fields.Many2one('sale.order')
