from odoo import fields, models , api,_
from datetime import date

from odoo.exceptions import ValidationError


class NiraLetter(models.Model):
    _name = 'nira.letter.request'
    _order = 'id desc'
    _description = 'Nira Letter Request'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']

    sequence = fields.Char('Sequence',default="New",size=256,readonly=True)
    labourer_id = fields.Many2one('labor.profile',readonly=True)
    name = fields.Char(string="Name",readonly=True)
    code = fields.Char(string="Code")
    reject_reason = fields.Char()
    birth_date = fields.Date(string="Date Of Birth",readonly=True)
    request_date = fields.Date("Request Date",readonly=True)
    invoice_date = fields.Date("Invoice Date")
    delivery_date = fields.Datetime("Delivery Date")
    start_date = fields.Date('Issued Date')
    end_date = fields.Date("Expired Date")
    state = fields.Selection([('new', 'New'), ('releasing', 'Releasing'),('done', 'Done'),('rejected', 'Rejected')], default='new',track_visibility="onchange")
    national_id = fields.Char('National ID',size=14)
    broker_list_id = fields.Many2one('nira.broker')
    broker = fields.Many2one('res.partner')

    @api.onchange('national_id')
    def onchange_national_id(self):
        if self.national_id:
            if len(self.national_id) < 14:
                message = _(('ID must be 14!'))
                mess = {
                    'title': _('Warning'),
                    'message': message
                }
                return {'warning': mess}


    @api.multi
    def nira_request_approve(self):
        self.invoice_date = date.today()
        return self.write({'state': 'invoiced'})

    @api.multi
    def nira_request_done(self):
        self.ensure_one()
        product = self.env['product.recruitment.config'].search([('type', '=', 'nira')])[0]
        if not self.national_id or not self.start_date:
            raise ValidationError(_('Enter nira info'))
        self.labourer_id.national_id = self.national_id
        self.labourer_id.start_date = self.start_date
        self.labourer_id.end_date = self.end_date
        self.state = 'done'
        invoice_line = []
        append_labor = []
        append_labor.append(self.labourer_id.id)

        purchase_journal = self.env['account.journal'].search([('type', '=', 'purchase')])[0]
        accounts = product.product.product_tmpl_id.get_product_accounts()
        invoice_line.append((0, 0, {
            'product_id': product.product.id,
            'labors_id': [(6, 0, append_labor)],
            'name': self.labourer_id.name,
            'uom_id': product.product.uom_id.id,
            'price_unit': product.price,
            'discount': 0.0,
            'quantity': 1,
            'account_id': accounts.get('stock_input') and accounts['stock_input'].id or \
                          accounts['expense'].id,
        }))
        invoice = self.env['account.invoice'].search(
            [('origin', '=', self.broker_list_id.name), ('state', '=', 'draft'), ('type', '=', 'in_invoice')])
        if invoice:
            invoice.write({'invoice_line_ids': invoice_line})
        else:
            self.env['account.invoice'].create({
                'partner_id': self.broker.id,
                'currency_id': product.currency_id.id,
                'state': 'draft',
                'type': 'in_invoice',
                'partner_type': self.broker.vendor_type,
                'origin': self.broker_list_id.name,
                'journal_id': purchase_journal.id,
                'account_id': self.broker.property_account_payable_id.id,
                'invoice_line_ids': invoice_line,

            })
        self.labourer_id.passport_request()


    @api.multi
    def nira_reject(self):
        self.ensure_one()
        if not self.reject_reason:
            raise ValidationError(_('Enter any reject reason'))
        self.state = 'rejected'
        type = ''
        price = 0.0
        labor = self.env['labor.profile'].search([('id', '=', self.labourer_id.id)])
        for record in labor.labor_process_ids:
            if record.type != 'agent_payment':
                type += record.type + ' , '
                price += record.total_cost
        append_labor = []
        append_labor.append(self.labor_id.id)
        invoice_line = []
        purchase_journal = self.env['account.journal'].search([('type', '=', 'purchase')])[0]
        product = self.env['product.recruitment.config'].search([('type', '=', 'labor_reject')])[0]
        accounts = product.product.product_tmpl_id.get_product_accounts()
        invoice_line.append((0, 0, {
            'product_id': product.product.id,
            'labors_id': [(6, 0, append_labor)],
            'name': type,
            'uom_id': product.product.uom_id.id,
            'price_unit': price,
            'discount': 0.0,
            'quantity': 1,
            'account_id': accounts.get('stock_input') and accounts['stock_input'].id or \
                          accounts['expense'].id,
        }))
        if labor.labor_process_ids:
            self.env['account.invoice'].create({
                'partner_id': labor.agent.id,
                'currency_id': product.currency_id.id,
                'type': 'in_refund',
                'partner_type': labor.agent.vendor_type,
                'origin': self.name,
                'journal_id': purchase_journal.id,
                'account_id': labor.agent.property_account_payable_id.id,
                'invoice_line_ids': invoice_line,

            })




    @api.model
    def create(self, vals):
        vals['sequence'] = self.env['ir.sequence'].next_by_code('nira.letter.request')
        vals['request_date'] = date.today()
        labor = self.env['labor.profile'].search([('id', '=', vals['labourer_id'])])
        line = []
        line.append((0, 0, {
            'type': 'nira',

        }))
        labor.labor_process_ids = line
        return super(NiraLetter, self).create(vals)



