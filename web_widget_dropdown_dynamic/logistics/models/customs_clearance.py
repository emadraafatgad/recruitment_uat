from odoo import models, fields, api,_
from datetime import date
from odoo.exceptions import ValidationError

class CustomsClearance(models.Model):
    _name = 'customs.clearance'
    _description = 'Clearance'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    name =fields.Char('Sequence',default='New',readonly=True)
    state = fields.Selection([('new', 'New'),('confirmed', 'Confirmed')], default='new', track_visibility="onchange")
    order_ids = fields.Many2many('operation.order')
    agree_qty = fields.Float('Total Qty',compute='compute_total')
    raw_supplier = fields.Many2one('res.partner',domain=[('supplier','=',True)],string='Supplier')
    concentration = fields.Char('Grade')
    pol = fields.Many2one('container.port',string='POL')
    arrival_port = fields.Many2one('container.port',string='POD')
    bank= fields.Many2one('res.partner',domain=[('partner_type','=','bank')])
    price= fields.Float('Unit Rate')
    amount = fields.Float(compute='compute_total')
    total_after_increase = fields.Float(compute='compute_total',string='Total Amount After 10%')
    supplier_invoice = fields.Char()
    export_agree = fields.Char()
    bank_certificate = fields.Char()
    port_send_date = fields.Date('Issued Date')
    country = fields.Many2one('res.country')
    agree_expiry_date = fields.Date('Expiry Date')

    @api.multi
    @api.depends('order_ids')
    def compute_total(self):
        for rec in self:
            for line in rec.order_ids:
                rec.agree_qty += line.total_weight
                rec.amount += line.amount
                rec.total_after_increase += line.total_after_increase

    @api.multi
    def action_confirm(self):
        if not self.order_ids:
            raise ValidationError(_('You must enter at least one line!'))
        for record in self.order_ids:
            record.agree = self.name
            record.clearance_finished = True
            if not record.bank_certificate:
                raise ValidationError(_('You must enter all Bank certificate!'))
        self.state = 'confirmed'

    @api.onchange('arrival_port')
    def onchange_pod(self):
        if self.arrival_port:
           domain = {'country': [('id', '=', self.arrival_port.country_id.id)]}
           self.country = self.arrival_port.country_id.id
           return {'domain': domain}


    @api.onchange('country')
    def onchange_country(self):
        if self.country:
            domain = {'arrival_port': [('country_id', '=', self.country.id)]}
            return {'domain': domain}

    @api.model
    def _get_same_port(self):
        operation = self.env['operation.order'].search([('arrival_port', '=', self.arrival_port.id),('shipment_port', '=', self.pol.id),('agree', '=', False),('price_unit', '=', self.price),('status', '=', 'done')])
        t = []
        for line in operation:
            t.append(line.id)
        return t


    @api.onchange('arrival_port', 'price', 'pol')
    def get_domain(self):
        if self.arrival_port and self.pol and self.price > 0:
            get_port = self._get_same_port()
            domain = {'order_ids': [('id', 'in',get_port)]}
            return {'domain': domain}
        else:
            domain = {'order_ids': [('id', '=', False)]}
            return {'domain': domain}


    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('customs.clearance')
        return super(CustomsClearance, self).create(vals)
