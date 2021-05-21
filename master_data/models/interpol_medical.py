from odoo import api, models, tools

import logging
import threading

_logger = logging.getLogger(__name__)


class InterpolUpdateGcc(models.TransientModel):
    _name = 'interpol.gcc.update'
    _description = 'Update Gcc from Interpol'

    def update_gcc_from_interpol(self):
        interpols = self.env['interpol.request'].search([('state', '=', 'done'), ('gcc_updated', '=', False)])
        for interpol in interpols:
            gcc = self.env['big.medical'].search(
                [('labor_id', '=', interpol.labor_id.id), ('interpol_done', '=', False)])
            gcc.write({'interpol_done': True})
            interpol.gcc_updated = True

    def update_agency_medical_interpol(self):
        interpols = self.env['interpol.request'].search([])
        for interpol in interpols:
            agency = self.env['specify.agent'].search([('labor_id', '=', interpol.labor_id.id)])
            agency.interpol_state = interpol.state
        big_medicals = self.env['big.medical'].search([])
        for big_medical in big_medicals:
            agency = self.env['specify.agent'].search([('labor_id', '=', big_medical.labor_id.id)])
            agency.medical_state = big_medical.state
