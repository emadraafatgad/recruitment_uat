from odoo import fields, models


class Contract(models.Model):
    _inherit = 'hr.contract'

    currency_id = fields.Many2one('res.currency',related='employee_id.currency_id', string="Currency 2", store=True, readonly=False)
    employee_id = fields.Many2one('hr.employee', string='Employee')
    company_id = fields.Many2one('res.company', default=lambda self: self.env.user.company_id)


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    currency_id = fields.Many2one('res.currency', string="Currency 2", readonly=False)
