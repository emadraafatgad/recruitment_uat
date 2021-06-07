from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class TravelCompany(models.Model):
    _name = 'travel.company'
    _description = 'Travel Company'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _order = 'id desc'
    _sql_constraints = [('laborer_unique', 'unique(labor_id)', 'Created with this Laborer before!')]

    name = fields.Char(string="Number", readonly=True, default='New')
    labor_id = fields.Many2one('labor.profile')
    labor_name = fields.Char()
    invoice = fields.Char()
    passport_no = fields.Char(related='labor_id.passport_no', store=True)
    destination_city = fields.Many2one('res.country.state')
    reservation_no = fields.Char()
    agency_code = fields.Char()
    visa_no = fields.Char()
    employer = fields.Char()
    departure_date = fields.Date()
    country_id = fields.Many2one('res.country', string='Destination Country', required=True)
    confirmation_date = fields.Date()
    flight_details = fields.Text()
    agency = fields.Many2one('res.partner', domain=[('agency', '=', True)])
    travel_company = fields.Many2one('res.partner', domain=[('vendor_type', '=', 'travel_company')])
    travel_list_id = fields.Many2one('travel.list')
    state = fields.Selection([('new', 'new'), ('in_progress', 'InProgress'), ('rejected', 'Rejected'), ('done', 'Done'),
                              ('blocked', 'Blocked')], default='new', track_visibility='onchange')

    @api.multi
    def action_done(self):
        self.ensure_one()
        list = self.env['travel.company'].search([('id', '=', self.id), ('state', '=', 'done')])
        if list:
            raise ValidationError(_('Done before '))
        # if not self.reservation_no:
        #     raise ValidationError(_('Enter Reservation No.'))
        if not self.departure_date:
            raise ValidationError(_('Enter Departure Date'))
        # if not self.confirmation_date:
        #     raise ValidationError(_('Enter Confirmation Date'))
        self.state = 'done'
        self.labor_id.state = 'travelled'
        product = self.env['product.recruitment.config'].search([('type', '=', 'agent')])[0]
        if not product.journal_id:
            raise ValidationError(_('Please, you must select journal in agent from configration'))
        method = self.env['account.payment.method'].search([('payment_type', '=', 'outbound')])[0]
        amount = 0.0
        if self.labor_id.register_with == 'national_id':
            amount = self.labor_id.agent.national_id_cost * 0.5


        elif self.labor_id.register_with == 'passport':
            amount = self.labor_id.agent.passport_cost * 0.5

        elif self.labor_id.register_with == 'nira':
            amount = self.labor_id.agent.nira_cost * 0.5
        l = []
        l.append(self.labor_id.agent_invoice.id)
        payment = self.env['account.payment'].create({
            'partner_id': self.labor_id.agent.id,
            'partner_type': 'supplier',
            'payment_type': 'outbound',
            'journal_id': product.journal_id.id,
            'currency_id': product.currency_id.id,
            'payment_method_id': method.id,
            'communication': self.labor_id.agent_invoice.number,
            'amount': amount,
            'payment': 'last',
            'labor_id': self.labor_id.id,
        })
        payment.invoice_ids = l
        line = []
        line.append((0, 0, {
            'type': 'agent_payment',
            'payment': 'last'

        }))
        self.labor_id.labor_process_ids = line
        append_labor = []
        append_labor.append(self.labor_id.id)
        invoice_line = []
        product = self.env['product.recruitment.config'].search([('type', '=', 'travel_company')])[0]
        if not product.journal_id:
            raise ValidationError(_('Please, you must select journal in travel from configration'))
        accounts = product.product.product_tmpl_id.get_product_accounts()
        name = self.labor_id.name + '/Agency: ' + self.agency.name
        invoice_line.append((0, 0, {
            'product_id': product.product.id,
            'labors_id': [(6, 0, append_labor)],
            'name': name,
            'uom_id': product.product.uom_id.id,
            'price_unit': 0.0,
            'discount': 0.0,
            'quantity': 1,
            'account_id': accounts.get('stock_input') and accounts['stock_input'].id or \
                          accounts['expense'].id,
        }))
        invoice = self.env['account.invoice'].search(
            [('origin', '=', self.travel_list_id.name), ('state', '=', 'draft')])
        if invoice:
            invoice.write({'invoice_line_ids': invoice_line})
        else:
            self.env['account.invoice'].create({
                'partner_id': self.travel_company.id,
                'currency_id': product.currency_id.id,
                'state': 'draft',
                'type': 'in_invoice',
                'partner_type': self.travel_company.vendor_type,
                'origin': self.travel_list_id.name,
                'journal_id': product.journal_id.id,
                'account_id': self.travel_company.property_account_payable_id.id,
                'invoice_line_ids': invoice_line,

            })

        if self.travel_list_id:
            if all(l.state == 'done' for l in self.travel_list_id.travel_list):
                self.travel_list_id.state = 'done'
        self.create_pcr(self.labor_id.id)

    def create_pcr_list(self):
        self.create_pcr(self.labor_id.id)

    def create_pcr(self, labour_id):
        exam = self.env['pcr.exam'].search([('labour_id', '=', labour_id)])
        if not exam:
            valuse = {'labour_id': labour_id, 'state': 'new'}
            self.env['pcr.exam'].create(valuse)
        else:
            raise ValidationError("You Can't Create 2 test")

    @api.multi
    def action_reject(self):
        self.ensure_one()
        request = self.env['travel.company'].search([('id', '=', self.id), ('state', '=', 'rejected')])
        if request:
            raise ValidationError(_('Done before'))
        labor = self.env['labor.profile'].search([('id', '=', self.labor_id.id)])
        type = ''
        price = 0.0
        for record in labor.labor_process_ids:
            if record.type != 'agent_payment':
                type += record.type + ' , '
                price += record.total_cost
        append_labor = []
        append_labor.append(self.labor_id.id)
        invoice_line = []
        product = self.env['product.recruitment.config'].search([('type', '=', 'labor_reject')])[0]
        if not product.journal_id:
            raise ValidationError(_('Please, you must select journal in laborer reject from configration'))
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
                'journal_id': product.journal_id.id,
                'account_id': labor.agent.property_account_payable_id.id,
                'invoice_line_ids': invoice_line,

            })
        self.state = 'rejected'

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('travel.company')
        labor = self.env['labor.profile'].search([('id', '=', vals['labor_id'])])
        line = []
        line.append((0, 0, {
            'type': 'travel_company',

        }))
        labor.labor_process_ids = line
        return super(TravelCompany, self).create(vals)


class LaborProfile(models.Model):
    _inherit = 'labor.profile'
    travel_ids = fields.One2many('travel.company', 'labor_id')
    travel_state = fields.Selection(
        [('new', 'new'), ('in_progress', 'InProgress'), ('rejected', 'Rejected'), ('done', 'Done'),
         ('blocked', 'Blocked')], store=True, compute='get_travel_state')

    @api.depends('travel_ids.state')
    def get_travel_state(self):
        for rec in self:
            travel = self.env['travel.company'].search([('labor_id', '=', rec.id)])
            rec.travel_state = travel.state
