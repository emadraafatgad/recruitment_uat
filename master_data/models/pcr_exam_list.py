from odoo import fields, api, models,_
from odoo.exceptions import ValidationError
from datetime import  date


class PCRExamList(models.Model):
    _name = 'pcr.exam.list'
    _description = 'PCR Exam List'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name= fields.Char('Sequence',default='New',readonly=True)
    hospital_id = fields.Many2one('res.partner', domain=[('vendor_type', '=', 'hospital')], track_visibility="onchange")
    exam_date = fields.Date(track_visibility="onchange")
    total_lines = fields.Integer(compute='compute_total_lines')
    exam_requests = fields.Many2many('pcr.exam')
    state = fields.Selection([('new', 'New'), ('in_progress', 'Inprogress'), ('finished', 'Finished')],default='new',track_visibility="onchange")

    @api.depends('exam_requests')
    def compute_total_lines(self):
        for line in self:
            line.total_lines = len(line.exam_requests)

    @api.multi
    def confirm_exam_list_lines(self):
        if not self.hospital_id:
            raise ValidationError(_('you must enter Hospital'))
        if len(self.exam_requests) < 1:
            raise ValidationError(_('you must enter al least one line'))
        # self.start_date = date.today()
        # self.list_now_len = len(self.training_requests)
        for rec in self.exam_requests:
            rec.state = 'in_progress'
            rec.start_date = self.start_date
        self.state = 'in_progress'

    # bill = fields.Many2one('account.invoice')

    # list_now_len = fields.Integer()
    # bill_state = fields.Char(compute='compute_bill_state')

    # show = fields.Boolean()


    # bill_count = fields.Integer(compute='_compute_bill', string='Bill', default=0)
    # bill_id = fields.Many2one('account.invoice', compute='_compute_bill', string='Bill', copy=False)

    # @api.depends('bill_id')
    # def compute_bill_state(self):
    #     if self.bill_id:
    #         self.bill_state = self.bill_id.state.capitalize()
    #
    # @api.onchange('training_requests')
    # def domain_list(self):
    #     line = []
    #     request = self.env['training.list'].search([])
    #     for record in request:
    #         for rec in record.training_requests:
    #             line.append(rec.id)
    #     domain = {'training_requests': [('id', 'not in', line)]}
    #     return {'domain': domain}
    #
    #
    # @api.onchange('training_requests')
    # def onchange_list(self):
    #     if not self.state == 'new':
    #         if self.total_lines > self.list_now_len:
    #             raise ValidationError(_('You cannot add lines in this state'))
    #         if self.total_lines < self.list_now_len:
    #             raise ValidationError(_('You cannot remove lines in this state'))
    #

    #
    #
    # @api.multi
    # def unlink(self):
    #     for rec in self:
    #         if rec.state != 'new':
    #             raise ValidationError(_('You cannot delete %s as it is not in new state') % rec.name)
    #     return super(PCRExamList, self).unlink()
    #
    # @api.constrains('training_center','training_requests')
    # def constrain_training_requests(self):
    #     for rec in self.training_requests:
    #         rec.training_center_id = self.training_center
    #
    #
    #
    # def action_view_bill(self):
    #     action = self.env.ref('account.action_vendor_bill_template')
    #     result = action.read()[0]
    #     result.pop('id', None)
    #     result['context'] = {}
    #     b_ids = sum([line.bill_id.ids for line in self], [])
    #     if len(b_ids) > 1:
    #         result['domain'] = "[('id','in',[" + ','.join(map(str, b_ids)) + "])]"
    #     elif len(b_ids) == 1:
    #         res = self.env.ref('account.invoice_supplier_form', False)
    #         result['views'] = [(res and res.id or False, 'form')]
    #         result['res_id'] = b_ids and b_ids[0] or False
    #     return result
    #
    # def _compute_bill(self):
    #     bills = self.env['account.invoice'].search([
    #         ('origin', '=', self.name)
    #     ])
    #     self.bill_id = bills
    #     self.bill_count = len(bills)



    # @api.multi
    # def action_finish(self):
    #     self.end_date = date.today()
    #     for rec in self.training_requests:
    #         rec.state = 'finished'
    #         rec.end_date = self.end_date
    #         interpol = self.env['interpol.request'].search([('labor_id', '=', rec.slave_id.id)])
    #         agency = self.env['specify.agent'].search([('labor_id', '=', rec.slave_id.id)])
    #         if interpol.state == 'done' and agency.state in ('available','sent','selected'):
    #             self.env['labor.clearance'].create({
    #                 'labor_id': rec.slave_id.id,
    #                 'labor_name': rec.slave_id.name,
    #                 'passport_no': interpol.passport_no,
    #                 'gender': rec.slave_id.gender,
    #                 'job_title': rec.slave_id.occupation,
    #                 'contact': rec.slave_id.phone,
    #                 'lc1': rec.slave_id.lc1.id,
    #                 'lc2': rec.slave_id.lc2.id,
    #                 'lc3': rec.slave_id.lc3.id,
    #                 'district': rec.slave_id.district.id,
    #                 'agency': agency.agency.id,
    #                 'agency_code': agency.name,
    #                 'destination_city': agency.destination_city,
    #             })
    #     self.state = 'finished'
    #
    #
    # @api.multi
    # def create_bill(self):
    #     invoice_line = []
    #     purchase_journal = self.env['account.journal'].search([('type', '=', 'purchase')])[0]
    #     product = self.env['product.recruitment.config'].search([('type', '=', 'training')])[0]
    #     accounts = product.product.product_tmpl_id.get_product_accounts()
    #     description = ''
    #     append_labor = []
    #     for rec in self.training_requests:
    #         description += rec.slave_id.name + ','
    #         append_labor.append(rec.slave_id.id)
    #     invoice_line.append((0, 0, {
    #         'product_id': product.product.id,
    #         'labors_id':[(6,0, append_labor)],
    #         'name': description,
    #         'uom_id': product.product.uom_id.id,
    #         'price_unit': self.training_center.partner_id.cost,
    #         'discount': 0.0,
    #         'quantity': len(self.training_requests),
    #         'account_id': accounts.get('stock_input') and accounts['stock_input'].id or \
    #                       accounts['expense'].id,
    #     }))
    #     cr = self.env['account.invoice'].create({
    #         'partner_id': self.hospital_id.id,
    #         'currency_id': product.currency_id.id,
    #         'state': 'draft',
    #         'type': 'in_invoice',
    #         'partner_type':self.hospital_id.vendor_type,
    #         'origin': self.name,
    #         'journal_id': purchase_journal.id,
    #         'account_id': self.training_center.partner_id.property_account_payable_id.id,
    #         'invoice_line_ids': invoice_line,
    #
    #     })
    #     self.show = True
    #     self.bill = cr.id
    @api.multi
    def unlink(self):
        for rec in self:
            if rec.state != 'new':
                raise ValidationError(_('You cannot delete %s as it is not in new state') % rec.name)
        return super(PCRExamList, self).unlink()
    @api.model
    def create(self, vals):
        sequence = self.env['ir.sequence'].next_by_code('pcr.exam.list')
        vals['name'] = sequence
        return super(PCRExamList, self).create(vals)
