# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.
##############################################################################

from odoo import fields, models


class bi_statement_line(models.Model):
    _name = 'bi.statement.line'
    _description = "Customer Statement Line"

    company_id = fields.Many2one('res.company', string='Company')
    partner_id = fields.Many2one('res.partner', string='Customer')
    name = fields.Char('Name')
    date_invoice = fields.Date('Invoice Date')
    date_due = fields.Date('Due Date')
    labour_id = fields.Many2one('labor.profile')
    employer = fields.Char()
    number = fields.Char('Number')
    origin = fields.Char(string='Source Document',
                         help="Reference of the document that generated this sales order request.")
    legacy_number = fields.Char(string="Legacy Number")
    note = fields.Char(string='Note')
    result = fields.Float("Balance")
    amount_total = fields.Float("Invoices/Debits")
    credit_amount = fields.Float("Payments/Credits")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('proforma', 'Pro-forma'),
        ('proforma2', 'Pro-forma'),
        ('open', 'Open'),
        ('paid', 'Paid'),
        ('cancel', 'Cancelled'),
    ], string='Status', )
    invoice_id = fields.Many2one('account.invoice', String='Invoice')
    payment_id = fields.Many2one('account.payment', String='Payment')
    currency_id = fields.Many2one(related='invoice_id.currency_id')
    amount_total_signed = fields.Monetary(
        related='invoice_id.amount_total_signed', currency_field='currency_id', )
    residual = fields.Monetary(related='invoice_id.residual')
    residual_signed = fields.Monetary(
        related='invoice_id.residual_signed', currency_field='currency_id', )
    excluded = fields.Boolean(string="Excluded")

    _order = 'date_invoice'


class bi_vendor_statement_line(models.Model):
    _name = 'bi.vendor.statement.line'
    _description = "Vendor Statement Line"

    company_id = fields.Many2one('res.company', string='Company')
    partner_id = fields.Many2one('res.partner', string='Customer')
    labour_id = fields.Many2one('labor.profile')
    employer = fields.Char()
    name = fields.Char('Name')
    date_invoice = fields.Date('Invoice Date')
    date_due = fields.Date('Due Date')
    number = fields.Char('Number')
    result = fields.Float("Balance")
    amount_total = fields.Float("Invoices/Debits")
    credit_amount = fields.Float("Payments/Credits")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('proforma', 'Pro-forma'),
        ('proforma2', 'Pro-forma'),
        ('open', 'Open'),
        ('paid', 'Paid'),
        ('cancel', 'Cancelled'),
    ], string='Status', )
    invoice_id = fields.Many2one('account.invoice', String='Invoice')
    payment_id = fields.Many2one('account.payment', String='Payment')
    currency_id = fields.Many2one(related='invoice_id.currency_id')
    amount_total_signed = fields.Monetary(
        related='invoice_id.amount_total_signed', currency_field='currency_id', )
    residual = fields.Monetary(related='invoice_id.residual')
    residual_signed = fields.Monetary(
        related='invoice_id.residual_signed', currency_field='currency_id', )

    _order = 'date_invoice'
