import logging

from odoo import models

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
        travels = self.env['travel.company'].search([])
        for travel in travels:
            agency = self.env['specify.agent'].search([('labor_id', '=', travel.labor_id.id)])
            if travel.state == 'done':
                agency.state = 'traveled'

    def update_intepol_labours(self):
        interpols = self.env['interpol.broker'].search([])
        for interpol in interpols:
            labour_list = []
            for line in interpol.interpol_request:
                labour_list.append(line.labor_id.id)
            interpol.labour_ids = labour_list

    def update_passports_labours(self):
        passports = self.env['passport.broker'].search([])
        for passport in passports:
            passport_list = []
            for line in passport.passport_request:
                passport_list.append(line.labor_id.id)
            passport.labour_ids = passport_list

    def update_training_labours(self):
        trainings = self.env['training.list'].search([])
        for training in trainings:
            training_list = []
            for line in training.training_requests:
                training_list.append(line.slave_id.id)
            training.labour_ids = training_list

    def update_clearance_labours(self):
        clearances = self.env['clearance.list'].search([])
        for clearance in clearances:
            training_list = []
            for line in clearance.clearance_list:
                training_list.append(line.labor_id.id)
            clearance.labour_ids = training_list

    def update_stamping_labours(self):
        stampings = self.env['stamping.list'].search([])
        for stamping in stampings:
            stamping_list = []
            for line in stamping.stamping_list:
                stamping_list.append(line.labor_id.id)
            stamping.labour_ids = stamping_list
