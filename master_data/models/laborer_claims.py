from datetime import date

from odoo import fields, models, api
from odoo.exceptions import ValidationError

class LaborerClaims(models.Model):
    _name = 'laborer.claims'
    _description = 'laborer Claim'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Sequence", default='New')
    contact = fields.Char(track_visibility="onchange",compute="onchange_labor",store=True)
    date = fields.Date(default=date.today(), required=True, track_visibility="onchange")
    labor_id = fields.Many2one('labor.profile', domain="[('state','=','travelled')]", required=True,
                               track_visibility="onchange")
    passport_no = fields.Char(related='labor_id.passport_no', track_visibility="onchange")
    employer = fields.Char(track_visibility="onchange",compute="onchange_labor",store=True)
    agency = fields.Many2one('res.partner',compute="onchange_labor",store=True, domain=[('agency', '=', True)], track_visibility="onchange")
    visa_no = fields.Char(track_visibility="onchange",compute="onchange_labor",store=True)
    reservation_no = fields.Char(track_visibility="onchange",compute="onchange_labor",store=True)
    destination_city = fields.Many2one('res.country.state',compute="onchange_labor",store=True, track_visibility="onchange")
    destination_country = fields.Many2one('res.country', related='labor_id.country_id', store=True)
    departure_date = fields.Date(compute="onchange_labor",store=True)
    problem = fields.Text(track_visibility="onchange")
    response = fields.Text(track_visibility="onchange")
    travel_company = fields.Many2one('res.partner',compute="onchange_labor",store=True, domain=[('vendor_type', '=', 'travel_company')],
                                     track_visibility="onchange")
    state = fields.Selection(
        [('new', 'New'), ('in_progress', 'In Progress'), ('done', 'Done'), ], default="new"
    )

    def action_claim_in_progress(self):
        self.state = 'in_progress'
        if not self.problem:
            raise ValidationError("please add problem")

    def action_claim_done(self):
        self.state = 'done'
        if not self.response:
            raise ValidationError("please add response")

    @api.depends('labor_id')
    def onchange_labor(self):
        labor_trav = self.env['travel.company'].search([('labor_id', '=', self.labor_id.id)], limit=1)
        if self.labor_id:
            self.agency = labor_trav.agency.id
            self.contact = self.labor_id.phone
            self.employer = labor_trav.employer
            self.visa_no = labor_trav.visa_no
            self.destination_city = labor_trav.destination_city.id
            self.travel_company = labor_trav.travel_company.id
            self.reservation_no = labor_trav.reservation_no
            self.departure_date = labor_trav.departure_date

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('laborer.claims')
        return super(LaborerClaims, self).create(vals)
