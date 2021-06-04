from odoo import fields, models , api
from datetime import date
from dateutil.relativedelta import relativedelta


class LaborStamping(models.Model):
    _name = 'labor.stamping'
    _description = 'LaborStamping'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(string="Number",track_visibility="onchange",readonly=True,default='New')
    labor_id = fields.Many2one('labor.profile')
    agency = fields.Many2one('res.partner',track_visibility="onchange",domain=[('customer','=',True)])
    employer = fields.Char()
    visa_no = fields.Char('Visa #')
    state = fields.Selection([('new','New'),('confirmed','Confirmed')],default='new',track_visibility="onchange")
    passport_no = fields.Char()
    interpol_no = fields.Char('Interpol No')
    city = fields.Char()
    visa_date = fields.Date()
    visa_expiry_date = fields.Date()
    big_medical = fields.Selection([('fit', 'Fit'),('unfit', 'Unfit'),('pending', 'Pending')],track_visibility="onchange")

    @api.onchange('visa_date')
    def onchange_date(self):
        if self.visa_date:
            self.visa_expiry_date = (self.visa_date + relativedelta(days=90)).strftime('%Y-%m-%d')

    @api.multi
    def action_confirm(self):
        self.env['labor.embassy'].create({
            'labor_id': self.labor_id.id,
            'passport_no': self.passport_no,
            'interpol_no': self.interpol_no,
            'visa_date': self.visa_date,

        })
        self.state = 'confirmed'
    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('labor.stamping')
        return super(LaborStamping, self).create(vals)

class LaborProfile(models.Model):
    _inherit = 'labor.profile'