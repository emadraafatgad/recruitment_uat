from datetime import date

from odoo import fields, models, api


class LaborerClaim(models.Model):
    _name = 'laborer.claim'
    _description = 'laborer Claim'
    # _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    name = fields.Char(string="Sequence", default='New')
    contact = fields.Char(track_visibility="onchange")
    date = fields.Date(default=date.today(), track_visibility="onchange")
    labor_id = fields.Many2one('labor.profile', track_visibility="onchange")
    passport_no = fields.Char(related='labor_id.passport_no', track_visibility="onchange")
    employer = fields.Char(track_visibility="onchange")
    agency = fields.Many2one('res.partner', domain=[('agency', '=', True)], track_visibility="onchange")
    visa_no = fields.Char(track_visibility="onchange")
    reservation_no = fields.Char(track_visibility="onchange")
    destination_city = fields.Many2one('res.country.state', track_visibility="onchange")
    destination_country = fields.Many2one('res.country', related='destination_city.country_id', store=True)
    departure_date = fields.Date()
    problem = fields.Text(track_visibility="onchange")
    response = fields.Text(track_visibility="onchange")
    travel_company = fields.Many2one('res.partner', domain=[('vendor_type', '=', 'travel_company')],
                                     track_visibility="onchange")

    @api.onchange('labor_id')
    def onchange_labor(self):
        labor_trav = self.env['travel.company'].search([('labor_id', '=', self.labor_id.id)], limit=1)
        if self.labor_id:
            self.agency = labor_trav.agency.id
            self.contact = self.labor_id.phone
            # self.passport_no = self.labor_id.passport_no
            self.employer = labor_trav.employer
            self.visa_no = labor_trav.visa_no
            self.destination_city = labor_trav.destination_city.id
            # self.destination_country = labor_trav.destination_city.country_id.id
            self.travel_company = labor_trav.travel_company.id
            self.reservation_no = labor_trav.reservation_no
            self.departure_date = labor_trav.departure_date

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('laborer.claim')
        return super(LaborerClaim, self).create(vals)
