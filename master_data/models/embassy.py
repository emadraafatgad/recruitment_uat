# from extra.master_data.models.interpol_request import InterpolRequest
from odoo import fields, models , api,_
from datetime import date
from dateutil.relativedelta import relativedelta

class LaborEmbassy(models.Model):
    _name = 'labor.embassy'
    _order = 'id desc'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']

    state = fields.Selection([('new','New'),('enjaz','Enjaz'),('stamping','Stamping'),('confirmed','Confirmed')],default='new',track_visibility="onchange")

    name = fields.Char(string="Number",readonly=True,default='New')
    labor_id = fields.Many2one('labor.profile')
    passport_no = fields.Char()
    interpol_no = fields.Char()
    enjaz_no = fields.Char()
    city = fields.Char()
    employer = fields.Char()
    visa_no = fields.Char('Visa #')
    visa_date = fields.Date()
    visa_expiry_date = fields.Date()
    agency = fields.Many2one('res.partner',domain=[('agency','=',True)])
    big_medical = fields.Selection([('fit', 'Fit'), ('unfit', 'Unfit'), ('pending', 'Pending')],
                                   track_visibility="onchange")

    @api.onchange('visa_date')
    def onchange_date(self):
        if self.visa_date:
            self.visa_expiry_date = (self.visa_date + relativedelta(days=90)).strftime('%Y-%m-%d')

    @api.multi
    def action_enjaz(self):
        self.state = 'enjaz'
    @api.multi
    def action_stamp(self):
        self.state = 'stamping'
    @api.multi
    def action_confirm(self):
        self.state = 'confirmed'
    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('labor.embassy')
        return super(LaborEmbassy, self).create(vals)


