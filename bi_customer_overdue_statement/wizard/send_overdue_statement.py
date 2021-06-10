# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.
##############################################################################
from odoo import fields, models


class account_report_partner_ledger(models.TransientModel):
    _name = "send.overdue.statement"

    confirm_text = fields.Char(default="Press Send Overdue Payment to send email notification to customer",readonly=True)

    def send_overdue_statement_customer(self):

    	res = self.env['res.partner'].browse(self._context.get('active_ids',[]))
    	for user in res :
    		user.do_partner_mail()

    	return
    
