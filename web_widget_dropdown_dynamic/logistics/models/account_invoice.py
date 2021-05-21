from odoo import fields, api, models, _
from odoo.tools import email_re, email_split, email_escape_char, float_is_zero, float_compare, \
    pycompat, date_utils


class SpecialDiscount(models.Model):
    _name = 'special.discount'

    product_id = fields.Many2one('product.product')
    name = fields.Char('Description',required=True)
    product_qty= fields.Integer(required=True,default=1)
    price_unit = fields.Float(required=True)
    price_subtotal = fields.Monetary(string='Subtotal Amount', store=True, readonly=True, currency_field='currency_id',
                                     compute='_compute_amount',
                                      track_visibility='always')
    invoice_id = fields.Many2one('account.invoice')
    currency_id = fields.Many2one('res.currency',related='invoice_id.currency_id')
    account_id = fields.Many2one('account.account',required=True)

    @api.depends('product_qty', 'price_unit')
    def _compute_amount(self):
        for line in self:
            # taxes = line.taxes_id.compute_all(line.price_unit, line.order_id.currency_id, line.product_qty, product=line.product_id, partner=line.order_id.partner_id)
            line.update({
                'price_subtotal': line.product_qty * line.price_unit
            })


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    advanced_payment = fields.Float()
    discount_amount = fields.Monetary(string='Discount Total',
        store=True, readonly=True, compute='_compute_amount')

    # special_discount_ids = fields.One2many('special.discount','invoice_id')
    bl_no = fields.Char()
    ship_date = fields.Date()
    ship_via = fields.Char()
    pol = fields.Many2one('container.port', string='Port Of Loading')
    pod = fields.Many2one('container.port', string='Port Of Discharge')
    vessel_voyage_no = fields.Char(string='Vessel & Voyage No')

    @api.multi
    def action_invoice_open(self):
        origin = self.env['operation.order'].search([('name', '=', self.origin)])
        for org in origin:
            org.invoice_id = self.id
        return super(AccountInvoice , self).action_invoice_open()

    # @api.one
    # @api.depends('invoice_line_ids.price_subtotal', 'tax_line_ids.amount', 'tax_line_ids.amount_rounding',
    #              'currency_id','special_discount_ids.price_subtotal', 'company_id', 'date_invoice', 'type')
    # def _compute_amount(self):
    #     round_curr = self.currency_id.round
    #     self.amount_untaxed = sum(line.price_subtotal for line in self.invoice_line_ids)
    #     self.amount_tax = sum(round_curr(line.amount_total) for line in self.tax_line_ids)
    #     self.discount_amount = sum(line.price_subtotal for line in self.special_discount_ids)
    #     self.amount_total = self.amount_untaxed + self.amount_tax - self.discount_amount
    #     amount_total_company_signed = self.amount_total
    #     amount_untaxed_signed = self.amount_untaxed
    #     if self.currency_id and self.company_id and self.currency_id != self.company_id.currency_id:
    #         currency_id = self.currency_id
    #         amount_total_company_signed = currency_id._convert(self.amount_total, self.company_id.currency_id,
    #                                                            self.company_id,
    #                                                            self.date_invoice or fields.Date.today())
    #         amount_untaxed_signed = currency_id._convert(self.amount_untaxed, self.company_id.currency_id,
    #                                                      self.company_id, self.date_invoice or fields.Date.today())
    #     sign = self.type in ['in_refund', 'out_refund'] and -1 or 1
    #     self.amount_total_company_signed = amount_total_company_signed * sign
    #     self.amount_total_signed = self.amount_total * sign
    #     self.amount_untaxed_signed = amount_untaxed_signed * sign
    #
    # @api.one
    # @api.depends(
    #     'state', 'currency_id', 'invoice_line_ids.price_subtotal',
    #     'move_id.line_ids.amount_residual',
    #     'move_id.line_ids.currency_id')
    # def _compute_residual(self):
    #     residual = 0.0
    #     residual_company_signed = 0.0
    #     sign = self.type in ['in_refund', 'out_refund'] and -1 or 1
    #     for line in self._get_aml_for_amount_residual():
    #         residual_company_signed += line.amount_residual
    #         if line.currency_id == self.currency_id:
    #             residual += line.amount_residual_currency if line.currency_id else line.amount_residual
    #         else:
    #             if line.currency_id:
    #                 residual += line.currency_id._convert(line.amount_residual_currency, self.currency_id,
    #                                                       line.company_id, line.date or fields.Date.today())
    #             else:
    #                 residual += line.company_id.currency_id._convert(line.amount_residual, self.currency_id,
    #                                                                  line.company_id, line.date or fields.Date.today())
    #     self.residual_company_signed = abs(residual_company_signed) * sign
    #     self.residual_signed = abs(residual) * sign
    #     self.residual = abs(residual)
    #     digits_rounding_precision = self.currency_id.rounding
    #     if float_is_zero(self.residual, precision_rounding=digits_rounding_precision):
    #         self.reconciled = True
    #     else:
    #         self.reconciled = False