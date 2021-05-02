from odoo import fields, models , api,_
from dateutil.relativedelta import relativedelta
from datetime import datetime,date
from odoo.exceptions import UserError, ValidationError


class PassportNumber(models.Model):
    _name = 'passport.request'
    _rec_name = 'labor_id'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _sql_constraints = [('prn_uniq', 'unique(prn)', 'PRN must be unique!'),('invoice_uniq', 'unique(invoice_no)', 'Invoice# must be unique!')
        ,('passport_no_unique', 'unique(passport_no)', 'Passport No must be unique!'),('laborer_unique', 'unique(labor_id)', 'Created with this Laborer before!')]
    _order = 'id desc'

    sequence = fields.Char(string="Sequence", readonly=True,default='New')
    name = fields.Char(string="Labor Name",readonly=True)
    national_id = fields.Char(required=True,size=14,string='National ID')
    labor_id = fields.Many2one('labor.profile',required=True)
    labor_id_no_edit = fields.Many2one('labor.profile',required=True)
    broker = fields.Many2one('res.partner',domain=[('vendor_type','=','passport_broker')])
    religion = fields.Selection([('muslim', 'Muslim'), ('christian', 'Christian'), ('jew', 'Jew'), ('other', 'Other')],'Religion')
    request_date = fields.Datetime(readonly=True, index=True, default=fields.Datetime.now)
    invoice_date = fields.Date('Invoice Date')
    invoice_id = fields.Many2one('account.invoice')
    end_date = fields.Datetime('Delivery Date')
    deadline = fields.Date('Deadline')
    state = fields.Selection([('new','New'),('to_invoice','To Invoice'),('invoiced','Invoiced'),
                              ('releasing','Releasing'),('rejected','Rejected'),('done','Done'),('blocked','Blocked')],default='new',track_visibility="onchange")
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
        labor = self.env['labor.process'].search([('labor', '=', self.labor_id.id),('type', '=', 'passport')])
        labor.state = self.state

    @api.multi
    def request_passport_approve(self):
        self.state = 'releasing'
    @api.multi
    def request_passport_done(self):
        self.ensure_one()
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
                'account_id': accounts.get('stock_input') and accounts['stock_input'].id or \
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
            #'flags': {'form': {'action_buttons': False}}

        }

    @api.multi
    def action_reject(self):
        self.ensure_one()
        labor = self.env['labor.profile'].search([('id', '=', self.labor_id.id)])
        type=''
        price=0.0
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
            'labors_id': [(6,0, append_labor)],
            'name':type,
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
                'origin': self.sequence,
                'journal_id': purchase_journal.id,
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
      labor = self.env['labor.profile'].search([('id', '=',vals['labor_id'])])
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










