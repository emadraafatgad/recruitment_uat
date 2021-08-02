from odoo import fields, models , api,_
from odoo.exceptions import ValidationError


class TravelList(models.Model):
    _name = 'travel.list'
    _description = 'Travel List'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(string="Number",readonly=True,default='New')
    travel_list = fields.Many2many('travel.company')
    travel_company = fields.Many2one('res.partner',domain=[('vendor_type','=','travel_company')])
    state = fields.Selection([('new', 'new'),('in_progress', 'InProgress'),('done', 'Done')], default='new',track_visibility='onchange')
    list_total_count = fields.Integer(compute='_compute_value')
    list_now_len = fields.Integer()
    booking_date = fields.Date()
    flight_details = fields.Char()

    @api.one
    @api.depends('travel_list')
    def _compute_value(self):
        self.list_total_count = len(self.travel_list)

    @api.constrains('travel_company','travel_list')
    def const_travel_list(self):
        for rec in self.travel_list:
            rec.travel_list_id = self.id
            rec.travel_company = self.travel_company.id

    @api.multi
    def action_done_all_list(self):
        self.state = 'done'

    @api.onchange('travel_list')
    def domain_list(self):
        line = []
        request = self.env['travel.list'].search([])
        for record in request:
            for rec in record.travel_list:
                line.append(rec.id)
        domain = {'travel_list': [('id', 'not in', line),('state', '=', 'new')]}
        return {'domain': domain}

    def action_inprogress(self):
        self.list_now_len = len(self.travel_list)
        for line in self.travel_list:
            line.action_in_progress(self.travel_company,self.name)
            self.state = 'in_progress'

    @api.onchange('travel_list')
    def onchange_travel_list(self):
        if not self.state == 'new':
            if self.list_total_count > self.list_now_len:
                raise ValidationError(_('You cannot add lines in this state'))
            if self.list_total_count < self.list_now_len:
                raise ValidationError(_('You cannot remove lines in this state'))


    @api.multi
    def unlink(self):
       for rec in self:
             if rec.state != 'new':
                raise ValidationError(_('You cannot delete %s as it is not in new state') % rec.name)
       return super(TravelList, self).unlink()

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('travel.list')
        return super(TravelList, self).create(vals)

