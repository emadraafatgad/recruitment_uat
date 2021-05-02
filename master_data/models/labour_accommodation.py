from odoo import models, fields,api, _
from odoo.exceptions import ValidationError


class LabourAccommodation(models.Model):
    _name = 'labour.accommodation'
    _order = 'id desc'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _rec_name = 'labour_id'

    labour_id = fields.Many2one('labor.profile',required=True,track_visibility="onchange")
    start_date = fields.Date(track_visibility="onchange")
    end_date = fields.Date(track_visibility="onchange")
    accommodation_period = fields.Integer(track_visibility="onchange",compute='calculate_accommodation_period',store=True)
    training_center = fields.Many2one('res.partner',domain="[('vendor_type','=','training')]", track_visibility="onchange")
    extra_days = fields.Integer()
    national_id = fields.Char(related='labour_id.national_id')
    passport_no = fields.Char(related='labour_id.passport_no')
    state = fields.Selection([('new','New'),('confirm','Confirm'),('invoiced','Invoiced'),('blocked','Blocked')],default='new',track_visibility="onchange")
    accommodation_list_id = fields.Many2one('accommodation.list')
    reasons = fields.Char()

    @api.onchange('labour_id')
    def labour_not_done_accommodation(self):
        accommodation = self.env['labour.accommodation'].search([('labour_id','=',self.labour_id.id),('state','=','new')])
        if self.labour_id:
            for rec in accommodation:
                raise ValidationError(_('There is accommodation for this laborer that is not confirmed in list # %s') % rec.accommodation_list_id.name)

    @api.depends('start_date','end_date','extra_days')
    def calculate_accommodation_period(self):
        for accommodation in self:
            if accommodation.start_date and accommodation.end_date:
                period = accommodation.end_date - accommodation.start_date
                print(period.days,"period")
                accommodation.accommodation_period = period.days + accommodation.extra_days + 1
            else:
                accommodation.accommodation_period = accommodation.extra_days