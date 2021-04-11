from odoo import models, fields, api


class WorkingState(models.Model):
    _name = 'working.state'

    name = fields.Char('Name')
