# from extra.master_data.models.interpol_request import InterpolRequest
from odoo import fields, models , api,_
from datetime import date
from dateutil.relativedelta import relativedelta


class LaborClearance(models.Model):
    _name = 'labor.clearance'
    _order = 'id desc'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    state = fields.Selection([('new','New'),('rejected','Rejected'),('confirmed','Confirmed')],default='new',track_visibility="onchange")
    name = fields.Char(string="Number",readonly=True,default='New')
    labor_id = fields.Many2one('labor.profile',required=True)
    labor_name = fields.Char()
    agency = fields.Many2one('res.partner',domain=[('agency','=',True)],required=True)
    lc1 = fields.Many2one('labor.village',required=True)
    lc2 = fields.Many2one('labor.parish',required=True)
    lc3 = fields.Many2one('labor.subcounty',required=True)
    district = fields.Many2one('labor.district',required=True)
    job_title = fields.Selection([('house_maid', 'House Maid'), ('pro_maid', 'Pro Maid'),('pro_worker','Pro Worker')],required=True)
    gender = fields.Selection([('Male', 'Male'), ('Female', 'Female')],required=True)
    contact = fields.Char(required=True)
    passport_no = fields.Char(required=True)
    agency_code = fields.Char(required=True)
    destination_city = fields.Many2one('res.country.state',)
    destination_country = fields.Many2one('res.country',related='agency.country_id', required=True)

    @api.multi
    def action_confirm(self):
        self.ensure_one()
        stamping = self.env['labor.enjaz.stamping'].search([('type', '=', 'stamping'),('labor_id', '=', self.labor_id.id)])
        if stamping.state == 'done':
            self.env['travel.company'].create({
                'labor_id': self.labor_id.id,
                'labor_name': self.labor_name,
                'passport_no': self.labor_id.passport_no,
                'agency': stamping.agency.id,
                'agency_code': self.agency_code,
                'destination_city': stamping.city.id,
                'employer': stamping.employer,
                'visa_no': stamping.visa_no,
            })

        self.state = 'confirmed'

    @api.multi
    def action_reject(self):
        self.ensure_one()
        labor = self.env['labor.profile'].search([('id', '=', self.labor_id.id)])
        type = ''
        price = 0.0
        for record in labor.labor_process_ids:
            if record.type != 'agent_payment':
                type += record.type + ' , '
                price += record.total_cost
        append_labor = []
        append_labor.append(self.labor_id.id)
        invoice_line = []
        purchase_journal = self.env['account.journal'].search([('type', '=', 'purchase')])[0]
        product = self.env['product.recruitment.config'].search([('type', '=', 'labor_reject')])[0]
        accounts = product.product.product_tmpl_id.get_product_accounts()
        invoice_line.append((0, 0, {
            'product_id': product.product.id,
            'labors_id': [(6,0, append_labor)],
            'name': type,
            'uom_id': product.product.uom_id.id,
            'price_unit': price,
            'discount': 0.0,
            'quantity': 1,
            'account_id': accounts.get('stock_input') and accounts['stock_input'].id or \
                          accounts['expense'].id,
        }))
        if labor.labor_process_ids:
            self.env['account.invoice'].create({
                'partner_id': labor.agent.id,
                'currency_id': product.currency_id.id,
                'type': 'in_refund',
                'partner_type': labor.agent.vendor_type,
                'origin': self.name,
                'journal_id': purchase_journal.id,
                'account_id': labor.agent.property_account_payable_id.id,
                'invoice_line_ids': invoice_line,

            })
        self.state = 'rejected'
    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('labor.clearance')
        labor = self.env['labor.profile'].search([('id', '=', vals['labor_id'])])
        for rec in labor:
            line = []
            line.append((0, 0, {
                'type': 'clearance',
            }))
            rec.labor_process_ids = line
        return super(LaborClearance, self).create(vals)


