# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models

class Company(models.Model):
    _inherit = 'res.company'
    
    send_statement = fields.Boolean("Send Customer Statement")
    period = fields.Selection([('monthly', 'Monthly'),('all', "All")],'Period',default='monthly')
    statement_days = fields.Integer("Statement Send Date")
    
    overdue_days = fields.Integer("Overdue Statement Send Date")
    send_overdue_statement = fields.Boolean("Send Overdue Customer Statement")
    filter_statement = fields.Selection([('filter_only','View Only Filter Statements'),('all_statement','View All Statements Along With Filter Statements')],string="Filter Statement")