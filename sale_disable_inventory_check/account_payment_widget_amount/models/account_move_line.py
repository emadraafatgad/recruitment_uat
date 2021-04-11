from collections import OrderedDict
import json
import re
import uuid
from functools import partial

from lxml import etree
from dateutil.relativedelta import relativedelta
from werkzeug.urls import url_encode

from odoo import api, exceptions, fields, models, _
from odoo.tools import email_re, email_split, email_escape_char, float_is_zero, float_compare, \
    pycompat, date_utils
from odoo.tools.misc import formatLang

from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning

from odoo.addons import decimal_precision as dp
import logging


class account_invoice(models.Model):
    _inherit = 'account.invoice'

    @api.one
    def _get_outstanding_info_JSON(self):
        self.outstanding_credits_debits_widget = json.dumps(False)
        if self.state == 'open':
            domain = [('account_id', '=', self.account_id.id),
                      ('partner_id', '=', self.env['res.partner']._find_accounting_partner(self.partner_id).id),
                      ('reconciled', '=', False),
                      ('move_id.state', '=', 'posted'),
                      '|',
                      '&', ('amount_residual_currency', '!=', 0.0), ('currency_id', '!=', None),
                      '&', ('amount_residual_currency', '=', 0.0), '&', ('currency_id', '=', None),
                      ('amount_residual', '!=', 0.0)]
            if self.type in ('out_invoice', 'in_refund'):
                domain.extend([('credit', '>', 0), ('debit', '=', 0)])
                type_payment = _('Outstanding credits')
            else:
                domain.extend([('credit', '=', 0), ('debit', '>', 0)])
                type_payment = _('Outstanding debits')
            info = {'title': '', 'outstanding': True, 'content': [], 'invoice_id': self.id}
            lines = self.env['account.move.line'].search(domain)
            account_payment_inv = self.env['account.payment'].search([('invoice_id_for_filtration', '=', self.id)],
                                                                     limit=1)
            currency_id = self.currency_id
            if len(lines) != 0:
                for line in lines:
                    if account_payment_inv:
                        if line.payment_id.id == account_payment_inv.id:
                            if line.currency_id and line.currency_id == self.currency_id:
                                amount_to_show = abs(line.amount_residual_currency)
                            else:
                                currency = line.company_id.currency_id
                                amount_to_show = currency._convert(abs(line.amount_residual), self.currency_id,
                                                                   self.company_id,
                                                                   line.date or fields.Date.today())
                            if float_is_zero(amount_to_show, precision_rounding=self.currency_id.rounding):
                                continue
                            if line.ref:
                                title = '%s : %s' % (line.move_id.name, line.ref)
                            else:
                                title = line.move_id.name
                            info['content'].append({
                                'journal_name': line.ref or line.move_id.name,
                                'title': title,
                                'amount': amount_to_show,
                                'currency': currency_id.symbol,
                                'id': line.id,
                                'position': currency_id.position,
                                'digits': [69, self.currency_id.decimal_places],
                            })
                            info['title'] = type_payment
                            self.outstanding_credits_debits_widget = json.dumps(info)
                            self.has_outstanding = True
                    else:
                        if line.currency_id and line.currency_id == self.currency_id:
                            amount_to_show = abs(line.amount_residual_currency)
                        else:
                            currency = line.company_id.currency_id
                            amount_to_show = currency._convert(abs(line.amount_residual), self.currency_id,
                                                               self.company_id,
                                                               line.date or fields.Date.today())
                        if float_is_zero(amount_to_show, precision_rounding=self.currency_id.rounding):
                            continue
                        if line.ref:
                            title = '%s : %s' % (line.move_id.name, line.ref)
                        else:
                            title = line.move_id.name
                        info['content'].append({
                            'journal_name': line.ref or line.move_id.name,
                            'title': title,
                            'amount': amount_to_show,
                            'currency': currency_id.symbol,
                            'id': line.id,
                            'position': currency_id.position,
                            'digits': [69, self.currency_id.decimal_places],
                        })
                        info['title'] = type_payment
                        self.outstanding_credits_debits_widget = json.dumps(info)
                        self.has_outstanding = True

    discount_lines = fields.One2many(
        comodel_name='discount.line',
        inverse_name='invoice_id',
        string='Discount Lines',
        required=False)

    ks_amount_discount = fields.Monetary(string='Discount', readonly=True, compute='_compute_amount',
                                         store=True, track_visibility='always')

    def _compute_amount(self):
        for rec in self:
            res = super(account_invoice, rec)._compute_amount()
            rec.ks_calculate_discount()
        return res

    @api.multi
    def ks_calculate_discount(self):
        for rec in self:
            discount_sum = 0.0
            for line in rec.discount_lines:
                discount_sum += line.amount
            rec.ks_amount_discount = discount_sum
            rec.amount_total = rec.amount_tax + rec.amount_untaxed - rec.ks_amount_discount

    @api.model
    def invoice_line_move_line_get(self):
        ks_res = super(account_invoice, self).invoice_line_move_line_get()
        if self.ks_amount_discount > 0 and self.ks_amount_discount < self.amount_total:
            for rec in self.discount_lines:
                dict = {
                    'invl_id': self.number,
                    'type': 'src',
                    'name': rec.name,
                    'price_unit': rec.amount,
                    'quantity': 1,
                    'price': -rec.amount,
                    'account_id': rec.account_id.id,
                    'invoice_id': self.id,
                }
                ks_res.append(dict)
        return ks_res


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    @api.model
    def update_amount_reconcile(
            self, temp_amount_residual, temp_amount_residual_currency,
            amount_reconcile, credit_move, debit_move):

        super(AccountMoveLine, self).update_amount_reconcile(
            temp_amount_residual, temp_amount_residual_currency,
            amount_reconcile, credit_move, debit_move)
        # Check if amount is positive
        paid_amt = self.env.context.get('paid_amount', 0.0)
        if not paid_amt:
            return temp_amount_residual, temp_amount_residual_currency, \
                amount_reconcile
        paid_amt = float(paid_amt)
        if paid_amt < 0:
            raise UserError(_(
                "The specified amount has to be strictly positive"))

        # We need those temporary value otherwise the computation might
        # be wrong below

        # Compute paid_amount currency
        if debit_move.amount_residual_currency or \
                credit_move.amount_residual_currency:

            temp_amount_residual_currency = min(
                debit_move.amount_residual_currency,
                -credit_move.amount_residual_currency,
                paid_amt)
        else:
            temp_amount_residual_currency = 0.0

        # If previous value is not 0 we compute paid amount in the company
        # currency taking into account the rate
        if temp_amount_residual_currency:
            paid_amt = debit_move.currency_id._convert(
                paid_amt, debit_move.company_id.currency_id,
                debit_move.company_id,
                credit_move.date or fields.Date.today())
        temp_amount_residual = min(debit_move.amount_residual,
                                   -credit_move.amount_residual,
                                   paid_amt)
        amount_reconcile = temp_amount_residual_currency or \
            temp_amount_residual

        return temp_amount_residual, temp_amount_residual_currency, \
            amount_reconcile

    @api.model
    def _check_remove_debit_move(self, amount_reconcile, debit_move, field):
        res = super(AccountMoveLine, self)._check_remove_debit_move(
            amount_reconcile, debit_move, field)
        if not isinstance(self.env.context.get('paid_amount', False), bool):
            return True
        return res

    @api.model
    def _check_remove_credit_move(self, amount_reconcile, credit_move, field):
        res = super(AccountMoveLine, self)._check_remove_credit_move(
            amount_reconcile, credit_move, field)
        if not isinstance(self.env.context.get('paid_amount', False), bool):
            return True
        return res



class account_payment(models.Model):
    _inherit = 'account.payment'

    invoice_id_for_filtration=fields.Many2one(
        comodel_name='account.invoice',
        string='Invoice',
        required=True)



