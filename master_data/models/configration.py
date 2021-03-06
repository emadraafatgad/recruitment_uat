from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class ProductConfig(models.Model):
    _name = 'product.recruitment.config'
    _description = 'Product Config'
    _rec_name = 'type'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _sql_constraints = [
        ('type_uniq', 'unique (type)', 'Type is already exist')
    ]

    product = fields.Many2one('product.product', track_visibility="onchange")
    price = fields.Float(string="Amount", track_visibility="onchange")
    currency_id = fields.Many2one('res.currency', track_visibility="onchange", required=True)
    journal_id = fields.Many2one('account.journal', track_visibility="onchange")
    type = fields.Selection([('pre_medical_check', 'Pre Medical Check'), ('agent', 'Agent'), ('nira', 'Nira Broker'),
                             ('passport', 'Passport Broker'), ('passport_placing_issue', 'Internal affairs'),
                             ('interpol', 'Interpol Broker'), ('gcc', 'GCC'), ('hospital', 'Big Medical'),
                             ('agency', 'Agency'), ('enjaz', 'Enjaz'), ('embassy', 'Stamping'),
                             ('travel_company', 'Travel'), ('training', 'Training'), ('lab', 'Lab'),
                             ('accommodation', 'Accommodation'),
                             ('labor_reject', 'Labor Reject')],
                            string='Type', track_visibility="onchange", required=True)

    @api.constrains('price')
    def constrains_price(self):
        if self.type in ('pre_medical_check', 'gcc', 'nira', 'enjaz', 'embassy') and self.price <= 0:
            raise ValidationError(_('you must enter price.'))
