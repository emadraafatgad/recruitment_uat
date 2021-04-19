
from odoo import fields, models , api,_


class LaborProcess(models.Model):
    _name = 'labor.process'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']

    name = fields.Many2one('labor.profile', track_visibility="onchange")
    labor_process = fields.One2many('labor.process.line','process_id', track_visibility="onchange")




