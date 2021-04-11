from odoo import fields, models , api,_
from datetime import date,datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError


class InterpolRequest(models.Model):
    _name = 'interpol.request'
    _description = 'Interpol Request'
    _rec_name = 'labor_id'
    _order = 'id desc'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _sql_constraints = [('interpol_uniq', 'unique(interpol_no)', 'Interpol no must be unique!')]

    name = fields.Char(string="Number",readonly=True,default='New')
    labor_id = fields.Many2one('labor.profile',readonly=True)
    labor = fields.Char('Labor Name',readonly=True)
    request_date = fields.Datetime(readonly=True, index=True, default=fields.Datetime.now)
    end_date = fields.Datetime('Delivery Date',readonly=True)
    broker = fields.Many2one('res.partner')
    national_id = fields.Char('National ID',size=14,required=True,readonly=True)
    state = fields.Selection([('new','New'),('assigned','Assigned'),('rejected','rejected'),
                             ('done','Done')],default='new',track_visibility="onchange")

    passport_no = fields.Char(readonly=True)
    interpol_no = fields.Char('Interpol No',readonly=True)
    attachment = fields.Binary(readonly=True)
    filename = fields.Char()
    interpol_start_date = fields.Date('Interpol Start Date',readonly=True)
    interpol_end_date = fields.Date('Interpol End Date',readonly=True)
    note = fields.Text(readonly=True)
    broker_list_id = fields.Many2one('interpol.broker')

    @api.onchange('interpol_start_date')
    def onchange_interpol_date(self):
        if self.interpol_start_date:
            self.interpol_end_date = (self.interpol_start_date + relativedelta(months=6)).strftime('%Y-%m-%d')

    @api.multi
    def interpol_invoice(self):
        self.invoice_date = date.today()
        self.state = 'invoiced'

    @api.multi
    def interpol_request_done(self):
        self.ensure_one()
        if not self.interpol_no :
            raise ValidationError(_('You must enter interpol Number #'))
        elif not self.attachment:
            raise ValidationError(_('you must add attachment'))
        else:
            self.labor_id.interpol_no = self.interpol_no
            self.labor_id.interpol_start_date = self.interpol_start_date
            self.labor_id.interpol_end_date = self.interpol_end_date
            self.state = 'done'
        agency = self.env['specify.agent'].search([('labor_id', '=', self.labor_id.id)])
        if self.labor_id.after_medical_check == 'fit' and agency.state == 'selected':
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
        append_labor = []
        append_labor.append(self.labor_id.id)
        invoice_line = []
        purchase_journal = self.env['account.journal'].search([('type', '=', 'purchase')])[0]
        interpol_type = self.env['product.recruitment.config'].search([('type', '=', 'interpol')])
        if interpol_type:
            product = self.env['product.recruitment.config'].search([('type', '=', 'interpol')])[0]
        elif not interpol_type:
            raise ValidationError('Please go to configuration and add product type interpol')
        accounts = product.product.product_tmpl_id.get_product_accounts()
        invoice_line.append((0, 0, {
            'product_id': product.product.id,
            'labors_id': [(6,0, append_labor)],
            'name': self.labor_id.name,
            'uom_id': product.product.uom_id.id,
            'price_unit': self.broker_list_id.broker.cost,
            'discount': 0.0,
            'quantity': 1,
            'account_id': accounts.get('stock_input') and accounts['stock_input'].id or \
                          accounts['expense'].id,
        }))
        invoice = self.env['account.invoice'].search(
            [('origin', '=', self.broker_list_id.name), ('state', '=', 'draft')])
        if invoice:
            invoice.write({'invoice_line_ids': invoice_line})
        else:
            self.env['account.invoice'].create({
                'partner_id': self.broker_list_id.broker.id,
                'currency_id': product.currency_id.id,
                'state': 'draft',
                'type': 'in_invoice',
                'partner_type':self.broker_list_id.broker.vendor_type,
                'origin': self.broker_list_id.name,
                'journal_id': purchase_journal.id,
                'account_id': self.broker_list_id.broker.property_account_payable_id.id,
                'invoice_line_ids': invoice_line,

            })
        if self.labor_id.occupation == 'house_maid':
            training = self.env['slave.training'].search([('slave_id', '=', self.labor_id.id)])
            if training.state == 'finished' and agency.state in ('available','sent','selected'):
                self.env['labor.clearance'].create({
                    'labor_id': self.labor_id.id,
                    'labor_name': self.labor_id.name,
                    'passport_no': self.passport_no,
                    'gender': self.labor_id.gender,
                    'job_title': self.labor_id.occupation,
                    'contact': self.labor_id.phone,
                    'lc1': self.labor_id.lc1.id,
                    'lc2': self.labor_id.lc2.id,
                    'lc3': self.labor_id.lc3.id,
                    'district': self.labor_id.district.id,
                    'agency': agency.agency.id,
                    'agency_code': agency.name,
                    'destination_city': agency.destination_city.id,
                })
        else:
            if agency.state in ('available','sent','selected'):
                self.env['labor.clearance'].create({
                    'labor_id': self.labor_id.id,
                    'labor_name': self.labor_id.name,
                    'passport_no': self.passport_no,
                    'gender': self.labor_id.gender,
                    'job_title': self.labor_id.occupation,
                    'contact': self.labor_id.phone,
                    'lc1': self.labor_id.lc1.id,
                    'lc2': self.labor_id.lc2.id,
                    'lc3': self.labor_id.lc3.id,
                    'district': self.labor_id.district.id,
                    'agency': agency.agency.id,
                    'agency_code': agency.name,
                    'destination_city': agency.destination_city.id,
                })
        if all(l.state == 'done' for l in self.broker_list_id.interpol_request):
            self.broker_list_id.state = 'done'



    @api.multi
    def action_assign(self):
        self.end_date = datetime.now()
        self.state = 'assigned'

    @api.multi
    def action_reject(self):

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
        purchase_journal = self.env['account.journal'].search([('type', '=', 'purchase')])[0]
        product = self.env['product.recruitment.config'].search([('type', '=', 'labor_reject')])[0]
        accounts = product.product.product_tmpl_id.get_product_accounts()
        invoice_line.append((0, 0, {
            'product_id': product.product.id,
            'labor_id': append_labor,
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
        self.state = 'rejected'

    @api.model
    def create(self, vals):

        vals['name'] = self.env['ir.sequence'].next_by_code('interpol.request')
        labor = self.env['labor.profile'].search([('id', '=', vals['labor_id'])])
        line = []
        line.append((0, 0, {
            'type': 'interpol',
        }))
        labor.labor_process_ids = line
        return super(InterpolRequest, self).create(vals)


class LaborProfile(models.Model):
    _inherit = 'labor.profile'

    def request_passport(self):
        print("================================")
        request_obj = self.env['passport.request']
        request_obj.create({
            'name':self.passport_no,
            'labor_id':self.id,
        })