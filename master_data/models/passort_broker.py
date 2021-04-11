from odoo import fields, models,api,_
from datetime import date,datetime
from odoo.exceptions import ValidationError


class PassportBroker(models.Model):
    _name = 'passport.broker'
    _description = 'Passport Broker Assign'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name= fields.Char('sequence',default='New')
    broker = fields.Many2one('res.partner',required=True,domain=[('vendor_type','=','passport_broker')])
    assign_date = fields.Datetime(default=datetime.now())
    deadline = fields.Date()
    passport_request = fields.Many2many('passport.request', string='Passport Requests',required=True)
    state = fields.Selection([('new', 'new'), ('assigned', 'Assigned'),('done', 'Done')], default='new', track_visibility="onchange")
    list_total_count = fields.Integer(compute='_compute_value')
    done_count = fields.Integer(compute='_compute_value')
    remaining_count = fields.Integer(compute='_compute_value')
    list_now_len = fields.Integer()

    @api.one
    @api.depends('passport_request')
    def _compute_value(self):
        self.list_total_count = len(self.passport_request)
        self.done_count = len([rec for rec in self.passport_request if rec.state == 'done'])
        self.remaining_count = len([rec for rec in self.passport_request if rec.state != 'done'])

    @api.constrains('broker','passport_request')
    def const_broker_list(self):
        for rec in self.passport_request:
            rec.broker_list_id = self.id
            rec.broker = self.broker


    @api.onchange('passport_request')
    def onchange_len_list(self):
        if not self.state == 'new':
            if self.list_total_count > self.list_now_len:
                raise ValidationError(_('You cannot add lines in this state'))
            if self.list_total_count < self.list_now_len:
                raise ValidationError(_('You cannot remove lines in this state'))


    @api.onchange('passport_request')
    def domain_list(self):
        line = []
        request = self.env['passport.broker'].search([])
        for record in request:
            for rec in record.passport_request:
                line.append(rec.id)
        domain = {'passport_request': [('id', 'not in', line),('state','=','invoiced')]}
        return {'domain': domain}


    @api.multi
    def action_assign(self):
        if self.list_total_count < 1:
            raise ValidationError(_('You must enter at least one line'))
        if not self.deadline:
            raise ValidationError(_('Enter Deadline for list'))

        self.assign_date= datetime.now()
        for list in self.passport_request:
            if list.state == 'releasing':
                raise ValidationError(_('you try to release request that already released!'))
            list.state= 'releasing'
            list.end_date= self.assign_date
            list.deadline= self.deadline

        self.list_now_len=len(self.passport_request)
        self.state = 'assigned'

    @api.multi
    def action_confirm(self):
        for list in self.passport_request:
            if list.passport_no and list.pass_start_date and list.pass_end_date and list.pass_from:
               list.request_passport_done()
               list.labor_id.request_interpol()
               list.labor_id.big_medical_request()
               list.labor_id.specify_agency_request()
            else:
                raise ValidationError(_('You must enter passport information to all list'))
        self.state = 'done'

    @api.onchange('passport_request')
    def default(self):
        next_sequence = 1
        for list in self.passport_request:
            list.seq = next_sequence
            list.row_num = str(list.seq) + "/" + str(len(self.passport_request))
            next_sequence += 1

    # @api.multi
    # def unlink(self):
    #     for rec in self:
    #         if rec.state != 'new':
    #             raise ValidationError(_('You cannot delete %s as it is not in new state') % rec.name)
    #     return super(PassportBroker, self).unlink()
    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('passport.broker')

        return super(PassportBroker, self).create(vals)