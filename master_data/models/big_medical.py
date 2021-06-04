from datetime import date

from dateutil.relativedelta import relativedelta

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class BigMedical(models.Model):
    _name = 'big.medical'
    _description = 'Big Medical'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _order = 'id desc'
    _sql_constraints = [('laborer_unique', 'unique(labor_id)', 'Created with this Laborer before!')]

    name = fields.Char(string="Number", readonly=True, default='New')
    labor_id = fields.Many2one('labor.profile')

    def _get_gcc_default(self):
        gcc = self.env['res.partner'].search([('vendor_type', '=', 'gcc')])
        if not gcc:
            raise ValidationError(_('Gcc is not exist,you can create partner its type is gcc'))
        return gcc[0].id

    company_id = fields.Many2one('res.company', 'Company', readonly=True,
                                 default=lambda self: self.env.user.company_id)
    gcc = fields.Many2one('res.partner', readonly=True, domain=[('vendor_type', '=', 'gcc')], default=_get_gcc_default)
    labor = fields.Char('Labor Name')
    gcc_no = fields.Char('GCC#')
    state = fields.Selection(
        [('new', 'New'), ('pending', 'On Examination'), ('fit', 'Finished'), ('rejected', 'Rejected'),
         ('unfit', 'Unfit'), ('blocked', 'Blocked')], default='new', track_visibility="onchange")
    national_id = fields.Char(size=14, string='National ID', related='labor_id.national_id', store=True)
    passport_no = fields.Char(related='labor_id.passport_no', store=True)
    hospital = fields.Many2one('res.partner', domain=[('vendor_type', '=', 'hospital')], track_visibility="onchange")
    booking_date = fields.Date(track_visibility='onchange')
    check_date = fields.Date(string="Examination Date", track_visibility='onchange')
    medical_check = fields.Selection([('fit', 'Fit'), ('unfit', 'Unfit'), ('pending', 'Pending')], string='Result',
                                     track_visibility="onchange")
    reason = fields.Char()
    invoiced = fields.Boolean('Hospital Invoiced')
    interpol_done = fields.Boolean()
    recheck_appear = fields.Boolean(compute='compute_recheck_appear')
    confirm_appear = fields.Boolean(compute='compute_confirm_appear')
    deadline = fields.Date(compute='onchange_check_date', store=True, readonly=False, track_visibility='onchange')
    deadline_medical = fields.Date(track_visibility='onchange', string='Deadline')
    date_today = fields.Date(default=date.today())

    @api.depends('state', 'medical_check')
    def compute_recheck_appear(self):
        for rec in self:
            if rec.state == 'unfit' and rec.medical_check == 'unfit':
                rec.recheck_appear = True
            else:
                rec.recheck_appear = False

    @api.depends('state', 'invoiced')
    def compute_confirm_appear(self):
        for rec in self:
            if rec.state == 'pending' and rec.invoiced:
                rec.confirm_appear = True
            else:
                rec.confirm_appear = False

    @api.depends('check_date')
    def onchange_check_date(self):
        for rec in self:
            if rec.check_date:
                rec.deadline = (rec.check_date + relativedelta(days=5)).strftime('%Y-%m-%d')

    @api.multi
    def action_recheck(self):
        self.medical_check = 'pending'
        self.state = 'pending'
        agency = self.env['specify.agent'].search([('labor_id', '=', self.labor_id.id)])
        agency.medical_state = 'pending'

    @api.multi
    def move_gcc(self):
        self.ensure_one()
        inv = self.env['account.invoice'].search([('origin', '=', self.name), ('type', '=', 'in_invoice')])
        if inv:
            raise ValidationError(_('Done before'))
        if not self.gcc:
            raise ValidationError(_('Gcc'))
        if not self.gcc_no:
            raise ValidationError(_('Enter Gcc#'))
        if not self.booking_date:
            raise ValidationError(_('Booking date'))
        if not self.hospital:
            raise ValidationError(_('Hospital'))
        if not self.check_date:
            raise ValidationError(_('Check Date'))
        medical_list_line = []
        list_found = self.env['medical.list'].search([('hospital', '=', self.hospital.id), ('state', '=', 'new')])
        if list_found:
            medical_list_line.append(self.id)
            list_found[0].medical_request = medical_list_line

        else:
            medical_list_line.append(self.id)
            cr = self.env['medical.list'].create({
                'hospital': self.hospital.id,
                'examination_date': self.check_date

            })
            cr.medical_request = medical_list_line
        append_labor = []
        append_labor.append(self.labor_id.id)
        invoice_line = []
        product = self.env['product.recruitment.config'].search([('type', '=', 'gcc')])[0]
        if not product.journal_id:
            raise ValidationError(_('Please, you must select journal in gcc from configration'))
        accounts = product.product.product_tmpl_id.get_product_accounts()
        invoice_line.append((0, 0, {
            'product_id': product.product.id,
            'labors_id': [(6, 0, append_labor)],
            'name': 'gcc',
            'uom_id': product.product.uom_id.id,
            'price_unit': product.price,
            'discount': 0.0,
            'quantity': 1,
            'account_id': accounts.get('stock_input') and accounts['stock_input'].id or \
                          accounts['expense'].id,
        }))

        cr = self.env['account.invoice'].create({
            'partner_id': self.gcc.id,
            'currency_id': product.currency_id.id,
            'state': 'draft',
            'type': 'in_invoice',
            'partner_type': self.gcc.vendor_type,
            'origin': self.name,
            'journal_id': product.journal_id.id,
            'account_id': self.gcc.property_account_payable_id.id,
            'invoice_line_ids': invoice_line,

        })
        cr.action_invoice_open()
        self.gcc_bill_paid(cr)

        self.state = 'pending'

    def gcc_bill_paid(self, invoice_obj):
        payment_obj = self.env["account.payment"]
        configuration = self.env['product.recruitment.config'].search([('type', '=', 'gcc')], limit=1)
        journal_id = configuration.journal_id
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
    def action_done(self):
        self.ensure_one()
        if self.state in ('fit', 'unfit'):
            raise ValidationError(_('Done before'))
        agency = self.env['specify.agent'].search([('labor_id', '=', self.labor_id.id)])
        if self.medical_check != 'fit':
            raise ValidationError(_('Result must be fit'))

        self.labor_id.after_medical_check = self.medical_check
        if self.reason:
            self.labor_id.reason = self.reason
        if self.medical_check == 'fit' and self.labor_id.interpol_no and agency.state == 'selected':
            self.env['labor.enjaz.stamping'].create({
                'labor_id': self.labor_id.id,
                'labor_name': self.labor,
                'type': 'enjaz',
                'agency': agency.agency.id,
                'agency_code': agency.name,
                'passport_no': self.passport_no,
                'employer': agency.employer,
                'city': agency.destination_city.id,
                'visa_no': agency.visa_no,
            })

        if self.medical_check == 'fit':
            self.state = 'fit'
            agency = self.env['specify.agent'].search([('labor_id', '=', self.labor_id.id)])
            agency.medical_state = 'fit'
        elif self.medical_check == 'unfit':
            self.state = 'unfit'
            agency = self.env['specify.agent'].search([('labor_id', '=', self.labor_id.id)])
            agency.medical_state = 'unfit'

    @api.multi
    def action_reject(self):
        self.ensure_one()
        request = self.env['big.medical'].search([('id', '=', self.id), ('state', '=', 'rejected')])
        if request:
            raise ValidationError(_('Done before'))
        if self.medical_check != 'unfit':
            raise ValidationError(_('Result must be Unfit'))
        if not self.reason:
            raise ValidationError(_('Unfit,you must enter reason'))
        self.labor_id.after_medical_check = self.medical_check
        type = ''
        price = 0.0
        for record in self.labor_id.labor_process_ids:
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
        if self.labor_id.labor_process_ids:
            self.env['account.invoice'].create({
                'partner_id': self.labor_id.agent.id,
                'currency_id': product.currency_id.id,
                'type': 'in_refund',
                'partner_type': self.labor_id.agent.vendor_type,
                'origin': self.name,
                'journal_id': purchase_journal.id,
                'account_id': self.labor_id.agent.property_account_payable_id.id,
                'invoice_line_ids': invoice_line,
            })
        self.state = 'rejected'
        agency = self.env['specify.agent'].search([('labor_id', '=', self.labor_id.id)])
        agency.medical_state = 'rejected'

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('big.medical')
        labor = self.env['labor.profile'].search([('id', '=', vals['labor_id'])])
        for rec in labor:
            line = []
            line.append((0, 0, {
                'type': 'big_medical',
            }))
            rec.labor_process_ids = line
        return super(BigMedical, self).create(vals)


class LaborProfile(models.Model):
    _inherit = 'labor.profile'

    big_medical_ids = fields.One2many('big.medical', 'labor_id')
    medical_state = fields.Selection(
        [('new', 'New'), ('pending', 'On Examination'), ('fit', 'Finished'), ('rejected', 'Rejected'),
         ('unfit', 'Unfit'), ('blocked', 'Blocked')],compute="get_labour_medical_status",
        store=True)

    @api.depends('big_medical_ids.state')
    def get_labour_medical_status(self):
        for rec in self:
            print("big medical state")
            medical = self.env['big.medical'].search([('labor_id', '=', rec.id)], limit=1)
            rec.medical_state = medical.state
