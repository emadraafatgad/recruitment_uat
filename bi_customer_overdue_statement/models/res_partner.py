# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.
##############################################################################
from datetime import datetime, date

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _


class Res_Partner(models.Model):
    _inherit = 'res.partner'

    @api.multi
    def _cron_send_overdue_statement(self):
        partners = self.env['res.partner'].search([('customer', '=', True)])
        partners.do_partner_mail()
        return True

    @api.multi
    def _cron_send_customer_statement(self):
        partners = self.env['res.partner'].search([('customer', '=', True)])
        if self.env.user.company_id.period == 'monthly':
            partners.do_process_monthly_statement_filter()
            partners.customer_monthly_send_mail()
        else:
            partners.customer_send_mail()

        return True

    @api.multi
    def _get_amounts_and_date_amount(self):
        user_id = self._uid
        filter_amount_due = 0.0
        filter_amount_overdue = 0.0
        filter_supplier_amount_due = 0.0
        filter_supplier_amount_overdue = 0.0

        company = self.env['res.users'].browse(user_id).company_id
        current_date = datetime.now().date()
        print(current_date)

        for partner in self:
            amount_due = amount_overdue = 0.0
            supplier_amount_due = supplier_amount_overdue = 0.0

            for aml in partner.balance_invoice_ids:
                # if (aml.company_id == company):
                date_maturity = aml.date_due or aml.date
                print(date_maturity)
                amount_due += aml.result
                if (date_maturity <= current_date):
                    amount_overdue += aml.result
            partner.payment_amount_due_amt = amount_due
            partner.payment_amount_overdue_amt = amount_overdue

            for aml in partner.supplier_invoice_ids:
                # if (aml.company_id == company):
                date_maturity = aml.date_due or aml.date
                supplier_amount_due += aml.result
                if (date_maturity <= current_date):
                    supplier_amount_overdue += aml.result
            partner.payment_amount_due_amt_supplier = supplier_amount_due
            partner.payment_amount_overdue_amt_supplier = supplier_amount_overdue

            for aml in partner.customer_statement_line_ids:
                if aml.date_due != False:
                    date_maturity = aml.date_due
                    filter_amount_due += aml.result
                    if (date_maturity <= current_date):
                        filter_amount_overdue += aml.result
            partner.filter_payment_amount_due_amt = filter_amount_due
            partner.filter_payment_amount_overdue_amt = filter_amount_overdue

            for aml in partner.vendor_statement_line_ids:
                date_maturity = aml.date_due
                filter_supplier_amount_due += aml.result
                if (date_maturity <= current_date):
                    filter_supplier_amount_overdue += aml.result
            partner.filter_payment_amount_due_amt_supplier = filter_supplier_amount_due
            partner.filter_payment_amount_overdue_amt_supplier = filter_supplier_amount_overdue

            monthly_amount_due_amt = monthly_amount_overdue_amt = 0.0
            for aml in partner.monthly_statement_line_ids:
                date_maturity = aml.date_due
                monthly_amount_due_amt += aml.result
                if (date_maturity <= current_date):
                    monthly_amount_overdue_amt += aml.result
            partner.monthly_payment_amount_due_amt = monthly_amount_due_amt
            partner.monthly_payment_amount_overdue_amt = monthly_amount_overdue_amt

    supplier_invoice_ids = fields.One2many('account.invoice', 'partner_id', 'Customer move lines', domain=[
        '&', ('type', 'in', ['in_invoice', 'in_refund']), '&', ('state', 'in', ['open', 'paid'])])
    balance_invoice_ids = fields.One2many('account.invoice', 'partner_id', 'Customer move lines', domain=[
        '&', ('type', 'in', ['out_invoice', 'out_refund']), '&', ('state', 'in', ['open', 'paid'])])
    #     customer_state_ids = fields.One2many('account.move.line', 'partner_id', 'Customer move lines', domain=[ '&', ('reconciled', '=', False), '&', ('account_id.internal_type', '=', 'receivable')])
    #     unreconciled_aml_ids = fields.One2many('account.move.line', 'partner_id', 'Move lines')

    payment_amount_due_amt = fields.Float(
        compute='_get_amounts_and_date_amount', string="Balance Due")
    payment_amount_overdue_amt = fields.Float(compute='_get_amounts_and_date_amount',
                                              string="Total Overdue Amount")
    payment_amount_due_amt_supplier = fields.Float(
        compute='_get_amounts_and_date_amount', string="Supplier Balance Due")
    payment_amount_overdue_amt_supplier = fields.Float(compute='_get_amounts_and_date_amount',
                                                       string="Total Supplier Overdue Amount")

    monthly_statement_line_ids = fields.One2many(
        'monthly.statement.line', 'partner_id', 'Monthly Statement Lines')
    customer_statement_line_ids = fields.One2many(
        'bi.statement.line', 'partner_id', 'Customer Statement Lines')
    vendor_statement_line_ids = fields.One2many(
        'bi.vendor.statement.line', 'partner_id', 'Supplier Statement Lines')

    filter_payment_amount_due_amt = fields.Float(
        compute='_get_amounts_and_date_amount', string="Balance Due")
    filter_payment_amount_overdue_amt = fields.Float(compute='_get_amounts_and_date_amount',
                                                     string="Total Overdue Amount")

    monthly_payment_amount_due_amt = fields.Float(
        compute='_get_amounts_and_date_amount', string="Balance Due")
    monthly_payment_amount_overdue_amt = fields.Float(compute='_get_amounts_and_date_amount',
                                                      string="Total Overdue Amount")

    filter_payment_amount_due_amt_supplier = fields.Float(
        compute='_get_amounts_and_date_amount', string="Supplier Balance Due")
    filter_payment_amount_overdue_amt_supplier = fields.Float(compute='_get_amounts_and_date_amount',
                                                              string="Total Supplier Overdue Amount")

    statement_from_date = fields.Date('From Date')
    statement_to_date = fields.Date('To Date')
    today_date = fields.Date(
        default=fields.Date.today(), string="Statement Date")
    vendor_statement_from_date = fields.Date('From Date')
    vendor_statement_to_date = fields.Date('To Date')

    first_thirty_day = fields.Float(string="0-30", compute="compute_days")
    thirty_sixty_days = fields.Float(string="30-60", compute="compute_days")
    sixty_ninty_days = fields.Float(string="60-90", compute="compute_days")
    ninty_plus_days = fields.Float(string="90+", compute="compute_days")
    total = fields.Float(string="Total", compute="compute_total")
    first_thirty_day_filter = fields.Float(
        string="0-30 filter", compute="compute_days_filter")
    thirty_sixty_days_filter = fields.Float(
        string="30-60 filter", compute="compute_days_filter")
    sixty_ninty_days_filter = fields.Float(
        string="60-90 filter", compute="compute_days_filter")
    ninty_plus_days_filter = fields.Float(
        string="90+ filter", compute="compute_days_filter")
    total_filter = fields.Float(string="Total", compute="compute_total_filter")

    initial_bal = fields.Float(string='Initial Balance', readonly=True)
    initial_supp_bal = fields.Float(
        string='Initial Supplier Balance', readonly=True)

    @api.depends('customer_statement_line_ids')
    def compute_days_filter(self):
        today = fields.date.today()
        for partner in self:
            partner.first_thirty_day_filter = 0
            partner.thirty_sixty_days_filter = 0
            partner.sixty_ninty_days_filter = 0
            partner.ninty_plus_days_filter = 0
            from_date = partner.statement_from_date
            to_date = partner.statement_to_date
            domain = [('account_id.internal_type', '=', 'receivable'),
                      ('partner_id', '=', partner.id)]
            if from_date:
                domain.append(('date_maturity', '>=', from_date))
                from_date = from_date
            else:
                from_date = fields.date.today()
                domain.append(('date_maturity', '>=', from_date))
            if to_date:
                domain.append(('date_maturity', '<=', to_date))

            move_lines = self.env['account.move.line'].search(domain)
            for ml in move_lines:
                diff = from_date - ml.date_maturity

                if diff.days >= 0 and diff.days <= 30:
                    partner.first_thirty_day_filter = partner.first_thirty_day_filter + ml.amount_residual

                elif diff.days > 30 and diff.days <= 60:
                    partner.thirty_sixty_days_filter = partner.thirty_sixty_days_filter + ml.amount_residual

                elif diff.days > 60 and diff.days <= 90:
                    partner.sixty_ninty_days_filter = partner.sixty_ninty_days_filter + ml.amount_residual
                else:
                    if diff.days > 90:
                        partner.ninty_plus_days_filter = partner.ninty_plus_days_filter + ml.amount_residual
        return

    def compute_days(self):
        today = fields.date.today()
        for partner in self:
            partner.first_thirty_day = 0
            partner.thirty_sixty_days = 0
            partner.sixty_ninty_days = 0
            partner.ninty_plus_days = 0
            domain = [('account_id.internal_type', '=', 'receivable'),
                      ('partner_id', '=', partner.id)]

            move_lines = self.env['account.move.line'].search(domain)
            for ml in move_lines:
                diff = today - ml.date_maturity
                # datetime.strptime(ml.date_maturity, DEFAULT_SERVER_DATE_FORMAT)
                if diff.days >= 0 and diff.days <= 30:
                    partner.first_thirty_day = partner.first_thirty_day + ml.amount_residual

                elif diff.days > 30 and diff.days <= 60:
                    partner.thirty_sixty_days = partner.thirty_sixty_days + ml.amount_residual

                elif diff.days > 60 and diff.days <= 90:
                    partner.sixty_ninty_days = partner.sixty_ninty_days + ml.amount_residual
                else:
                    if diff.days > 90:
                        partner.ninty_plus_days = partner.ninty_plus_days + ml.amount_residual
        return

    @api.depends('ninty_plus_days', 'sixty_ninty_days', 'thirty_sixty_days', 'first_thirty_day')
    def compute_total(self):
        for partner in self:
            partner.total = 0.0
            partner.total = partner.ninty_plus_days + partner.sixty_ninty_days + \
                            partner.thirty_sixty_days + partner.first_thirty_day
        return

    @api.depends('ninty_plus_days_filter', 'sixty_ninty_days_filter', 'thirty_sixty_days_filter',
                 'first_thirty_day_filter')
    def compute_total_filter(self):
        for partner in self:
            partner.total_filter = 0.0
            partner.total_filter = partner.ninty_plus_days_filter + partner.sixty_ninty_days_filter + \
                                   partner.thirty_sixty_days_filter + partner.first_thirty_day_filter
        return

    @api.multi
    def do_partner_mail(self):
        unknown_mails = 0
        for partner in self:
            partners_to_email = [
                child for child in partner.child_ids if child.type == 'invoice' and child.email]
            if not partners_to_email and partner.email:
                partners_to_email = [partner]
            if partners_to_email and partner.payment_amount_overdue_amt != 0:
                for partner_to_email in partners_to_email:
                    mail_template_id = self.env['ir.model.data'].xmlid_to_object(
                        'bi_customer_overdue_statement.email_template_customer_statement')
                    mail_template_id.send_mail(partner_to_email.id)
                if partner not in partners_to_email:
                    msg = _('Overdue email sent to %s' % ', '.join(
                        ['%s <%s>' % (partner.name, partner.email) for partner in partners_to_email]))
                    partner.message_post(body=msg)
        return unknown_mails

    @api.multi
    def customer_monthly_send_mail(self):
        unknown_mails = 0
        for partner in self:
            partners_to_email = [
                child for child in partner.child_ids if child.type == 'invoice' and child.email]
            if not partners_to_email and partner.email:
                partners_to_email = [partner]
            if partners_to_email:
                for partner_to_email in partners_to_email:
                    mail_template_id = self.env['ir.model.data'].xmlid_to_object(
                        'bi_customer_overdue_statement.email_template_customer_monthly_statement')
                    mail_template_id.send_mail(partner_to_email.id)
                if partner not in partner_to_email:
                    msg = _('Customer Monthly Statement email sent to %s' % ', '.join(
                        ['%s <%s>' % (partner.name, partner.email) for partner in partners_to_email]))
                    partner.message_post(body=msg)
        return unknown_mails

    @api.multi
    def customer_send_mail(self):
        unknown_mails = 0
        for partner in self:
            partners_to_email = [
                child for child in partner.child_ids if child.type == 'invoice' and child.email]
            if not partners_to_email and partner.email:
                partners_to_email = [partner]
            if partners_to_email:
                for partner_to_email in partners_to_email:
                    mail_template_id = self.env['ir.model.data'].xmlid_to_object(
                        'bi_customer_overdue_statement.email_template_customer_statement')
                    mail_template_id.send_mail(partner_to_email.id)
                if partner not in partner_to_email:
                    msg = _('Customer Statement email sent to %s' % ', '.join(
                        ['%s <%s>' % (partner.name, partner.email) for partner in partners_to_email]))
                    partner.message_post(body=msg)
        return unknown_mails

    @api.multi
    def do_process_statement_filter(self):
        account_invoice_obj = self.env['account.invoice']
        statement_line_obj = self.env['bi.statement.line']
        account_payment_obj = self.env['account.payment']
        inv_list = []
        for record in self:
            from_date = record.statement_from_date
            to_date = record.statement_to_date

            if from_date:
                final_initial_bal = 0.0

                in_bal = account_invoice_obj.search([('partner_id', '=', record.id),
                                                     ('type', 'in', ['out_invoice', 'out_refund']),
                                                     ('state', 'in', ['open']), ('date_due', '<', from_date)])

                for inv in in_bal:
                    final_initial_bal += inv.residual

                in_pay_bal = account_payment_obj.search([('partner_id', '=', record.id),
                                                         ('state', 'in', [
                                                             'posted', 'reconciled']), ('payment_date', '<', from_date),
                                                         ('partner_type', '=', 'customer')])

                for pay in in_pay_bal:
                    if not pay.invoice_ids:
                        final_initial_bal -= pay.amount

                if final_initial_bal:
                    record.write({'initial_bal': final_initial_bal})

            domain_payment = [('partner_type', '=', 'customer'), ('state', 'in', [
                'posted', 'reconciled']), ('partner_id', '=', record.id)]
            domain = [('type', 'in', ['out_invoice', 'out_refund']), ('state', 'in', [
                'open', 'paid']), ('partner_id', '=', record.id)]
            if from_date:
                domain.append(('date_invoice', '>=', from_date))
                domain_payment.append(('payment_date', '>=', from_date))
            if to_date:
                domain.append(('date_invoice', '<=', to_date))
                domain_payment.append(('payment_date', '<=', to_date))

            lines_to_be_delete = statement_line_obj.search(
                [('partner_id', '=', record.id)])
            lines_to_be_delete.unlink()

            invoices = account_invoice_obj.search(domain)
            payments = account_payment_obj.search(domain_payment)
            if invoices:
                for invoice in invoices.sorted(key=lambda r: r.number):
                    employer = self.env['specify.agent'].search([('labor_id', '=', invoice.laborer.id)],limit=1)
                    vals = {
                        'partner_id': invoice.partner_id.id or False,
                        'state': invoice.state or False,
                        'date_invoice': invoice.date_invoice,
                        'date_due': invoice.date_due,
                        'number': invoice.number or '',
                        'origin': invoice.origin or '',
                        'labour_id': invoice.laborer.id,
                        'employer': employer.employer,
                        'note': invoice.name or '',
                        'legacy_number': invoice.legacy_number or '',
                        'result': invoice.result or 0.0,
                        'name': invoice.name or '',
                        'amount_total': invoice.amount_total or 0.0,
                        'credit_amount': invoice.credit_amount or 0.0,
                        'invoice_id': invoice.id,
                    }
                    test = statement_line_obj.create(vals)
            if payments:
                for payment in payments.sorted(key=lambda r: r.name):
                    credit_amount = 0.0
                    debit_amount = 0.0
                    if not payment.invoice_ids:
                        for move in payment.move_line_ids:
                            if move.account_id.internal_type == 'receivable':
                                if not move.full_reconcile_id:
                                    debit_amount = move.debit
                                    credit_amount = move.credit
                    else:
                        for move in payment.move_line_ids:
                            if move.account_id.internal_type == 'receivable':
                                if move.reconciled:
                                    pass
                                else:
                                    for matched_id in move.matched_debit_ids:
                                        debit_amount = matched_id.amount
                                        credit_amount = move.credit
                    if debit_amount != 0.0 or credit_amount != 0.0:
                        vals = {
                            'partner_id': payment.partner_id.id or False,
                            'date_invoice': payment.payment_date,
                            'date_due': payment.payment_date,
                            'number': payment.name or '',
                            'result': debit_amount - credit_amount or 0.0,
                            'name': payment.name or '',
                            'amount_total': debit_amount or 0.0,
                            'credit_amount': credit_amount or 0.0,
                            'payment_id': payment.id,
                        }
                        statement_line_obj.create(vals)

    @api.multi
    def do_process_monthly_statement_filter(self):
        account_invoice_obj = self.env['account.invoice']
        statement_line_obj = self.env['monthly.statement.line']
        for record in self:

            today = date.today()
            d = today - relativedelta(months=1)

            start_date = date(d.year, d.month, 1)
            end_date = date(today.year, today.month, 1) - relativedelta(days=1)

            from_date = str(start_date)
            to_date = str(end_date)

            domain = [('type', 'in', ['out_invoice', 'out_refund']), ('state', 'in', [
                'open', 'paid']), ('partner_id', '=', record.id)]
            if from_date:
                domain.append(('date_invoice', '>=', from_date))
            if to_date:
                domain.append(('date_invoice', '<=', to_date))

            lines_to_be_delete = statement_line_obj.search(
                [('partner_id', '=', record.id)])
            lines_to_be_delete.unlink()

            invoices = account_invoice_obj.search(domain)

            for invoice in invoices.sorted(key=lambda r: r.number):
                vals = {
                    'partner_id': invoice.partner_id.id or False,
                    'state': invoice.state or False,
                    'date_invoice': invoice.date_invoice,
                    'date_due': invoice.date_due,
                    'number': invoice.number or '',
                    'result': invoice.result or 0.0,
                    'name': invoice.name or '',
                    'amount_total': invoice.amount_total or 0.0,
                    'credit_amount': invoice.credit_amount or 0.0,
                    'invoice_id': invoice.id,
                }
                statement_line_obj.create(vals)

    @api.multi
    def do_process_vendor_statement_filter(self):
        account_invoice_obj = self.env['account.invoice']
        vendor_statement_line_obj = self.env['bi.vendor.statement.line']
        account_payment_obj = self.env['account.payment']
        for record in self:
            from_date = record.vendor_statement_from_date
            to_date = record.vendor_statement_to_date

            if from_date:

                final_initial_bal = 0.0

                in_bal = account_invoice_obj.search([('partner_id', '=', record.id),
                                                     ('type', 'in', ['in_invoice', 'in_refund']),
                                                     ('state', 'in', ['open']), ('date_due', '<', from_date)])

                for inv in in_bal:
                    final_initial_bal += inv.residual

                in_pay_bal = account_payment_obj.search([('partner_id', '=', record.id),
                                                         ('state', 'in', [
                                                             'posted', 'reconciled']), ('payment_date', '<', from_date),
                                                         ('partner_type', '=', 'supplier')])

                for pay in in_pay_bal:
                    if not pay.invoice_ids:
                        final_initial_bal -= pay.amount

                if final_initial_bal:
                    record.write({'initial_supp_bal': final_initial_bal})

            domain_payment = [('partner_type', '=', 'supplier'), ('state', 'in', [
                'posted', 'reconciled']), ('partner_id', '=', record.id)]
            domain = [('type', 'in', ['in_invoice', 'in_refund']), ('state', 'in', [
                'open', 'paid']), ('partner_id', '=', record.id)]
            if from_date:
                domain.append(('date_invoice', '>=', from_date))
                domain_payment.append(('payment_date', '>=', from_date))
            if to_date:
                domain.append(('date_invoice', '<=', to_date))
                domain_payment.append(('payment_date', '<=', to_date))

            lines_to_be_delete = vendor_statement_line_obj.search(
                [('partner_id', '=', record.id)])
            lines_to_be_delete.unlink()

            invoices = account_invoice_obj.search(domain)
            payments = account_payment_obj.search(domain_payment)
            if invoices:
                for invoice in invoices.sorted(key=lambda r: r.number):
                    vals = {
                        'partner_id': invoice.partner_id.id or False,
                        'state': invoice.state or False,
                        'date_invoice': invoice.date_invoice,
                        'date_due': invoice.date_due,
                        'number': invoice.number or '',
                        'result': invoice.result or 0.0,
                        'name': invoice.name or '',
                        'amount_total': invoice.amount_total or 0.0,
                        'credit_amount': invoice.credit_amount or 0.0,
                        'invoice_id': invoice.id,
                    }
                    vendor_statement_line_obj.create(vals)
            if payments:
                for payment in payments.sorted(key=lambda r: r.name):
                    credit_amount = 0.0
                    debit_amount = 0.0
                    if not payment.invoice_ids:
                        for move in payment.move_line_ids:
                            if move.account_id.internal_type == 'payable':
                                if not move.full_reconcile_id:
                                    debit_amount = move.debit
                                    credit_amount = move.credit
                    else:
                        for move in payment.move_line_ids:
                            if move.account_id.internal_type == 'payable':
                                if move.reconciled:
                                    pass
                                else:
                                    for matched_id in move.matched_credit_ids:
                                        debit_amount = move.debit
                                        credit_amount = matched_id.amount
                    if debit_amount != 0.0 or credit_amount != 0.0:
                        vals = {
                            'partner_id': payment.partner_id.id or False,
                            # 'state':payment.state or False,
                            'date_invoice': payment.payment_date,
                            'date_due': payment.payment_date,
                            'number': payment.name or '',
                            'result': debit_amount - credit_amount or 0.0,
                            'name': payment.name or '',
                            'amount_total': debit_amount or 0.0,
                            'credit_amount': credit_amount or 0.0,
                            'payment_id': payment.id,
                        }
                        vendor_statement_line_obj.create(vals)

    @api.multi
    def do_send_statement_filter(self):
        unknown_mails = 0
        for partner in self:
            partners_to_email = [
                child for child in partner.child_ids if child.type == 'invoice' and child.email]
            if not partners_to_email and partner.email:
                partners_to_email = [partner]
            if partners_to_email:
                for partner_to_email in partners_to_email:
                    mail_template_id = self.env['ir.model.data'].xmlid_to_object(
                        'bi_customer_overdue_statement.email_template_customer_statement_filter')
                    mail_template_id.send_mail(partner_to_email.id)
                if partner not in partner_to_email:
                    msg = _('Customer Filter Statement email sent to %s' % ', '.join(
                        ['%s <%s>' % (partner.name, partner.email) for partner in partners_to_email]))
                    partner.message_post(body=msg)
        return unknown_mails

    @api.multi
    def do_button_print(self):
        return self.env.ref('account.action_report_print_overdue').report_action(self)

    @api.multi
    def do_button_print_statement(self):
        return self.env.ref('bi_customer_overdue_statement.report_customert_print').report_action(self)

    @api.multi
    def do_button_print_vendor_statement(self):
        return self.env.ref('bi_customer_overdue_statement.report_supplier_print').report_action(self)

    @api.multi
    def do_print_statement_filter(self):
        return self.env.ref('bi_customer_overdue_statement.report_customer_statement_filter_print').report_action(self)

    @api.multi
    def do_print_vendor_statement_filter(self):
        return self.env.ref('bi_customer_overdue_statement.report_supplier_filter_print').report_action(self)
