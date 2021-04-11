# -*- coding: utf-8 -*-

from odoo import models, fields, api

class JournalEdit(models.Model):
    _name = 'account.move'
    _inherit = ['account.move','portal.mixin', 'mail.thread', 'mail.activity.mixin']

    state = fields.Selection([('draft', 'Unposted'), ('posted', 'Posted')], string='Status',
                             required=True, readonly=True, copy=False, default='draft',track_visibility="onchange",
                             help='All manually created new journal entries are usually in the status \'Unposted\', '
                                  'but you can set the option to skip that status on the related journal. '
                                  'In that case, they will behave as journal entries automatically created by the '
                                  'system on document validation (invoices, bank statements...) and will be created '
                                  'in \'Posted\' status.')
