# from extra.master_data.models.interpol_request import InterpolRequest
from odoo import fields, models, api, _

from odoo.exceptions import ValidationError


class LaborClearance(models.Model):
    _name = 'labor.clearance'
    _order = 'id desc'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']

    _sql_constraints = [('laborer_unique', 'unique(labor_id)', 'Created with this Laborer before!')]
    state = fields.Selection(
        [('new', 'New'), ('rejected', 'Rejected'), ('confirmed', 'Confirmed'), ('blocked', 'Blocked')], default='new',
        track_visibility="onchange")
    name = fields.Char(string="Number", readonly=True, default='New')
    labor_id = fields.Many2one('labor.profile', required=True)
    labor_name = fields.Char()
    agency = fields.Many2one('res.partner', domain=[('agency', '=', True)], required=True)
    lc1 = fields.Many2one('labor.village', required=True)
    lc2 = fields.Many2one('labor.parish', required=True)
    lc3 = fields.Many2one('labor.subcounty', required=True)
    district = fields.Many2one('labor.district', required=True)
    job_title = fields.Selection([('house_maid', 'House Maid'), ('pro_maid', 'Pro Maid'), ('pro_worker', 'Pro Worker')],
                                 required=True)
    gender = fields.Selection([('Male', 'Male'), ('Female', 'Female')], required=True)
    contact = fields.Char(required=True)
    passport_no = fields.Char(related='labor_id.passport_no', store=True)
    agency_code = fields.Char(required=True)
    destination_city = fields.Many2one('res.country.state')
    destination_country = fields.Many2one('res.country', related='labor_id.country_id', store=True)
    clearance_list = fields.Many2one('clearance.list')

    @api.multi
    def action_confirm(self):
        self.ensure_one()
        stamping = self.env['labor.enjaz.stamping'].search(
            [('type', '=', 'stamping'), ('labor_id', '=', self.labor_id.id)])
        if stamping.state == 'done':
            self.env['travel.company'].create({
                'labor_id': self.labor_id.id,
                'labor_name': self.labor_name,
                'passport_no': self.labor_id.passport_no,
                'agency': stamping.agency.id,
                'agency_code': self.agency_code,
                'destination_city': stamping.city.id,
                'employer': stamping.employer,
                'visa_no': stamping.visa_no,
                'country_id': stamping.agency.country_id.id,
            })
        self.state = 'confirmed'

    @api.multi
    def action_reject(self):
        self.ensure_one()
        request = self.env['labor.clearance'].search([('id', '=', self.id), ('state', '=', 'rejected')])
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

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('labor.clearance')
        labor = self.env['labor.profile'].search([('id', '=', vals['labor_id'])])
        for rec in labor:
            line = []
            line.append((0, 0, {
                'type': 'clearance',
            }))
            rec.labor_process_ids = line
        return super(LaborClearance, self).create(vals)


class LaborProfile(models.Model):
    _inherit = 'labor.profile'

    clearance_ids = fields.One2many('labor.clearance', 'labor_id')
    clearance_state = fields.Selection(
        [('new', 'New'), ('rejected', 'Rejected'), ('confirmed', 'Confirmed'), ('blocked', 'Blocked')],
        compute='get_clearance_state',
        store=True,
        track_visibility="onchange")

    @api.depends('clearance_ids.state')
    def get_clearance_state(self):
        for rec in self:
            print("labor.clearance state")
            clearance = self.env['labor.clearance'].search([('labor_id', '=', rec.id)], limit=1)
            rec.clearance_state = clearance.state
