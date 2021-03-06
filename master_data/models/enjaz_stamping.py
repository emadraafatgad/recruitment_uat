# from extra.master_data.models.interpol_request import InterpolRequest
from dateutil.relativedelta import relativedelta

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class LaborEnjaz(models.Model):
    _name = 'labor.enjaz.stamping'
    _order = 'id desc'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']

    state = fields.Selection(
        [('new', 'New'), ('in_progress', 'InProgress'), ('rejected', 'Rejected'), ('done', 'Done'),
         ('blocked', 'Blocked')], default='new',
        track_visibility="onchange")
    name = fields.Char(string="Number", track_visibility="onchange", readonly=True, default='New')
    labor_id = fields.Many2one('labor.profile', track_visibility="onchange")
    religion = fields.Selection(
        [('muslim', 'Muslim'), ('christian', 'Christian'), ('jew', 'Jew'), ('other', 'Other')],
        'Religion',related='labor_id.religion',store=True, track_visibility="onchange")
    labor_name = fields.Char()
    agency = fields.Many2one('res.partner', track_visibility="onchange", domain=[('agency', '=', True)])
    agency_code = fields.Char()
    type = fields.Selection([('enjaz', 'Enjaz'), ('stamping', 'Stamping')], track_visibility="onchange", required=True)
    enjaz_no = fields.Char(track_visibility="onchange")
    passport_no = fields.Char(track_visibility="onchange", related='labor_id.passport_no', store=True)
    employer = fields.Char(track_visibility="onchange")
    city = fields.Many2one('res.country.state', track_visibility="onchange")
    bill = fields.Many2one('account.invoice', track_visibility="onchange")
    bill_date = fields.Date(related='bill.date_invoice', track_visibility="onchange")
    visa_no = fields.Char()
    visa_date = fields.Date(string="Issue date", track_visibility="onchange")
    visa_expiry_date = fields.Date(string="Expiry date", track_visibility="onchange")

    def _get_enjaz_default(self):
        enjaz = self.env['res.partner'].search([('vendor_type', '=', 'enjaz')])
        if not enjaz:
            raise ValidationError(_('Enjaz Partner is not exist,you can create partner its type is enjaz'))
        return enjaz[0].id

    def _get_embassy_default(self):
        embassy = self.env['res.partner'].search([('vendor_type', '=', 'embassy')])
        if not embassy:
            raise ValidationError(_('Embassy Partner is not exist,you can create partner its type is embassy'))
        return embassy[0].id

    enjaz_partner = fields.Many2one('res.partner', readonly=True, domain=[('vendor_type', '=', 'enjaz')],
                                    default=_get_enjaz_default)
    embassy = fields.Many2one('res.partner', readonly=True, domain=[('vendor_type', '=', 'embassy')],
                              default=_get_embassy_default)

    @api.onchange('visa_date')
    def onchange_date(self):
        if self.visa_date:
            self.visa_expiry_date = (self.visa_date + relativedelta(days=90)).strftime('%Y-%m-%d')

    @api.multi
    def action_inprogress(self):
        self.state = 'in_progress'

    @api.multi
    def action_done(self):
        self.ensure_one()
        request = self.env['labor.enjaz.stamping'].search([('id', '=', self.id), ('state', '=', 'done')])
        if request:
            raise ValidationError(_('Done before'))
        append_labor = []
        append_labor.append(self.labor_id.id)
        if self.type == 'enjaz':
            if not self.enjaz_partner:
                raise ValidationError(_('Enjaz Partner does not exist'))
            if not self.enjaz_no:
                raise ValidationError(_('Please, enter enjaz#'))

            invoice_line = []
            product = self.env['product.recruitment.config'].search([('type', '=', 'enjaz')],limit=1)
            if not product.journal_id:
                raise ValidationError(_('Please, you must select journal in enjaz from configration'))
            accounts = product.product.product_tmpl_id.get_product_accounts()
            invoice_line.append((0, 0, {
                'product_id': product.product.id,
                'labors_id': [(6, 0, append_labor)],
                'name': self.labor_name,
                'product_uom_id': product.product.uom_id.id,
                'price_unit': product.price,
                'discount': 0.0,
                'quantity': 1,
                'account_id': accounts.get('expense') and accounts['expense'].id or \
                              accounts['expense'].id,
            }))
            cr = self.env['account.invoice'].create({
                'partner_id': self.enjaz_partner.id,
                'currency_id': product.currency_id.id,
                'state': 'draft',
                'type': 'in_invoice',
                'partner_type': self.enjaz_partner.vendor_type,
                'origin': self.name,
                'journal_id': product.journal_id.id,
                'account_id': self.enjaz_partner.property_account_payable_id.id,
                'invoice_line_ids': invoice_line,
            })
            cr.action_invoice_open()
            self.gcc_bill_paid(cr)

            self.bill = cr.id
            self.env['labor.enjaz.stamping'].create({
                'type': 'stamping',
                'labor_id': self.labor_id.id,
                'labor_name': self.labor_name,
                'agency': self.agency.id,
                'agency_code': self.agency_code,
                'visa_no': self.visa_no,
                'passport_no': self.passport_no,
                'enjaz_no': self.enjaz_no,
                'city': self.city.id,
                'employer': self.employer,
            })
        else:
            if not self.visa_date:
                raise ValidationError(_('Please, enter visa date'))
            if not self.visa_expiry_date:
                raise ValidationError(_('Please, enter visa expiry date'))
            clearance = self.env['labor.clearance'].search([('labor_id', '=', self.labor_id.id)])

            if clearance.state == 'confirmed':
                self.env['travel.company'].create({
                    'labor_id': self.labor_id.id,
                    'labor_name': self.labor_name,
                    'passport_no': self.labor_id.passport_no,
                    'agency': self.agency.id,
                    'agency_code': self.agency_code,
                    'destination_city': self.city.id,
                    'country_id': self.agency.country_id.id,
                    'employer': self.employer,
                    'visa_no': self.visa_no, })

            invoice_line = []
            sale_journal = self.env['account.journal'].search([('type', '=', 'sale')])[0]
            product_agency = self.env['product.recruitment.config'].search([('type', '=', 'agency')],limit=1)
            accounts = product_agency.product.product_tmpl_id.get_product_accounts()
            invoice_line.append((0, 0, {
                'product_id': product_agency.product.id,
                'labors_id': [(6, 0, append_labor)],
                'name': self.labor_name,
                'product_uom_id': product_agency.product.uom_id.id,
                'price_unit': self.agency.agency_cost,
                'discount': 0.0,
                'quantity': 1,
                'account_id': accounts.get('expense') and accounts['expense'].id or \
                              accounts['income'].id,
            }))
            cr = self.env['account.invoice'].create({
                'partner_id': self.agency.id,
                'currency_id': product_agency.currency_id.id,
                'state': 'draft',
                'type': 'out_invoice',
                'origin': self.name,
                'journal_id': sale_journal.id,
                'account_id': self.agency.property_account_receivable_id.id,
                'invoice_line_ids': invoice_line,
            })
            cr.action_invoice_open()

        self.state = 'done'

    def gcc_bill_paid(self, invoice_obj):
        payment_obj = self.env["account.payment"]
        configuration = self.env['product.recruitment.config'].search([('type', '=', 'enjaz')], limit=1)
        if configuration.journal_id:
            journal_id = configuration.journal_id
        else:
            raise ValidationError('please add journal Cash or Bank in configuration')
        # invoice_line_obj = self.env["account.invoice.line"]
        inv_ids = []
        curr_payment = {
            'invoice_ids': [(4, invoice_obj.id, None)],
            'communication': invoice_obj.name,
            'payment_method_id': 2,
            'partner_type': 'supplier',
            'partner_id': invoice_obj.partner_id.id,
            'amount': configuration.price,
            'payment_type': 'outbound',
            'journal_id': journal_id.id,
            'payment_date': fields.Date.today(),
        }
        payment = payment_obj.create(curr_payment)
        print("i will paid", payment)
        payment.action_validate_invoice_payment()
        print("i paid here")
        return True

    @api.multi
    def action_reject(self):
        self.ensure_one()
        request = self.env['labor.enjaz.stamping'].search([('id', '=', self.id), ('state', '=', 'rejected')])
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
    def action_release(self):
        self.state = 'in_progress'

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

    @api.model
    def create(self, vals):
        if 'labor_id' in vals:
            labor = self.env['labor.profile'].search([('id', '=', vals['labor_id'])])
            line = []
            if vals['type'] == 'enjaz':
                vals['name'] = self.env['ir.sequence'].next_by_code('labor.enjaz')
                for rec in labor:
                    line.append((0, 0, {
                        'type': 'enjaz',

                    }))
                    rec.labor_process_ids = line

            elif vals['type'] == 'stamping':
                vals['name'] = self.env['ir.sequence'].next_by_code('labor.stamping')
                for rec in labor:
                    line.append((0, 0, {
                        'type': 'stamping',

                    }))
                    rec.labor_process_ids = line
        else:
            raise ValidationError('there is no labour ')

        return super(LaborEnjaz, self).create(vals)


class LaborProfile(models.Model):
    _inherit = 'labor.profile'

    enjaz_stamping_ids = fields.One2many('labor.enjaz.stamping', 'labor_id')
    stamping_state = fields.Selection(
        [('new', 'New'), ('in_progress', 'InProgress'), ('rejected', 'Rejected'), ('done', 'Done'),
         ('blocked', 'Blocked')],
        compute="get_enjaz_state", store=True)

    @api.depends('enjaz_stamping_ids.state')
    def get_enjaz_state(self):
        for rec in self:
            enjaz = self.env['labor.enjaz.stamping'].search([('labor_id', '=', rec.id)], limit=1)
            rec.stamping_state = enjaz.state
