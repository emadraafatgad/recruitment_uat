from odoo import fields, api, models,_
from odoo.exceptions import ValidationError
from datetime import  date


class TrainingCenter(models.Model):
    _name = 'training.center'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _inherits = {
        'res.partner': 'partner_id',
    }
    _description = 'Labor Profile'

    partner_id = fields.Many2one('res.partner', string='Related Partner', required=True, ondelete='cascade',
                                 help='Partner-related data of the patient')

    @api.model
    def create(self, vals):
        vals['vendor_type'] = 'training'
        vals['supplier'] = True
        vals['customer'] = False
        vals['company_type'] = 'company'
        labor = super(TrainingCenter, self).create(vals)
        return labor


class SlaveTraining(models.Model):
    _name = 'slave.training'
    _description = 'Training'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _sql_constraints = [('laborer_unique', 'unique(slave_id)', 'Created with this Laborer before!')]

    name = fields.Char(readonly=True)
    slave_id = fields.Many2one('labor.profile',string="Labor", domain="[('pre_medical_check','=','Fit')]")
    start_date = fields.Date(readonly=True)
    end_date = fields.Date(readonly=True)
    state = fields.Selection([('new', 'New'), ('in_progress', 'Inprogress'), ('rejected', 'Rejected'),('finished', 'Finished'),('blocked', 'Blocked')], default='new')
    training_center_id = fields.Many2one('res.partner',domain="[('vendor_type','=','training')]")
    note = fields.Text()
    phone = fields.Char()
    invoiced = fields.Boolean()
    passport_no = fields.Char(related='slave_id.passport_no',store=True)

    @api.multi
    def action_reject(self):
        self.ensure_one()
        request = self.env['slave.training'].search([('id', '=', self.id), ('state', '=', 'rejected')])
        if request:
            raise ValidationError(_('Done before'))
        labor = self.env['labor.profile'].search([('id', '=', self.slave_id.id)])
        type = ''
        price = 0.0
        for record in labor.labor_process_ids:
            if record.type != 'agent_payment':
                type += record.type + ' , '
                price += record.total_cost
        append_labor = []
        append_labor.append(self.slave_id.id)
        invoice_line = []
        purchase_journal = self.env['account.journal'].search([('type', '=', 'purchase')])[0]
        product = self.env['product.recruitment.config'].search([('type', '=', 'labor_reject')])[0]
        accounts = product.product.product_tmpl_id.get_product_accounts()
        invoice_line.append((0, 0, {
            'product_id': product.product.id,
            'labors_id': [(6,0, append_labor)],
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
        sequence = self.env['ir.sequence'].next_by_code('slave.training')
        vals['name'] = sequence
        labor = self.env['labor.profile'].search([('id', '=', vals['slave_id'])])
        for rec in labor:
            line = []
            line.append((0, 0, {
                'type': 'training',

            }))
            rec.labor_process_ids = line
        return super(SlaveTraining, self).create(vals)


class TrainingList(models.Model):
    _name = 'training.list'
    _description = 'Training List'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']

    name= fields.Char('Sequence',default='New',readonly=True)
    state = fields.Selection([('new', 'New'), ('in_progress', 'Inprogress'), ('finished', 'Finished')],default='new',track_visibility="onchange")
    start_date = fields.Date(track_visibility="onchange")
    end_date = fields.Date(track_visibility="onchange")

    training_center = fields.Many2one('res.partner', domain="[('vendor_type','=','training')]", track_visibility="onchange",required=True)
    training_requests = fields.Many2many('slave.training')
    bill = fields.Many2one('account.invoice')
    total_lines = fields.Integer(compute='compute_len_lines')
    list_now_len = fields.Integer()
    bill_state = fields.Char(compute='compute_bill_state')
    show_set_draft = fields.Char(compute='compute_show_set_draft')

    @api.depends('bill_id')
    def compute_bill_state(self):
        if self.bill_id:
            self.bill_state = self.bill_id.state.capitalize()


    @api.multi
    def set_to_draft(self):
        self.ensure_one()
        self.state = 'new'

    @api.onchange('training_requests')
    def domain_list(self):
        line = []
        request = self.env['training.list'].search([])
        for record in request:
            for rec in record.training_requests:
                line.append(rec.id)
        domain = {'training_requests': [('id', 'not in', line)]}
        return {'domain': domain}

    @api.onchange('training_requests')
    def onchange_list(self):
        if not self.state == 'new':
            if self.total_lines > self.list_now_len:
                raise ValidationError(_('You cannot add lines in this state'))
            if self.total_lines < self.list_now_len:
                raise ValidationError(_('You cannot remove lines in this state'))

    @api.one
    @api.depends('training_requests')
    def compute_len_lines(self):
        self.total_lines = len(self.training_requests)


    @api.depends('state','show')
    def compute_show_set_draft(self):
        if self.state == 'in_progress' and not self.show:
            self.show_set_draft = True
        else:
            self.show_set_draft = False
    @api.multi
    def unlink(self):
        for rec in self:
            if rec.state != 'new':
                raise ValidationError(_('You cannot delete %s as it is not in new state') % rec.name)
        return super(TrainingList, self).unlink()

    @api.constrains('training_center','training_requests')
    def constrain_training_requests(self):
        for rec in self.training_requests:
            rec.training_center_id = self.training_center


    show = fields.Boolean()
    bill_count = fields.Integer(compute='_compute_bill', string='Bill', default=0)
    bill_id = fields.Many2one('account.invoice', compute='_compute_bill', string='Bill', copy=False)

    def action_view_bill(self):
        action = self.env.ref('account.action_vendor_bill_template')
        result = action.read()[0]
        result.pop('id', None)
        result['context'] = {}
        b_ids = sum([line.bill_id.ids for line in self], [])
        if len(b_ids) > 1:
            result['domain'] = "[('id','in',[" + ','.join(map(str, b_ids)) + "])]"
        elif len(b_ids) == 1:
            res = self.env.ref('account.invoice_supplier_form', False)
            result['views'] = [(res and res.id or False, 'form')]
            result['res_id'] = b_ids and b_ids[0] or False
        return result

    def _compute_bill(self):
        bills = self.env['account.invoice'].search([
            ('origin', '=', self.name)
        ])
        self.bill_id = bills
        self.bill_count = len(bills)


    @api.multi
    def action_start(self):
        list = self.env['training.list'].search([('id', '=', self.id), ('state', '=', 'in_progress')])
        if list:
            raise ValidationError(_('Done before '))
        if not self.training_center:
            raise ValidationError(_('you must enter training center'))
        if len(self.training_requests) < 1:
            raise ValidationError(_('you must enter al least one line'))
        self.start_date = date.today()
        self.list_now_len = len(self.training_requests)
        for rec in self.training_requests:
            rec.state = 'in_progress'
            rec.start_date = self.start_date
        self.state = 'in_progress'

    @api.multi
    def action_finish(self):
        list = self.env['training.list'].search([('id', '=', self.id), ('state', '=', 'finished')])
        if list:
            raise ValidationError(_('Finished before '))
        self.end_date = date.today()
        for rec in self.training_requests:
            rec.state = 'finished'
            rec.end_date = self.end_date
            interpol = self.env['interpol.request'].search([('labor_id', '=', rec.slave_id.id)])
            agency = self.env['specify.agent'].search([('labor_id', '=', rec.slave_id.id)])
            if interpol.state == 'done' and agency.state in ('available','sent','selected'):
                self.env['labor.clearance'].create({
                    'labor_id': rec.slave_id.id,
                    'labor_name': rec.slave_id.name,
                    'passport_no': interpol.passport_no,
                    'gender': rec.slave_id.gender,
                    'job_title': rec.slave_id.occupation,
                    'contact': rec.slave_id.phone,
                    'lc1': rec.slave_id.lc1.id,
                    'lc2': rec.slave_id.lc2.id,
                    'lc3': rec.slave_id.lc3.id,
                    'district': rec.slave_id.district.id,
                    'agency': agency.agency.id,
                    'agency_code': agency.name,
                    #'destination_city': agency.destination_city.id,
                })
        self.state = 'finished'


    @api.multi
    def create_bill(self):
        list = self.env['training.list'].search([('id', '=', self.id), ('show', '=', True)])
        if list:
            raise ValidationError(_('Created before '))
        invoice_line = []
        purchase_journal = self.env['account.journal'].search([('type', '=', 'purchase')])[0]
        product = self.env['product.recruitment.config'].search([('type', '=', 'training')])[0]
        accounts = product.product.product_tmpl_id.get_product_accounts()
        description = ''
        append_labor = []
        for rec in self.training_requests:
            description += rec.slave_id.name + ','
            append_labor.append(rec.slave_id.id)
        invoice_line.append((0, 0, {
            'product_id': product.product.id,
            'labors_id':[(6,0, append_labor)],
            'name': description,
            'uom_id': product.product.uom_id.id,
            'price_unit': self.training_center.cost,
            'discount': 0.0,
            'quantity': len(self.training_requests),
            'account_id': accounts.get('stock_input') and accounts['stock_input'].id or \
                          accounts['expense'].id,
        }))
        cr = self.env['account.invoice'].create({
            'partner_id': self.training_center.id,
            'currency_id': product.currency_id.id,
            'state': 'draft',
            'type': 'in_invoice',
            'partner_type':self.training_center.vendor_type,
            'origin': self.name,
            'journal_id': purchase_journal.id,
            'account_id': self.training_center.property_account_payable_id.id,
            'invoice_line_ids': invoice_line,

        })
        self.show = True
        for rec in self.training_requests:
            rec.invoiced=True
        self.bill = cr.id

    @api.model
    def create(self, vals):
        sequence = self.env['ir.sequence'].next_by_code('training.list')
        vals['name'] = sequence
        return super(TrainingList, self).create(vals)
