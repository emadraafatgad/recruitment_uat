from odoo import fields, models,api,_
from datetime import date,datetime

from odoo.exceptions import ValidationError


class InterpolBroker(models.Model):
    _name = 'interpol.broker'
    _description = 'Interpol Broker Assign'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(string="Number",track_visibility="onchange",readonly=True,default='New')
    broker = fields.Many2one('res.partner',track_visibility="onchange",required=True,domain=[('vendor_type','=','interpol_broker')])
    assign_date = fields.Datetime(default=datetime.now(),track_visibility="onchange")
    interpol_request = fields.Many2many('interpol.request',track_visibility="onchange", string='Interpol Requests',required=True)
    state = fields.Selection([('new', 'new'), ('assigned', 'Assigned'), ('partially_done', 'Partially Done'), ('done', 'Done')], default='new', track_visibility="onchange")
    list_total_count = fields.Integer(compute='_compute_value',)
    done_count = fields.Integer(compute='_compute_value')
    remaining_count = fields.Integer(compute='_compute_value')
    list_now_len = fields.Integer(track_visibility="onchange")

    @api.onchange('passport_request')
    def onchange_len_list(self):
        if not self.state == 'new':
            if self.list_total_count > self.list_now_len:
                raise ValidationError(_('You cannot add lines in this state'))
            if self.list_total_count < self.list_now_len:
                raise ValidationError(_('You cannot remove lines in this state'))
    @api.one
    @api.depends('interpol_request')
    def _compute_value(self):
        self.list_total_count = len(self.interpol_request)
        self.done_count = len([rec for rec in self.interpol_request if rec.state == 'done'])
        self.remaining_count = len([rec for rec in self.interpol_request if rec.state != 'done'])

    @api.multi
    def action_assign(self):
        if self.list_total_count < 1:
            raise ValidationError(_('You must enter at least one line'))
        self.assign_date =datetime.now()
        for list in self.interpol_request:
            list.state= 'assigned'
            list.end_date= self.assign_date
        self.list_now_len = len(self.interpol_request)
        self.state = 'assigned'

    @api.onchange('interpol_request')
    def domain_list(self):
        line = []
        request = self.env['interpol.broker'].search([])
        for record in request:
            for rec in record.interpol_request:
                line.append(rec.id)
        domain = {'interpol_request': [('id', 'not in', line),('state', '=', 'new')]}
        return {'domain': domain}

    @api.constrains('broker','interpol_request')
    def const_broker_list(self):
        for rec in self.interpol_request:
            rec.broker_list_id = self.id
            rec.broker = self.broker

    # @api.multi
    # def unlink(self):
    #     for rec in self:
    #         if rec.state != 'new':
    #             raise ValidationError(_('You cannot delete %s as it is not in new state') % rec.name)
    #     return super(InterpolBroker, self).unlink()
    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('interpol.broker')

        return super(InterpolBroker, self).create(vals)


class InterpolAccountInvoice(models.Model):
    _inherit = 'account.invoice'
    partner_type = fields.Selection([('agent', 'Agent'), ('nira_broker', 'Nira Broker'),('passport_broker', 'Passport Broker'),
                                    ('passport_placing_issue', 'Passport Placing Issue'),
                                    ('interpol_broker', 'Interpol Broker'), ('gcc', 'Gcc'), ('hospital', 'Hospital'),('enjaz','Enjaz'),
                                    ('embassy', 'Embassy'), ('travel_company', 'Travel Company'),
                                    ('training', 'Training Center'),('agency', 'Agency')])
    laborer = fields.Many2many('labor.profile', related='invoice_line_ids.labors_id')
    @api.multi
    def action_invoice_open(self):
        if self.partner_id.vendor_type == 'travel_company':
            for rec in self.invoice_line_ids:
                if rec.price_unit == 0:
                    raise ValidationError(_('You must enter price.'))
        origin = self.env['interpol.broker'].search([('name', '=', self.origin)])
        for list in origin.interpol_request:
            list.invoice_id = self.id

        return super(InterpolAccountInvoice, self).action_invoice_open()


class PartnerPayments(models.Model):
    _inherit = 'account.payment'

    @api.multi
    def action_validate_invoice_payment(self):
        for record in self.invoice_ids:
            if record.type == 'in_invoice':
                for rec in record.invoice_line_ids:
                    for lab in rec.labors_id:
                        if self.partner_id.vendor_type == 'nira_broker':
                            labor = self.env['labor.process'].search(
                                [('labor', 'in', lab.ids), ('type', '=', 'nira')])
                            labor.cost += rec.price_unit
                        if self.partner_id.vendor_type == 'passport_broker' or self.partner_id.vendor_type == 'passport_placing_issue':
                            labor = self.env['labor.process'].search(
                                [('labor', 'in', lab.ids), ('type', '=', 'passport')])
                            if len(labor)>1:
                                raise ValidationError(_("Not Accepted many labor process for %s %s %s" %(labor,self.communication,self.partner_id.name)))
                            labor.cost += rec.price_unit
                        if self.partner_id.vendor_type == 'interpol_broker':
                            labor = self.env['labor.process'].search(
                                [('labor', 'in', lab.ids), ('type', '=', 'interpol')])
                            labor.cost += rec.price_unit
                        if self.partner_id.vendor_type == 'gcc' or self.partner_id.vendor_type == 'hospital':
                            labor = self.env['labor.process'].search(
                                [('labor', 'in', lab.ids), ('type', '=', 'big_medical')],limit=1)
                            labor.cost += rec.price_unit
                        if self.partner_id.vendor_type == 'enjaz':
                            labor = self.env['labor.process'].search(
                                [('labor', 'in', lab.ids), ('type', '=', 'enjaz')])
                            labor.cost += rec.price_unit
                        if self.partner_id.vendor_type == 'embassy':
                            labor = self.env['labor.process'].search(
                                [('labor', 'in', lab.ids), ('type', '=', 'stamping')])
                            labor.cost += rec.price_unit
                        if self.partner_id.vendor_type == 'travel_company':
                            labor = self.env['labor.process'].search(
                                [('labor', 'in', lab.ids), ('type', '=', 'travel_company')])
                            labor.cost += rec.price_unit
                        if self.partner_id.vendor_type == 'training':
                            labor = self.env['labor.process'].search(
                                [('labor', 'in', lab.ids), ('type', '=', 'training')])
                            labor.cost += rec.price_unit
                        #if self.partner_id.vendor_type == 'training' and self.accommodation:
                          #  labor = self.env['labor.process'].search(
                             #   [('labor', 'in', lab.ids), ('type', '=', 'accommodation')])
                            #labor.cost += rec.price_unit


        return super(PartnerPayments, self).action_validate_invoice_payment()


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'
    labors_id = fields.Many2many('labor.profile')
    labor_id = fields.Many2one('labor.profile')



