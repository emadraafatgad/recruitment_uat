# from extra.master_data.models.interpol_request import InterpolRequest
from odoo import fields, models , api,_
from datetime import date
from dateutil.relativedelta import relativedelta

from odoo.exceptions import ValidationError


class ClearanceList(models.Model):
    _name = 'clearance.list'
    _order = 'id desc'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']

    state = fields.Selection([('new','New'),('confirmed','Confirmed')],default='new',track_visibility="onchange")
    name = fields.Char(string="Number",readonly=True,default='New')
    reference_no = fields.Char(string="Reference #")
    assign_date = fields.Date()
    receive_date = fields.Date(string="Issued date")
    clearance_list = fields.Many2many('labor.clearance')
    list_total_count = fields.Integer(compute='_compute_value')
    list_now_len = fields.Integer()

    @api.one
    @api.depends('clearance_list')
    def _compute_value(self):
        self.list_total_count = len(self.clearance_list)

    @api.multi
    def action_confirm(self):
        if not self.reference_no:
            raise ValidationError(_('You must enter reference #'))

        self.receive_date = date.today()
        self.list_now_len = len(self.clearance_list)
        for rec in self.clearance_list:
            rec.action_confirm()
        self.state = 'confirmed'

    @api.onchange('clearance_list')
    def domain_list(self):
        line = []
        request = self.env['clearance.list'].search([])
        for record in request:
            for rec in record.clearance_list:
                line.append(rec.id)
        domain = {'clearance_list': [('id', 'not in', line),('state', '=', 'new')]}
        return {'domain': domain}

    @api.multi
    def print_report_excel(self):
        return self.env.ref('clearance_xlx_report_id').report_action(self)

    @api.onchange('clearance_list')
    def onchange_len_list(self):
        if not self.state == 'new':
            if self.list_total_count > self.list_now_len:
                raise ValidationError(_('You cannot add lines in this state'))
            if self.list_total_count < self.list_now_len:
                raise ValidationError(_('You cannot remove lines in this state'))

    @api.multi
    def unlink(self):
        for rec in self:
            if rec.state != 'new':
                raise ValidationError(_('You cannot delete %s as it is not in new state') % rec.name)
        return super(ClearanceList, self).unlink()

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('clearance.list')
        vals['assign_date'] = date.today()
        return super(ClearanceList, self).create(vals)


