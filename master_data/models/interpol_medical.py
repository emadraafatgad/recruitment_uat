from odoo import api, models, tools

import logging
import threading

_logger = logging.getLogger(__name__)


class InterpolUpdateGcc(models.TransientModel):
    _name = 'interpol.gcc.update'
    _description = 'Update Gcc from Interpol'

    def update_gcc_from_interpol(self):
        interpols = self.env['interpol.request'].search([('state','=','done'),('gcc_updated', '=', False)])
        for interpol in interpols:
            gcc = self.env['big.medical'].search([('labor_id','=',interpol.labor_id.id),('interpol_done','=',False)])
            gcc.write({'interpol_done': True})
            interpol.gcc_updated = True

    # def procure_calculation(self):
    #     threaded_calculation = threading.Thread(target=self._procure_calculation_orderpoint, args=())
    #     threaded_calculation.start()
    #     return {'type': 'ir.actions.act_window_close'}