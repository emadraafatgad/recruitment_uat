from odoo import fields, models,api,_
from odoo.exceptions import ValidationError


class MedicalList(models.Model):
    _name = 'medical.list'
    _order = 'id desc'
    _description = 'Medical List'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Number",readonly=True,default='New')
    list_now_len = fields.Integer()
    total_lines = fields.Integer(compute='_compute_value')
    medical_request = fields.Many2many('big.medical',required=True)
    hospital = fields.Many2one('res.partner', domain=[('vendor_type','=','hospital')])
    state = fields.Selection([('new', 'New'), ('invoiced', 'Invoiced'),('done', 'Done')], default='new', track_visibility="onchange")
    examination_date = fields.Date()

    @api.one
    @api.depends('medical_request')
    def _compute_value(self):
        self.total_lines = len(self.medical_request)

    @api.multi
    def action_confirm(self):
        for list in self.medical_request:
            if list.medical_check:
               list.action_done()
            else:
                raise ValidationError(_('You must enter medical check information to all list'))
        self.state = 'done'

    @api.onchange('medical_request')
    def onchange_list(self):
        if not self.state == 'new':
            if self.total_lines > self.list_now_len:
                raise ValidationError(_('You cannot add lines in this state'))
            if self.total_lines < self.list_now_len:
                raise ValidationError(_('You cannot add lines in this state'))

    @api.onchange('medical_request','hospital')
    def domain_list(self):
        line = []
        request = self.env['medical.list'].search([])
        for record in request:
            for rec in record.medical_request:
                line.append(rec.id)
        if self.hospital:
            domain = {'medical_request': [('id', 'not in', line),('state', '=', 'pending'),('hospital', '=', self.hospital.id)]}
            return {'domain': domain}
        else:
            domain = {'medical_request': [('id', '=',False)]}
            return {'domain': domain}

    @api.multi
    def invoice(self):
        if not self.hospital:
            raise ValidationError(_('Enter hospital'))
        if not self.medical_request:
            raise ValidationError(_('Enter lines to invoice'))
        self.state = 'invoiced'
        self.list_now_len = len(self.medical_request)
        invoice_line = []
        product = self.env['product.recruitment.config'].search([('type', '=', 'hospital')])[0]
        if not product.journal_id:
            raise ValidationError(_('Please, you must select journal in big medical from configration'))
        accounts = product.product.product_tmpl_id.get_product_accounts()
        name = ''
        append_labor = []
        for rec in self.medical_request:
            if not rec.check_date:
                raise ValidationError(_('You must enter check date to all list'))
            rec.invoiced = True
            name += rec.labor_id.name + '/Passport#: '+rec.passport_no + '/GCC#: '+rec.gcc_no +', '
            append_labor.append(rec.labor_id.id)
        invoice_line.append((0, 0, {
            'product_id': product.product.id,
            'labors_id': [(6,0, append_labor)],
            'name': name,
            'uom_id': product.product.uom_id.id,
            'price_unit': self.hospital.cost,
            'discount': 0.0,
            'quantity': float(len(self.medical_request)),
            'account_id': accounts.get('stock_input') and accounts['stock_input'].id or \
                          accounts['expense'].id,
        }))

        cr = self.env['account.invoice'].create({
            'partner_id': self.hospital.id,
            'currency_id': product.currency_id.id,
            'state': 'draft',
            'type': 'in_invoice',
            'partner_type': self.hospital.vendor_type,
            'origin': self.name,
            'journal_id': product.journal_id.id,
            'account_id': self.hospital.property_account_payable_id.id,
            'invoice_line_ids': invoice_line,

        })
        cr.action_invoice_open()


    """@api.constrains('hospital','medical_request')
    def hospital_constrains(self):
        for rec in self.medical_request:
            rec.hospital = self.hospital"""

    # @api.multi
    # def unlink(self):
    #     for rec in self:
    #         if rec.state != 'new':
    #             raise ValidationError(_('You cannot delete %s as it is not in new state') % rec.name)
    #     return super(MedicalList, self).unlink()
    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('medical.list')
        return super(MedicalList, self).create(vals)




