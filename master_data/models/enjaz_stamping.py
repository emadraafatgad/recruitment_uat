# from extra.master_data.models.interpol_request import InterpolRequest
from odoo import fields, models, api, _
from datetime import date
from dateutil.relativedelta import relativedelta

from odoo.exceptions import ValidationError


class LaborEnjaz(models.Model):
    _name = 'labor.enjaz.stamping'
    _order = 'id desc'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']

    state = fields.Selection(
        [('new', 'New'), ('in_progress', 'InProgress'), ('rejected', 'Rejected'), ('done', 'Done')], default='new',
        track_visibility="onchange")
    name = fields.Char(string="Number", readonly=True, default='New')
    labor_id = fields.Many2one('labor.profile')
    labor_name = fields.Char()
    agency = fields.Many2one('res.partner', domain=[('agency', '=', True)])
    agency_code = fields.Char()
    type = fields.Selection([('enjaz', 'Enjaz'), ('stamping', 'Stamping')], required=True)
    enjaz_no = fields.Char()
    passport_no = fields.Char()
    employer = fields.Char()
    city = fields.Many2one('res.country.state')
    bill = fields.Many2one('account.invoice')
    bill_date = fields.Date(related='bill.date_invoice')
    visa_no = fields.Char()
    visa_date = fields.Date(string="Issue date")
    visa_expiry_date = fields.Date(string="Expiry date")

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
        append_labor = []
        append_labor.append(self.labor_id.id)
        if self.type == 'enjaz':
            if not self.enjaz_partner:
                raise ValidationError(_('Enjaz Partner does not exist'))
            if not self.enjaz_no:
                raise ValidationError(_('Please, enter enjaz#'))

            invoice_line = []
            purchase_journal = self.env['account.journal'].search([('type', '=', 'purchase')])[0]
            product = self.env['product.recruitment.config'].search([('type', '=', 'enjaz')])[0]
            accounts = product.product.product_tmpl_id.get_product_accounts()
            invoice_line.append((0, 0, {
                'product_id': product.product.id,
                'labors_id': [(6, 0, append_labor)],
                'name': self.labor_name,
                'product_uom_id': product.product.uom_id.id,
                'price_unit': product.price,
                'discount': 0.0,
                'quantity': 1,
                'account_id': accounts.get('stock_input') and accounts['stock_input'].id or \
                              accounts['expense'].id,
            }))
            cr = self.env['account.invoice'].create({
                'partner_id': self.enjaz_partner.id,
                'currency_id': product.currency_id.id,
                'state': 'draft',
                'type': 'in_invoice',
                'partner_type': self.enjaz_partner.vendor_type,
                'origin': self.name,
                'journal_id': purchase_journal.id,
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
            invoice_line = []
            purchase_journal = self.env['account.journal'].search([('type', '=', 'purchase')])[0]
            product = self.env['product.recruitment.config'].search([('type', '=', 'embassy')])[0]
            accounts = product.product.product_tmpl_id.get_product_accounts()
            invoice_line.append((0, 0, {
                'product_id': product.product.id,
                'labors_id': [(6, 0, append_labor)],
                'name': self.labor_name,
                'product_uom_id': product.product.uom_id.id,
                'price_unit': product.price,
                'discount': 0.0,
                'quantity': 1,
                'account_id': accounts.get('stock_input') and accounts['stock_input'].id or \
                              accounts['expense'].id,
            }))
            self.env['account.invoice'].create({
                'partner_id': self.embassy.id,
                'currency_id': product.currency_id.id,
                'state': 'draft',
                'type': 'in_invoice',
                'partner_type': self.embassy.vendor_type,
                'origin': self.name,
                'journal_id': purchase_journal.id,
                'account_id': self.embassy.property_account_payable_id.id,
                'invoice_line_ids': invoice_line,

            })
            clearance = self.env['labor.clearance'].search([('labor_id', '=', self.labor_id.id)])

            if clearance.state == 'confirmed':
                self.env['travel.company'].create({
                    'labor_id': self.labor_id.id,
                    'labor_name': self.labor_name,
                    'passport_no': self.labor_id.passport_no,
                    'agency': self.agency.id,
                    'agency_code': self.agency_code,
                    'destination_city': self.city.id,
                    'employer': self.employer,
                    'visa_no': self.visa_no, })

            invoice_line = []
            sale_journal = self.env['account.journal'].search([('type', '=', 'sale')])[0]
            product_agency = self.env['product.recruitment.config'].search([('type', '=', 'agency')])[0]
            accounts = product_agency.product.product_tmpl_id.get_product_accounts()
            invoice_line.append((0, 0, {
                'product_id': product_agency.product.id,
                'labors_id': [(6, 0, append_labor)],
                'name': self.labor_name,
                'product_uom_id': product_agency.product.uom_id.id,
                'price_unit': self.agency.agency_cost,
                'discount': 0.0,
                'quantity': 1,
                'account_id': accounts.get('stock_input') and accounts['stock_input'].id or \
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
