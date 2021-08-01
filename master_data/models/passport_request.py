from dateutil.relativedelta import relativedelta

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class PassportNumber(models.Model):
    _name = 'passport.request'
    _rec_name = 'labor_id'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    _sql_constraints = [('prn_uniq', 'unique(prn)', 'PRN must be unique!'),
                        ('invoice_uniq', 'unique(invoice_no)', 'Invoice# must be unique!')
        , ('passport_no_unique', 'unique(passport_no)', 'Passport No must be unique!'),
                        ('laborer_unique', 'unique(labor_id)', 'Created with this Laborer before!')]

    sequence = fields.Char(string="Sequence", readonly=True, default='New')
    name = fields.Char(string="Labor Name", readonly=True)
    national_id = fields.Char(required=True, size=14, string='National ID')
    labor_id = fields.Many2one('labor.profile', required=True)
    labor_id_no_edit = fields.Many2one('labor.profile', required=True)
    broker = fields.Many2one('res.partner', domain=[('vendor_type', '=', 'passport_broker')])
    religion = fields.Selection([('muslim', 'Muslim'), ('christian', 'Christian'), ('jew', 'Jew'), ('other', 'Other')],
                                'Religion')
    request_date = fields.Datetime(readonly=True, index=True, default=fields.Datetime.now)
    invoice_date = fields.Date('Invoice Date')
    invoice_id = fields.Many2one('account.invoice')
    end_date = fields.Datetime('Delivery Date')
    deadline = fields.Date('Deadline')
    state = fields.Selection([('new', 'New'), ('to_invoice', 'To Invoice'), ('invoiced', 'Invoiced'),
                              ('releasing', 'Releasing'), ('rejected', 'Rejected'), ('done', 'Done'),
                              ('blocked', 'Blocked')], default='new', track_visibility="onchange")
    passport_no = fields.Char(track_visibility="onchange")
    pass_start_date = fields.Date(track_visibility="onchange")
    pass_end_date = fields.Date(track_visibility="onchange")
    pass_from = fields.Char(track_visibility="onchange")
    prn = fields.Char('PRN NO')
    invoice_no = fields.Char('Invoice Number')
    note = fields.Text()
    filename = fields.Char()
    attachment = fields.Binary()
    seq = fields.Integer()
    row_num = fields.Char()
    broker_list_id = fields.Many2one('passport.broker')

    @api.multi
    def set_to_invoiced(self):
        self.broker = False
        self.state = 'invoiced'

    @api.multi
    def set_to_draft(self):
        self.state = 'new'

    @api.multi
    def set_to_release(self):
        self.broker = self.broker_list_id.broker
        self.state = 'releasing'

    @api.onchange('state')
    def onchange_state(self):
        labor = self.env['labor.process'].search([('labor', '=', self.labor_id.id), ('type', '=', 'passport')])
        for rec in labor:
            rec.state = self.state

    @api.multi
    def request_passport_approve(self):
        self.state = 'releasing'

    @api.multi
    def request_passport_done(self):
        self.ensure_one()
        list = self.env['passport.request'].search([('id', '=', self.id), ('state', '=', 'done')])
        if list:
            raise ValidationError(_('Done before '))
        if not self.passport_no or not self.pass_start_date or not self.pass_end_date or not self.pass_from:
            raise ValidationError(_('You must enter passport info'))
        else:
            self.labor_id.passport_no = self.passport_no
            self.labor_id.pass_start_date = self.pass_start_date
            self.labor_id.pass_end_date = self.pass_end_date
            self.labor_id.pass_from = self.pass_from
            self.state = 'done'
            self.labor_id.request_interpol()
            self.labor_id.big_medical_request()
            self.labor_id.specify_agency_request()
        append_labor = []
        append_labor.append(self.labor_id.id)
        invoice_line = []
        product = self.env['product.recruitment.config'].search([('type', '=', 'passport')])[0]
        if not product.journal_id:
            raise ValidationError(_('Please, you must select journal in passport broker from configration'))
        accounts = product.product.product_tmpl_id.get_product_accounts()
        invoice_line.append((0, 0, {
            'product_id': product.product.id,
            'labors_id': [(6, 0, append_labor)],
            'name': self.labor_id.name,
            'uom_id': product.product.uom_id.id,
            'price_unit': self.broker_list_id.broker.cost,
            'discount': 0.0,
            'quantity': 1,
            'account_id': accounts.get('expense') and accounts['expense'].id or \
                          accounts['expense'].id,
        }))
        invoice = self.env['account.invoice'].search(
            [('origin', '=', self.broker_list_id.name), ('state', '=', 'draft')])
        if invoice:
            for rec in invoice.invoice_line_ids:
                for labor in rec.labors_id:
                    if labor.id == self.labor_id.id:
                        raise ValidationError(_('Done before'))
            invoice.write({'invoice_line_ids': invoice_line})
        else:
            self.env['account.invoice'].create({
                'partner_id': self.broker_list_id.broker.id,
                'currency_id': product.currency_id.id,
                'state': 'draft',
                'type': 'in_invoice',
                'partner_type': self.broker_list_id.broker.vendor_type,
                'origin': self.broker_list_id.name,
                'journal_id': product.journal_id.id,
                'account_id': self.broker_list_id.broker.property_account_payable_id.id,
                'invoice_line_ids': invoice_line,

            })
        if self.labor_id.occupation in ('pro_worker', 'pro_maid'):
            invoice_line = []
            sale_journal = self.env['account.journal'].search([('type', '=', 'sale')])[0]
            accounts = product.product.product_tmpl_id.get_product_accounts()
            invoice_line.append((0, 0, {
                'product_id': product.product.id,
                'labors_id': [(6, 0, append_labor)],
                'name': 'Passport Broker',
                'product_uom_id': product.product.uom_id.id,
                'price_unit': self.broker_list_id.broker.cost,
                'discount': 0.0,
                'quantity': 1,
                'account_id': accounts.get('expense') and accounts['expense'].id or \
                              accounts['income'].id,
            }))
            self.env['account.invoice'].create({
                'partner_id': self.labor_id.partner_id.id,
                'currency_id': product.currency_id.id,
                'state': 'draft',
                'type': 'out_invoice',
                'origin': self.broker_list_id.name,
                'journal_id': sale_journal.id,
                'account_id': self.labor_id.partner_id.property_account_receivable_id.id,
                'invoice_line_ids': invoice_line,

            })

        if all(l.state == 'done' for l in self.broker_list_id.passport_request):
            self.broker_list_id.state = 'done'

    @api.multi
    def action_view_labor(self):
        return {
            'name': _('View Labourer Profile'),
            'type': 'ir.actions.act_window',
            'res_model': 'labor.profile',
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
            'res_id': self.labor_id.id,
            # 'flags': {'form': {'action_buttons': False}}
        }

    @api.multi
    def action_reject(self):
        self.ensure_one()
        request = self.env['passport.request'].search([('id', '=', self.id), ('state', '=', 'rejected')])
        if request:
            raise ValidationError(_('Done before'))
        labor = self.env['labor.profile'].search([('id', '=', self.labor_id.id)])
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
                type += record.type +'/ Laborer Reject'
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
                'origin': self.sequence,
                'journal_id': agent_conf.journal_id.id,
                'account_id': labor.agent.property_account_payable_id.id,
                'invoice_line_ids': invoice_line,

            })
        self.state = 'rejected'

    @api.onchange('pass_start_date')
    def onchange_pass_date(self):
        if self.pass_start_date:
            self.pass_end_date = (self.pass_start_date + relativedelta(years=10)).strftime('%Y-%m-%d')

    @api.model
    def create(self, vals):
        sequence = self.env['ir.sequence'].next_by_code('passport.release')
        vals['sequence'] = sequence
        labor = self.env['labor.profile'].search([('id', '=', vals['labor_id'])])
        for rec in labor:
            line = []
            line.append((0, 0, {
                'type': 'passport',

            }))
            rec.labor_process_ids = line
        return super(PassportNumber, self).create(vals)

    @api.constrains('labor_id')
    def constrain_labor(self):
        if self.labor_id != self.labor_id_no_edit:
            raise ValidationError(_('You cannot change labor!'))


class LaborProfile(models.Model):
    _inherit = 'labor.profile'

    passport_ids = fields.One2many('passport.request', 'labor_id')
    passport_state = fields.Selection([('new', 'New'), ('to_invoice', 'To Invoice'), ('invoiced', 'Invoiced'),
                                       ('releasing', 'Releasing'), ('rejected', 'Rejected'), ('done', 'Done'),
                                       ('blocked', 'Blocked')], compute="get_passport_state",store=True)

    @api.depends('passport_ids.state')
    def get_passport_state(self):
        for rec in self:
            print("labor.passport state")
            passport = self.env['passport.request'].search([('labor_id', '=', rec.id)], limit=1)
            rec.passport_state = passport.state
