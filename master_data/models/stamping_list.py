from odoo import fields, models , api,_
from datetime import date

from odoo.exceptions import ValidationError


class StampingList(models.Model):
    _name = 'stamping.list'
    _description = 'Stamping List'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(string="Number",readonly=True,default='New')
    state = fields.Selection([('new','New'),('in_progress','InProgress'),('done','Done')],default='new',track_visibility="onchange")
    stamping_list = fields.Many2many('labor.enjaz.stamping')
    list_total_count = fields.Integer(compute='_compute_value')
    assign_date = fields.Date()
    list_now_len = fields.Integer()
    def _get_embassy_default(self):
        embassy = self.env['res.partner'].search([('vendor_type', '=', 'embassy')])
        if not embassy:
            raise ValidationError(_('Embassy Partner is not exist,you can create partner its type is embassy'))
        return embassy[0].id

    embassy = fields.Many2one('res.partner',readonly=True, domain=[('vendor_type', '=', 'embassy')],default=_get_embassy_default)

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
            if self.list_total_count > self.list_now_len:
                raise ValidationError(_('You cannot add lines in this state'))
            if self.list_total_count < self.list_now_len:
                raise ValidationError(_('You cannot remove lines in this state'))

    @api.onchange('stamping_list')
    def domain_list(self):
        line = []
        request = self.env['stamping.list'].search([])
        for record in request:
            for rec in record.stamping_list:
                line.append(rec.id)
        domain = {'stamping_list': [('id', 'not in', line),('type', '=', 'stamping')]}
        return {'domain': domain}

    # def action_create_invoice(self):


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

