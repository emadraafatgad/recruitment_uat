from odoo import models, fields,api, _
from odoo.exceptions import ValidationError

class AccommodationList(models.Model):
    _name = 'accommodation.list'
    _order = 'id desc'
    _description = 'Accommodation List'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Sequence",track_visibility="onchange",default='New')
    start_date = fields.Date(track_visibility="onchange")
    end_date = fields.Date(track_visibility="onchange")
    accommodation_period = fields.Integer(track_visibility="onchange",compute='calculate_accommodation_period',store=True)
    training_center = fields.Many2one('res.partner',domain="[('vendor_type','=','training')]", track_visibility="onchange")
    extra_days = fields.Integer()
    accommodation_list = fields.One2many('labour.accommodation','accommodation_list_id')
    total_lines = fields.Integer(compute='compute_len_lines')
    list_now_len = fields.Integer()
    state = fields.Selection([('new','New'),('confirm','Confirmed'),('invoiced','Invoiced')], default='new', track_visibility="onchange")

    @api.depends('start_date','end_date','extra_days')
    def calculate_accommodation_period(self):
        for accommodation in self:
            if accommodation.start_date and accommodation.end_date:
                period = accommodation.end_date - accommodation.start_date
                print(period.days,"period")
                accommodation.accommodation_period = period.days + accommodation.extra_days + 1
            else:
                accommodation.accommodation_period = accommodation.extra_days

    @api.one
    @api.depends('accommodation_list')
    def compute_len_lines(self):
        self.total_lines = len(self.accommodation_list)

    """@api.onchange('accommodation_list')
    def onchange_list(self):
        if not self.state == 'new':
            if self.total_lines > self.list_now_len:
                raise ValidationError(_('You cannot add lines in this state'))
            if self.total_lines < self.list_now_len:
                raise ValidationError(_('You cannot remove lines in this state'))"""

    @api.multi
    def action_confirm(self):
        self.ensure_one()
        self.list_now_len = len(self.accommodation_list)
        if not self.start_date:
            raise ValidationError(_('You must enter start date'))
        if not self.end_date:
            raise ValidationError(_('You must enter end date'))
        for record in self.accommodation_list:
            record.start_date = self.start_date
            record.end_date = self.end_date
            record.training_center = self.training_center
            record.state = 'confirm'
        self.state = 'confirm'

    @api.multi
    def unlink(self):
        for rec in self:
            if rec.state != 'new':
                raise ValidationError(_('You cannot delete %s as it is not in new state') % rec.name)
        return super(AccommodationList, self).unlink()

    @api.multi
    def create_bill(self):
        self.ensure_one()
        for record in self.accommodation_list:
            record.state = 'invoiced'
        invoice_line = []
        product = self.env['product.recruitment.config'].search([('type', '=', 'accommodation')],limit=1)
        if not product:
            raise ValidationError(_('There is no configration for accommodation you must put configration for accommodation'))
        if not product.journal_id:
            raise ValidationError(_('Please, you must select journal in accomodation from configration'))
        accounts = product.product.product_tmpl_id.get_product_accounts()
        for rec in self.accommodation_list:
            append_labor = []
            append_labor.append(rec.labour_id.id)
            invoice_line.append((0, 0, {
                'product_id': product.product.id,
                'labors_id': [(6, 0, append_labor)],
                'name': rec.labour_id.name,
                'uom_id': product.product.uom_id.id,
                'price_unit': self.training_center.accommodation_cost,
                'discount': 0.0,
                'quantity':  float(self.accommodation_period),
                'account_id': accounts.get('stock_input') and accounts['stock_input'].id or \
                              accounts['expense'].id,
            }))
        cr = self.env['account.invoice'].create({
            'partner_id': self.training_center.id,
            'currency_id': product.currency_id.id,
            'state': 'draft',
            'type': 'in_invoice',
            'partner_type': self.training_center.vendor_type,
            'origin': self.name,
            'journal_id': product.journal_id.id,
            'account_id': self.training_center.property_account_payable_id.id,
            'invoice_line_ids': invoice_line,

        })
        self.state = 'invoiced'

    @api.model
    def create(self, vals):
        sequence = self.env['ir.sequence'].next_by_code('accommodation.list')
        vals['name'] = sequence
        return super(AccommodationList, self).create(vals)


