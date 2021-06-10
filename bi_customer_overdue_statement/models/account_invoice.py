# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.
##############################################################################

from odoo import api, fields, models, _


class account_invoice(models.Model):

    _inherit = 'account.invoice'
    _order = 'date_due'

    @api.multi
    def _get_result(self):
        for aml in self:
            aml.result = aml.amount_total_signed - aml.credit_amount

    @api.multi
    def _get_credit(self):
        for aml in self:
            aml.credit_amount = aml.amount_total_signed - aml.residual_signed

    credit_amount = fields.Float(compute='_get_credit',   string="Credit/paid")
    # 'balance' field is not the same
    result = fields.Float(compute='_get_result',   string="Balance")
    excluded = fields.Boolean(string='Excluded')
    legacy_number = fields.Char("Legacy Number")
