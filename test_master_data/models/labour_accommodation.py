from odoo import models, fields,api, _


class LabourAccommodation(models.Model):
    _name = 'labour.accommodation'
    _order = 'id desc'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _rec_name = 'labour_id'
    # name = fields.Char()
    labour_id = fields.Many2one('labor.profile',required=True,track_visibility="onchange")
    start_date = fields.Date(track_visibility="onchange")
    end_date = fields.Date(track_visibility="onchange")
    accommodation_period = fields.Integer(track_visibility="onchange",compute='calculate_accommodation_period',store=True)
    training_center = fields.Many2one('training.center',track_visibility="onchange")
    extra_days = fields.Integer()
    national_id = fields.Char(related='labour_id.national_id')
    passport_no = fields.Char(related='labour_id.passport_no')
    state = fields.Selection([('new','New'),('confirm','Confirm'),('invoiced','Invoiced')],)
    @api.depends('start_date','end_date','extra_days')
    def calculate_accommodation_period(self):
        for accommodation in self:
            if accommodation.start_date and accommodation.end_date:
                period = accommodation.end_date - accommodation.start_date
                print(period.days,"period")
                accommodation.accommodation_period = period.days + accommodation.extra_days + 1
            else:
                accommodation.accommodation_period = accommodation.extra_days