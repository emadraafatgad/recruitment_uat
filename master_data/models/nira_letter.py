from datetime import date

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class NiraLetter(models.Model):
    _name = 'nira.letter.request'
    _order = 'id desc'
    _description = 'Nira Letter Request'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _sql_constraints = [('laborer_unique', 'unique(labourer_id)', 'Created with this Laborer before!')]
    sequence = fields.Char('Sequence', default="New", size=256, readonly=True)
    labourer_id = fields.Many2one('labor.profile', readonly=True, string='Laborer')
    name = fields.Char(string="Name", readonly=True)
    code = fields.Char(string="Code")
    reject_reason = fields.Char()
    birth_date = fields.Date(string="Date Of Birth", readonly=True)
    request_date = fields.Date("Request Date", readonly=True)
    invoice_date = fields.Date("Invoice Date")
    delivery_date = fields.Datetime("Delivery Date")
    start_date = fields.Date('Issued Date')
    end_date = fields.Date("Expired Date")
    state = fields.Selection([('new', 'New'), ('releasing', 'Releasing'), ('done', 'Done'), ('rejected', 'Rejected'),
                              ('blocked', 'Blocked')], default='new', track_visibility="onchange")
    national_id = fields.Char('National ID', size=14, track_visibility="onchange")
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
        product = self.env['product.recruitment.config'].search([('type', '=', 'nira')],limit=1)
        if not product.journal_id:
            raise ValidationError(_('Please, you must select journal in nira from configration'))
        if not self.national_id or not self.start_date:
            raise ValidationError(_('Enter nira info'))
        self.labourer_id.national_id = self.national_id
        self.labourer_id.start_date = self.start_date
        self.labourer_id.end_date = self.end_date
        self.state = 'done'
        invoice_line = []
        append_labor = []
        append_labor.append(self.labourer_id.id)
        accounts = product.product.product_tmpl_id.get_product_accounts()
        invoice_line.append((0, 0, {
            'product_id': product.product.id,
            'labors_id': [(6, 0, append_labor)],
            'name': self.labourer_id.name,
            'uom_id': product.product.uom_id.id,
            'price_unit': product.price,
            'discount': 0.0,
            'quantity': 1,
            'account_id': accounts.get('expense') and accounts['expense'].id or \
                          accounts['expense'].id,
        }))
        invoice = self.env['account.invoice'].search(
            [('origin', '=', self.broker_list_id.name), ('state', '=', 'draft'), ('type', '=', 'in_invoice')])
        if invoice:
            for rec in invoice.invoice_line_ids:
                for labor in rec.labors_id:
                    if labor.id == self.labourer_id.id:
                        raise ValidationError(_('Done before'))
            invoice.write({'invoice_line_ids': invoice_line})
        else:
            self.env['account.invoice'].create({
                'partner_id': self.broker.id,
                'currency_id': product.currency_id.id,
                'state': 'draft',
                'type': 'in_invoice',
                'partner_type': self.broker.vendor_type,
                'origin': self.broker_list_id.name,
                'journal_id': product.journal_id.id,
                'account_id': self.broker.property_account_payable_id.id,
                'invoice_line_ids': invoice_line,

            })
        self.labourer_id.passport_request()

    @api.multi
    def nira_reject(self):
        self.ensure_one()
        request = self.env['nira.letter.request'].search([('id', '=', self.id), ('state', '=', 'rejected')])
        if request:
            raise ValidationError(_('Done before'))
        if not self.reject_reason:
            raise ValidationError(_('Enter any reject reason'))
        self.state = 'rejected'
        labor = self.env['labor.profile'].search([('id', '=', self.labourer_id.id)])
        currency_id = self.env['product.recruitment.config'].search([('type', '=', "agent")]).currency_id
        type = ''
        process_price = 0.0
        price = 0.0
        invoice_line = []
        append_labor = []
        append_labor.append(self.labor_id.id)
        for record in self.labor_id.labor_process_ids:
            price = 0.0
            process_price = 0.0
            type = ''
            if record.type != 'agent_payment' and record.total_cost > 0:
                conf_type = self.env['product.recruitment.config'].search([('type', '=', record.type)])
                if conf_type.type == 'agency':
                    continue
                if conf_type.type == 'clearance':
                    continue
                if conf_type.type == 'travel_company':
                    continue
                if conf_type:
                    proc_currency_id = conf_type.currency_id
                    accounts = conf_type.product.product_tmpl_id.get_product_accounts()
                    process_price = proc_currency_id._convert(record.total_cost, currency_id, self.env.user.company_id,
                                                              fields.Date.today())

                elif record.type == "big_medical":
                    conf_type = self.env['product.recruitment.config'].search([('type', '=', "hospital")])
                    accounts = conf_type.product.product_tmpl_id.get_product_accounts()
                    proc_currency_id = conf_type.currency_id
                    process_price = proc_currency_id._convert(record.total_cost, currency_id, self.env.user.company_id,
                                                              fields.Date.today())

                elif record.type == "stamping":
                    conf_type = self.env['product.recruitment.config'].search([('type', '=', "embassy")])
                    accounts = conf_type.product.product_tmpl_id.get_product_accounts()
                    proc_currency_id = conf_type.currency_id
                    process_price = proc_currency_id._convert(record.total_cost, currency_id, self.env.user.company_id,
                                                              fields.Date.today())
                elif record.type == "agent_commission":
                    conf_type = self.env['product.recruitment.config'].search([('type', '=', "agent")])
                    accounts = conf_type.product.product_tmpl_id.get_product_accounts()
                    proc_currency_id = conf_type.currency_id
                    process_price = proc_currency_id._convert(record.total_cost, currency_id, self.env.user.company_id,
                                                              fields.Date.today())
                type += record.type + '/ Laborer Reject'
                price += process_price
                invoice_line.append((0, 0, {
                    'product_id': conf_type.product.id,
                    'labors_id': [(6, 0, append_labor)],
                    'name': type,
                    'uom_id': conf_type.product.uom_id.id,
                    'price_unit': price,
                    'discount': 0.0,
                    'quantity': 1,
                    'account_id': accounts.get('expense') and accounts['expense'].id or \
                                  accounts['expense'].id,
                }))
        agent_conf = self.env['product.recruitment.config'].search([('type', '=', "agent")])
        if labor.labor_process_ids:
            self.env['account.invoice'].create({
                'partner_id': labor.agent.id,
                'currency_id': currency_id.id,
                'type': 'in_refund',
                'partner_type': labor.agent.vendor_type,
                'origin': self.name,
                'journal_id': agent_conf.journal_id.id,
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


class LaborProfile(models.Model):
    _inherit = 'labor.profile'

    nira_ids = fields.One2many('nira.letter.request', 'labourer_id')
    nira_state = fields.Selection([('new', 'New'), ('releasing', 'Releasing'), ('done', 'Done'), ('rejected', 'Rejected'),
                              ('blocked', 'Blocked')],  compute="get_nira_state",store=True)

    @api.depends('nira_ids.state')
    def get_nira_state(self):
        for rec in self:
            nira = self.env['nira.letter.request'].search([('labourer_id','=',rec.id)],limit=1)
            if nira:
                rec.nira_state = nira.state
