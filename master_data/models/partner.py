from odoo import models, fields, api, _
from datetime import date
from odoo.exceptions import ValidationError
from odoo.exceptions import Warning


class PartnerRelativesDegrees(models.Model):
    _name = 'partner.relative.degree'

    name = fields.Char(required=True)


class PartnerRelatives(models.Model):
    _name = 'partner.relatives'

    name = fields.Char(required=True)
    relatives_degree = fields.Selection([('father', 'Father'), ('mother', 'Mother'), ('next_of_kin', 'Next Of Kin')],required=True,string='R Degrees')
    phone = fields.Char()
    national_id = fields.Char(string='ID',size=14)
    lc1 = fields.Many2one('labor.village', string='LC1')
    lc2 = fields.Many2one('labor.parish',string='LC2')
    lc3 = fields.Many2one('labor.subcounty',string='LC3')
    lc4 = fields.Many2one('labor.county',string='LC4')
    district = fields.Many2one('labor.district',string='District')
    tribe = fields.Many2one('labor.tribe')
    date_of_birth = fields.Date('DOB')
    nationality = fields.Many2one('res.country')
    note = fields.Char()
    partner_id = fields.Many2one('res.partner')


class Partner(models.Model):
    _inherit = 'res.partner'
    _sql_constraints = [('short_code_uniq', 'unique(short_code)', 'Short Code must be unique!')]
    is_slave = fields.Boolean('House Maid')
    gender = fields.Selection([("Male","Male"),("Female","Female")],string="type")
    age = fields.Integer(compute='_compute_slave_age')
    broker = fields.Many2one("master.broker",string="Brokers")
    date_of_birth = fields.Date("Date of Birth")
    relative_ids = fields.One2many('partner.relatives', 'partner_id')
    pre_medical_check = fields.Selection([('Fit', 'Fit'),('Unfit', 'Unfit')],default='Fit')
    reason = fields.Char()
    short_code = fields.Char()

    vendor_type = fields.Selection([('supplier','supplier'),('agent','Agent'),('nira_broker','Nira Broker'),('passport_broker','Passport Broker')
                                       ,('passport_placing_issue','Passport Placing Issue'),('interpol_broker','Interpol Broker'),
                                       ('gcc','Gcc'),('hospital','Hospital'),('enjaz','Enjaz'),('embassy','Embassy'),('travel_company','Travel Company'),('training','Training Center')])
    agency = fields.Boolean()



    agency_cost = fields.Float(track_visibility="onchange")
    cost = fields.Float(track_visibility="onchange")
    nira_cost = fields.Float(compute='compute_nira_cost')
    national_id_cost = fields.Float(track_visibility="onchange")
    passport_cost = fields.Float(track_visibility="onchange")
    express_passport_cost = fields.Float(string="Express Cost")
    accommodation_cost = fields.Float()

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100):
        if args is None:
            args = []
        if name:
            actions = self.search([('name', operator, name)] + args, limit=limit)
            return actions.name_get()
        return super(Partner, self)._name_search(name, args=args, operator=operator, limit=limit)

    @api.depends('national_id_cost')
    def compute_nira_cost(self):
        for rec in self:
            nira = self.env['product.recruitment.config'].search([('type', '=', 'nira')])
            if rec.national_id_cost:
               rec.nira_cost = rec.national_id_cost - nira.price

    @api.constrains('cost')
    def constrains_cost(self):
        if self.vendor_type in ('passport_broker','interpol_broker','passport_placing_issue','hospital') and self.cost <= 0:
            raise ValidationError(_('You must enter Cost.'))

    # @api.constrains('nira_cost','national_id_cost','passport_cost')
    # def constrains_agent_cost(self):
    #     if self.vendor_type == 'agent' and (
    #             self.nira_cost <= 0 or self.national_id_cost <= 0 or self.passport_cost <= 0):
    #         raise ValidationError(_('You must enter all agent costs.'))

    @api.depends('date_of_birth')
    def _compute_slave_age(self):

        current_dt = date.today()
        for rec in self:
            if rec.date_of_birth:
                start = rec.date_of_birth
                age_calc = ((current_dt - start).days / 365)
                # Age should be greater than 0
                if age_calc > 21:
                    rec.age = age_calc
                else :
                    raise ValidationError(_('Not Enough reserved Qty.'))
    # <record id="labor_identification_code" model="ir.sequence">
    #         <field name="name">HouseMaid Identification Code</field>
    #         <field name="code">house.maid</field>
    #         <field name="prefix">HM/%(year)s/</field>
    #         <field name="padding">5</field>
    #         <field name="company_id" eval="False"/>
    #     </record>

    @api.model
    def create(self,vals):
        if self.agency:
            super(Partner, self).create(vals)
            sequence = self.env['ir.sequence'].create({
                'name': self.name,
                'code': self.name,
                'prefix': self.short_code,
                'padding': 5,
            })
        return super(Partner, self).create(vals)
