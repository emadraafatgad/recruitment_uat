# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.
##############################################################################

from odoo import api, fields, models, _


class monthly_statement_line(models.Model):
    
    _name = 'monthly.statement.line'
    _description = "Monthly Statement Line"
    
    
    company_id = fields.Many2one('res.company', string='Company')
    partner_id = fields.Many2one('res.partner', string='Customer')
    name = fields.Char('Name') 
    date_invoice = fields.Date('Invoice Date')
    date_due = fields.Date('Due Date')
    number = fields.Char('Number')
    result = fields.Float("Balance")
    amount_total = fields.Float("Invoices/Debits")
    credit_amount = fields.Float("Payments/Credits")
    state = fields.Selection([
            ('draft','Draft'),
            ('proforma', 'Pro-forma'),
            ('proforma2', 'Pro-forma'),
            ('open', 'Open'),
            ('paid', 'Paid'),
            ('cancel', 'Cancelled'),
        ], string='Status',)
    invoice_id = fields.Many2one('account.invoice', String='Invoice')
    currency_id = fields.Many2one(related='invoice_id.currency_id')
    amount_total_signed = fields.Monetary(related='invoice_id.amount_total_signed', currency_field='currency_id',)
    residual = fields.Monetary(related='invoice_id.residual')
    residual_signed = fields.Monetary(related='invoice_id.residual_signed', currency_field='currency_id',)
    
    _order = 'date_invoice'
   

