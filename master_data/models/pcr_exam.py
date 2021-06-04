from odoo import fields, models, api


class PCRExam(models.Model):
    _name = 'pcr.exam'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(readonly=True, default='#')

    booking_date = fields.Date()
    labour_id = fields.Many2one('labor.profile')
    exam_date = fields.Date(string="Test Date")
    passport_no = fields.Char(related='labour_id.passport_no', store=True)
    national_id = fields.Char(related='labour_id.national_id', store=True)
    state = fields.Selection(
        [('new', 'new'), ('in_progress', 'InProgress'), ('positive', 'Positive'), ('negative', 'Negative'),
         ('blocked', 'Blocked')],
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


class LaborProfile(models.Model):
    _inherit = 'labor.profile'

    pcr_exam_ids = fields.One2many('pcr.exam', 'labour_id')
    pcr_state = fields.Selection(
        [('new', 'new'), ('in_progress', 'InProgress'), ('positive', 'Positive'), ('negative', 'Negative'),
         ('blocked', 'Blocked')],
        store=True, compute='get_pcr_state')

    @api.depends('pcr_exam_ids.state')
    def get_pcr_state(self):
        for rec in self:
            pcr = self.env['pcr.exam'].search([('labour_id', '=', rec.id)])
            rec.pcr_state = pcr.state
