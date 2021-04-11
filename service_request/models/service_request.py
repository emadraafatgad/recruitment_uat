# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
import datetime


class ServiceRequest(models.Model):
    _name = 'service.request'

    partner_id = fields.Many2one('res.partner',domain="[('is_customer','=',True)]",
                                 string='Related Partner', required=False, ondelete='cascade')
    request_date = fields.Datetime('Date', required=False)
    coiffure_id = fields.Many2one('hr.employee')
    time = fields.Float('Time')
    Customer_type = fields.Selection([('new', 'New Customer'), ('old', 'Old Customer')],default='new')
    customer_name = fields.Char()
    phone = fields.Char()
    picture = fields.Binary()
    add_tips = fields.Text()
    add_advice = fields.Text()
    final_picture = fields.Binary()
    final_color = fields.Many2one('product.product')
    color = fields.Many2one("product.product", string="requested color",)