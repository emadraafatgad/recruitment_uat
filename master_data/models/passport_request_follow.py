from odoo import models, fields, api
from datetime import date


class PassportRequestFollow(models.Model):
    _name = 'passport.request.follow'
    _inherit = 'mail.thread'
    _description = 'Passport Request Following'
    _rec_name = 'name'
    _order = 'id desc'

    name = fields.Char(string="Number", readonly=True)
    state = fields.Selection(
        [('new', 'New'), ('to_invoice', 'To Invoice'), ('invoiced', 'Invoiced'), ('releasing', 'Releasing'),
         ('done', 'Done')], default='new', track_visibility="onchange")
    broker = fields.Many2one("res.partner", string="Broker")
    date = fields.Date('Delivery Date')
    passport_request = fields.Many2many('passport.request', string='Passport Requests')

    @api.multi
    def action_assign(self):
        self.state = 'releasing'
        self.date = date.today()
        for rec in self.passport_request:
            rec.end_date = date.today()
            rec.state = 'releasing'

    @api.multi
    def action_done(self):
        for rec in self.passport_request:
            rec.state = 'done'
        self.state = 'done'

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('passport.request.follow')
        return super(PassportRequestFollow, self).create(vals)
