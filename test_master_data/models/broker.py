from odoo import fields, models,api,_
from datetime import date


class PassportBroker(models.Model):
    _name = 'passport.broker'
    _order = 'id desc'
    _description = 'Broker Assign'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']


    broker = fields.Many2one('res.partner')
    assign_date = fields.Date(default=date.today())
    passport_request = fields.Many2many('passport.request', string='Passport Requests',required=True)
    state = fields.Selection([('new', 'new'), ('assigned', 'Assigned'),], default='new', track_visibility="onchange")
    @api.multi
    def action_assign(self):
        for list in self.passport_request:
            list.state= 'releasing'
            list.end_date= self.assign_date
        self.state = 'assigned'
