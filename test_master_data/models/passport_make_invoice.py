from odoo import fields, models , api,_
from datetime import date,datetime

from odoo.exceptions import ValidationError


class PassportInvoice(models.Model):
    _name = 'passport.request.invoice'
    _description = 'Passport Request Invoice'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(string="Number",readonly=True,default='New')
    placing_issue = fields.Many2one('res.partner',string='Internal affairs',domain=[('vendor_type','=','passport_placing_issue')])
    state = fields.Selection([('new', 'new'),('to_invoice', 'To invoice'),('invoiced', 'Invoiced')], default='new',track_visibility='onchange')
    to_invoice_date = fields.Datetime(readonly=True)
    issued_date = fields.Datetime(readonly=True)
    passport_request = fields.Many2many('passport.request', string='Passport Requests')
    list_now_len = fields.Integer()
    total_lines = fields.Integer()
    amount = fields.Float(compute='compute_amount')
    def compute_amount(self):
        self.amount = len(self.passport_request) * self.placing_issue.cost


    @api.multi
    def action_to_invoice(self):
        if self.total_lines < 1:
            raise ValidationError(_('You must enter at least one line'))

        for l in self.passport_request:
            if not l.prn:
                raise ValidationError(_('You must enter prn to all list'))
            l.state='to_invoice'
        self.to_invoice_date = datetime.now()
        self.list_now_len = len(self.passport_request)
        self.state='to_invoice'

    @api.onchange('passport_request')
    def onchange_len_list(self):
        self.total_lines = len(self.passport_request)
        if not self.state == 'new':
            if self.total_lines > self.list_now_len:
                raise ValidationError(_('You cannot add lines in this state'))
            if self.total_lines < self.list_now_len:
                raise ValidationError(_('You cannot remove lines in this state'))



    @api.onchange('passport_request')
    def domain_list(self):
        line = []
        request = self.env['passport.request.invoice'].search([])
        for record in request:
            for rec in record.passport_request:
                line.append(rec.id)
        domain = {'passport_request': [('id', 'not in', line)]}
        return {'domain': domain}

    @api.multi
    def action_invoice(self):
        for l in self.passport_request:
            if not l.invoice_no :
                raise ValidationError(_('You must enter invoice No to all list'))
        self.issued_date = datetime.now()
        desc = ''
        append_labor = []
        for description in self.passport_request:
            desc += description.prn + ','
            append_labor.append(description.labor_id.id)
        invoice_line = []
        purchase_journal = self.env['account.journal'].search([('type', '=', 'purchase')])[0]
        product = self.env['product.recruitment.config'].search([('type', '=', 'passport_placing_issue')])[0]
        accounts = product.product.product_tmpl_id.get_product_accounts()
        invoice_line.append((0, 0, {
            'product_id': product.product.id,
            'labors_id': [(6,0, append_labor)],
            'name': desc,
            'uom_id': product.product.uom_id.id,
            'price_unit': self.placing_issue.cost,
            'discount': 0.0,
            'quantity': float(len(self.passport_request)),
            'account_id': accounts.get('stock_input') and accounts['stock_input'].id or \
                          accounts['expense'].id,
        }))
        cr =self.env['account.invoice'].create({
            'partner_id': self.placing_issue.id,
            'currency_id': product.currency_id.id,
            'type': 'in_invoice',
            'partner_type': self.placing_issue.vendor_type,
            'origin': self.name,
            'journal_id': purchase_journal.id,
            'account_id': self.placing_issue.property_account_payable_id.id,
            'invoice_line_ids': invoice_line,

        })
        cr.action_invoice_open()
        for rec in self.passport_request:
            if rec.labor_id.occupation in ('pro_worker','pro_maid'):
                invoice_line = []
                append_labor = []
                append_labor.append(rec.labor_id.id)
                sale_journal = self.env['account.journal'].search([('type', '=', 'sale')])[0]
                accounts = product.product.product_tmpl_id.get_product_accounts()
                invoice_line.append((0, 0, {
                    'product_id': product.product.id,
                    'labors_id': [(6,0, append_labor)],
                    'name': 'Passport PLacing Issue',
                    'product_uom_id': product.product.uom_id.id,
                    'price_unit': self.placing_issue.cost,
                    'discount': 0.0,
                    'quantity': 1,
                    'account_id': accounts.get('stock_input') and accounts['stock_input'].id or \
                                  accounts['income'].id,
                }))
                self.env['account.invoice'].create({
                    'partner_id': rec.labor_id.partner_id.id,
                    'currency_id': product.currency_id.id,
                    'state': 'draft',
                    'type': 'out_invoice',
                    'origin': self.name,
                    'journal_id': sale_journal.id,
                    'account_id': rec.labor_id.partner_id.property_account_receivable_id.id,
                    'invoice_line_ids': invoice_line,

                })

        return {
            'name': _('Passport List Invoice'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.invoice',
            'type': 'ir.actions.act_window',
            'domain' :[('origin','=',self.name),('type','=','in_invoice')]

        }

    # @api.multi
    # def unlink(self):
    #     for rec in self:
    #         if rec.state != 'new':
    #             raise ValidationError(_('You cannot delete %s as it is not in new state') % rec.name)
    #     return super(PassportInvoice, self).unlink()
    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('passport.request.invoice')
        return super(PassportInvoice, self).create(vals)

class PassportAccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    @api.onchange('number')
    def action_invoice_open(self):
        origin = self.env['passport.request.invoice'].search([('name', '=', self.origin)])
        for org in origin:
            org.state = 'invoiced'
            org.invoice_date = date.today()
        for list in origin.passport_request:
            list.pass_from = self.partner_id.name
            list.state = 'invoiced'
            list.invoice_id = self.id
            list.invoice_date = date.today()
        return super(PassportAccountInvoice, self).action_invoice_open()