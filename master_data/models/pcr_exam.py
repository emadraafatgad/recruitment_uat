from odoo import fields, models, api


class PCRExam(models.Model):
    _name = 'pcr.exam'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(readonly=True,default='#')

    booking_date = fields.Date()
    labour_id = fields.Many2one('labor.profile')
    exam_date = fields.Date(string="Test Date")
    passport_no = fields.Char(related='labour_id.passport_no')
    national_id = fields.Char(related='labour_id.national_id')
    state = fields.Selection(
        [('new', 'new'), ('in_progress', 'InProgress'), ('positive', 'Positive'), ('negative', 'Negative'),('blocked','Blocked')],
        default='new', track_visibility='onchange')
    note = fields.Char()
    # result = fields.Selection([('positive','positive'),('negative','negative')])

    @api.multi
    def action_positive(self):
        self.state = 'positive'

    @api.multi
    def action_negative(self):
        self.state = 'negative'

    @api.model
    def create(self, vals):
        sequence = self.env['ir.sequence'].next_by_code('pcr.exam')
        vals['name'] = sequence
        return super(PCRExam, self).create(vals)
