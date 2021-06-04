from odoo import fields, models, api, _
from datetime import date

from odoo.exceptions import ValidationError


class StampingList(models.Model):
    _name = 'stamping.list'
    _description = 'Stamping List'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(string="Number", readonly=True, default='New')
    state = fields.Selection([('new', 'New'), ('in_progress', 'InProgress'), ('done', 'Done')], default='new',
                             track_visibility="onchange")
    stamping_list = fields.Many2many('labor.enjaz.stamping')
    list_total_count = fields.Integer(compute='_compute_value')
    assign_date = fields.Date()
    list_now_len = fields.Integer()
    labour_ids = fields.Many2many('labor.profile')
    def _get_embassy_default(self):
        embassy = self.env['res.partner'].search([('vendor_type', '=', 'embassy')])
        if not embassy:
            raise ValidationError(_('Embassy Partner is not exist,you can create partner its type is embassy'))
        return embassy[0].id

    embassy = fields.Many2one('res.partner', readonly=True, domain=[('vendor_type', '=', 'embassy')],
                              default=_get_embassy_default)

    @api.one
    @api.depends('stamping_list')
    def _compute_value(self):
        self.list_total_count = len(self.stamping_list)

    @api.multi
    def action_inprogress(self):
        if not self.embassy:
            raise ValidationError(_('Embassy Partner not found!'))
        for rec in self.stamping_list:
            rec.state = 'in_progress'
        self.list_now_len = len(self.stamping_list)
        self.state = 'in_progress'

    @api.onchange('stamping_list')
    def onchange_nira_list(self):
        if not self.state == 'new':
            # if self.list_total_count > self.list_now_len:
            #     raise ValidationError(_('You cannot add lines in this state'))
            if self.list_total_count < self.list_now_len:
                raise ValidationError(_('You cannot remove lines in this state'))

    @api.onchange('stamping_list')
    def domain_list(self):
        line = []
        request = self.env['stamping.list'].search([])
        for record in request:
            for rec in record.stamping_list:
                line.append(rec.id)
        domain = {'stamping_list': [('id', 'not in', line), ('type', '=', 'stamping'),
                                    ('state', 'not in', ('done', 'rejected', 'blocked'))]}
        return {'domain': domain}

    @api.multi
    def action_create_invoice(self):
        self.ensure_one()
        if not self.stamping_list:
            raise ValidationError(_('You must add lines in list'))
        append_labor = []
        name = ''
        for rec in self.stamping_list:
            append_labor.append(rec.labor_id.id)
            name += rec.labor_name
        invoice_line = []
        product = self.env['product.recruitment.config'].search([('type', '=', 'embassy')])[0]
        if not product.journal_id:
            raise ValidationError(_('Please, you must select journal in stamping from configration'))
        accounts = product.product.product_tmpl_id.get_product_accounts()
        invoice_line.append((0, 0, {
            'product_id': product.product.id,
            'labors_id': [(6, 0, append_labor)],
            'name': name,
            'product_uom_id': product.product.uom_id.id,
            'price_unit': product.price,
            'discount': 0.0,
            'quantity': float(len(self.stamping_list)),
            'account_id': accounts.get('stock_input') and accounts['stock_input'].id or \
                          accounts['expense'].id,
        }))
        cr = self.env['account.invoice'].create({
            'partner_id': self.embassy.id,
            'currency_id': product.currency_id.id,
            'type': 'in_invoice',
            'state': 'draft',
            'partner_type': self.embassy.vendor_type,
            'origin': self.name,
            'journal_id': product.journal_id.id,
            'account_id': self.embassy.property_account_payable_id.id,
            'invoice_line_ids': invoice_line,
        })
        cr.action_invoice_open()
        self.list_now_len = len(self.stamping_list)
        self.state = 'in_progress'
        for rec in self.stamping_list:
            rec.state = 'in_progress'

    # @api.multi
    # def unlink(self):
    #     for rec in self:
    #         if rec.state != 'new':
    #             raise ValidationError(_('You cannot delete %s as it is not in new state') % rec.name)
    #     return super(StampingList, self).unlink()

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('stamping.list')
        vals['assign_date'] = date.today()
        return super(StampingList, self).create(vals)
