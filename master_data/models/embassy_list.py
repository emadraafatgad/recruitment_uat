# from extra.master_data.models.interpol_request import InterpolRequest
from odoo import fields, models, api, _
from datetime import date
from dateutil.relativedelta import relativedelta

from odoo.exceptions import ValidationError


class EmbassyList(models.Model):
    _name = 'embassy.list'
    _order = 'id desc'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']

    state = fields.Selection([('new', 'New'), ('confirmed', 'Confirmed')], default='new', track_visibility="onchange")
    name = fields.Char(string="Number", readonly=True, default='New', track_visibility="onchange")
    assign_date = fields.Date(track_visibility="onchange")
    receive_date = fields.Date(track_visibility="onchange")
    embassy_list = fields.Many2many('labor.embassy', track_visibility="onchange")

    @api.multi
    def action_confirm(self):
        self.receive_date = date.today()
        for rec in self.embassy_list:
            rec.state = 'confirmed'
        self.state = 'confirmed'

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('embassy.list')
        vals['assign_date'] = date.today()
        return super(EmbassyList, self).create(vals)

    @api.onchange('embassy_list')
    def onchange_len_list(self):
        if not self.state == 'new':
            if self.list_total_count > self.list_now_len:
                raise ValidationError(_('You cannot add lines in this state'))
            if self.list_total_count < self.list_now_len:
                raise ValidationError(_('You cannot remove lines in this state'))
