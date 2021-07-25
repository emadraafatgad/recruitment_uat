from odoo import fields, models, api, _
from datetime import date


class PassportInvoice(models.Model):
    _name = 'passport.request.invoice'
    _order = 'id desc'
    _description = 'Passport Request Invoice'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Number", track_visibility="onchange", readonly=True, default='New')
    placing_issue = fields.Many2one('res.partner', string='Internal affairs', track_visibility="onchange",
                                    domain=[('supplier', '=', True)])
    state = fields.Selection([('new', 'new'), ('to_invoice', 'to Invoice'), ('invoiced', 'Invoiced')], default='new',
                             track_visibility='onchange')
    issued_date = fields.Date(default=date.today(), track_visibility="onchange", readonly=True)
    invoice_date = fields.Date(readonly=True, track_visibility="onchange")
    passport_request = fields.Many2many('passport.request', track_visibility="onchange", string='Passport Requests')

    def _get_product_default(self):
        product = self.env['product.recruitment.config'].search([('type', '=', 'passport')])
        self.product = product.product

    product = fields.Many2one('product.product', compute=_get_product_default)

    @api.multi
    def action_invoice(self):
        invoice_line = []
        purchase_journal = self.env['account.journal'].search([('type', '=', 'purchase')])[0]
        accounts = self.product.product_tmpl_id.get_product_accounts()
        invoice_line.append((0, 0, {
            'product_id': self.product.id,
            'name': self.product.name,
            'product_uom_id': self.product.uom_id.id,
            'price_unit': self.product.list_price,
            'discount': 0.0,
            'quantity': float(len(self.passport_request)),
            'account_id': accounts.get('expense') and accounts['expense'].id or \
                          accounts['expense'].id,
        }))
        self.env['account.invoice'].create({
            'partner_id': self.placing_issue.id,
            'state': 'draft',
            'type': 'in_invoice',
            'origin': self.name,
            'journal_id': purchase_journal.id,
            'account_id': self.placing_issue.property_account_payable_id.id,
            'invoice_line_ids': invoice_line,

        })

        self.state = 'to_invoice'
        return {
            'name': _('List Invoice'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.invoice',
            'type': 'ir.actions.act_window',
            'domain': [('origin', '=', self.name)]
        }

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('passport.request.invoice')
        return super(PassportInvoice, self).create(vals)


class PassportAccountInvoice(models.Model):
    _inherit = 'account.invoice'

    def action_invoice_open(self):
        origin = self.env['passport.request.invoice'].search([('name', '=', self.origin)])
        origin.state = 'invoiced'
        origin.invoice_date = date.today()
        for list in origin.passport_request:
            list.invoice_no = self.number
            list.invoice_date = date.today()
            list.pass_from = self.partner_id.name
            list.state = 'invoiced'
        return super(PassportAccountInvoice, self).action_invoice_open()
