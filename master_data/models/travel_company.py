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
    clearance_list = fields.Many2one('clearance.list',compute='compute_clearance_list')

    @api.one
    @api.depends('labor_id')
    def compute_clearance_list(self):
        list = self.env['clearance.list'].search([])
        for record in list:
            for lab in record.clearance_list:
                if lab.labor_id == self.labor_id:
                    self.clearance_list = record.id
                    break

    @api.multi
    def action_done(self):
        list = self.env['travel.company'].search([('id', '=', self.id), ('state', '=', 'done')])
        if list:
            raise ValidationError(_('Done before '))
        if not self.departure_date:
            raise ValidationError(_('Enter Departure Date'))
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
        self.labor_id.state = 'travelled'
        self.state = "done"
        if self.travel_list_id:
            if all(l.state == 'done' for l in self.travel_list_id.travel_list):
                self.travel_list_id.state = 'done'

    @api.multi
    def action_in_progress(self,travel_company,list_name):
        self.ensure_one()
        list = self.env['travel.company'].search([('id', '=', self.id), ('state', '=', 'in_progress')])
        if list:
            raise ValidationError(_('state already in progress before for labor {}'.format(self.labor_id.name)))
        append_labor = []
        append_labor.append(self.labor_id.id)
        invoice_line = []
        product = self.env['product.recruitment.config'].search([('type', '=', 'travel_company')],limit=1)
        if not product:
            raise ValidationError(_('Please, you must add configuration for Travel'))
        if not product.journal_id:
            raise ValidationError(_('Please, you must select journal in travel from configuration'))
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
            'account_id': accounts.get('expense') and accounts['expense'].id or \
                          accounts['expense'].id,
        }))
        invoice = self.env['account.invoice'].search([('partner_id','=',travel_company.id),
            ('origin', '=', list_name), ('state', '=', 'draft')])
        if invoice:
            invoice.write({'invoice_line_ids': invoice_line})
        else:
            print("=============1")
            # travel_list_ids = self.env['travel.list'].search([('state','=','new')])
            #
            # for line in travel_list_ids:
            #     print(line,"====================line")
            #     print( self.id ,"=====----====",line.travel_list)
            #     if self.id in line.travel_list.ids:
            #         print(line.travel_list,"travel_list",self.id)
            #         travel_company = line.travel_company
            self.env['account.invoice'].create({
                'partner_id': travel_company.id,
                'currency_id': product.currency_id.id,
                'state': 'draft',
                'type': 'in_invoice',
                'partner_type': travel_company.vendor_type,
                'origin': list_name,
                'journal_id': product.journal_id.id,
                'account_id': travel_company.property_account_payable_id.id,
                'invoice_line_ids': invoice_line,

            })
        self.state = 'in_progress'

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
        self.state = 'rejected'

    @api.multi
    def action_view_clearance_list(self):
        return {
            'name': _('View Laborer Clearance List'),
            'type': 'ir.actions.act_window',
            'res_model': 'clearance.list',
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
            'res_id': self.clearance_list.id,
            # 'flags': {'form': {'action_buttons': False}}
        }

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
