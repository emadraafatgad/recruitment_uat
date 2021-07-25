# -*- coding: utf-8 -*-
import base64
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo import api, SUPERUSER_ID, fields, models, _
from datetime import date
from odoo.exceptions import UserError, ValidationError


class LaborSkills(models.Model):
    _name = 'labor.skills'

    name = fields.Char(required=True)
    for_men = fields.Boolean()


class LaborSpecification(models.Model):
    _name = 'labor.specifications'
    name = fields.Char(required=True)


class LaborProfile(models.Model):
    _name = 'labor.profile'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _inherits = {
        'res.partner': 'partner_id',
    }
    _description = 'Labor Profile'
    _order = 'id desc'

    SEX = [
        ('Male', 'Male'),
        ('Female', 'Female'),
    ]

    state = fields.Selection(
        [('new', 'New'), ('editing', 'Editing'), ('confirmed', 'Confirmed'), ('block', 'Blocked'),
         ('travelled', 'Travelled'),
         ('rejected', 'Rejected')], default="new", track_visibility="onchange")
    partner_id = fields.Many2one('res.partner', string='Related Partner', required=True, ondelete='cascade',
                                 help='Partner-related data of the patient')
    age = fields.Integer(compute='_compute_slave_age', track_visibility="onchange", store=True)
    gender = fields.Selection(SEX, string='Gender', track_visibility="onchange", index=True)
    # country_id = fields.Many2one('res.country', string='Nationality')
    identification_code = fields.Char(string='Labor Code', copy=True, index=True, track_visibility="onchange",
                                      default=lambda self: _('New'),
                                      help='Labor Identifier provided by the Health Center', readonly=True)
    national_id = fields.Char(size=14, string='National ID', track_visibility="onchange")
    card_no = fields.Char()
    start_date = fields.Date('Date Of Issue', track_visibility="onchange")
    end_date = fields.Date('Date of Expiry', track_visibility="onchange")

    general_info = fields.Text(string='General Information', track_visibility="onchange",
                               help="General information about the patient")
    have_skills = fields.Boolean(track_visibility="onchange")
    skills_ids = fields.Many2one('labor.skills', track_visibility="onchange")
    occupation = fields.Selection(
        [('house_maid', 'House Maid'), ('pro_maid', 'Pro Maid'), ('pro_worker', 'Pro Worker')],
        default="house_maid", track_visibility="onchange", string='Occupation')
    salary = fields.Float(default=900, track_visibility="onchange")

    def get_default_currency(self):
        currency = self.env['res.currency'].search([('currency_subunit_label', '=', 'Halala')])
        return currency

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100):
        if args is None:
            args = []
        if name:
            actions = self.search(['|', ('name', operator, name), ('passport_no', operator, name)] + args, limit=limit)
            return actions.name_get()
        return super(LaborProfile, self)._name_search(name, args=args, operator=operator, limit=limit)

    currency = fields.Many2one('res.currency', default=get_default_currency)
    agent = fields.Many2one('res.partner', domain=[('vendor_type', '=', 'agent')], required=True)
    experience = fields.Selection([('first_time', 'First Time'), ('has_experience', 'Has Experience')],
                                  default="first_time", track_visibility="onchange", required=True)
    experience_ids = fields.One2many('prior.experience', 'laborer_id', track_visibility="onchange")
    language = fields.Many2many('res.lang', track_visibility="onchange")
    specifications = fields.Many2many('labor.specifications', track_visibility="onchange")
    height = fields.Float(track_visibility="onchange")
    weight = fields.Float(track_visibility="onchange")
    general_remarks = fields.Text(track_visibility="onchange")
    children = fields.Char(track_visibility="onchange")
    other_mob = fields.Char('Other Mob', track_visibility="onchange")
    marital_status = fields.Selection(
        [('single', 'Single'), ('married', 'Married'), ('windowed', 'Windowed'), ('divorced', 'Divorced')],
        'Marital Status')
    religion = fields.Selection([('muslim', 'Muslim'), ('christian', 'Christian'), ('jew', 'Jew'), ('other', 'Other')],
                                'Religion', track_visibility="onchange")
    children_ids = fields.One2many('children.number', 'laborer_id')
    education_certificate = fields.Selection(
        [('primary', 'Primary Education'), ('preparatory', 'Preparatory Education'),
         ('secondary', 'Secondary Education'), ('university', 'University'), ('diploma', 'Diploma'),
         ('no_education', 'No Education')], 'Educational Certificate', track_visibility="onchange")
    end_education = fields.Char('Education Remarks', track_visibility="onchange")
    no_education = fields.Char('Remarks', track_visibility="onchange")
    agent_invoice = fields.Many2one('account.invoice', track_visibility="onchange")
    register_with = fields.Selection([('national_id', 'National ID'), ('nira', 'Nira'), ('passport', 'Passport')],
                                     'Document', track_visibility="onchange")
    allow_passport_request = fields.Boolean('Allow Passport Request', track_visibility="onchange")
    lc1 = fields.Many2one('labor.village', string='Village /LC1', track_visibility="onchange")
    lc2 = fields.Many2one('labor.parish', string='Parish /LC2', track_visibility="onchange")
    lc3 = fields.Many2one('labor.subcounty', string='Sub County /LC3', track_visibility="onchange")
    lc4 = fields.Many2one('labor.county', string='County /LC4', track_visibility="onchange")
    district = fields.Many2one('labor.district', string='District', track_visibility="onchange")
    origin_lc1 = fields.Many2one('labor.village', string='Village /LC1', track_visibility="onchange")
    origin_lc2 = fields.Many2one('labor.parish', string='Parish /LC2', track_visibility="onchange")
    origin_lc3 = fields.Many2one('labor.subcounty', string='Sub County /LC3', track_visibility="onchange")
    origin_lc4 = fields.Many2one('labor.county', string='County /LC4', track_visibility="onchange")
    origin_district = fields.Many2one('labor.district', string='District', track_visibility="onchange")
    origin_tribe = fields.Many2one('labor.tribe', string='Tribe', track_visibility="onchange")
    origin_clan = fields.Many2one('labor.clan', string='Clan', track_visibility="onchange")
    origin_descendants = fields.Char(string='Descendants', track_visibility="onchange")
    interpol_no = fields.Char('Interpol No', track_visibility="onchange")
    interpol_start_date = fields.Date('Interpol Start Date', track_visibility="onchange")
    interpol_end_date = fields.Date('Interpol End Date', track_visibility="onchange")
    allow_passport = fields.Boolean('Expenses of passport', compute='passport_expense', track_visibility="onchange",
                                    store=True)
    large_image = fields.Binary(track_visibility="onchange")
    after_medical_check = fields.Selection([('fit', 'Fit'), ('unfit', 'Unfit'), ('pending', 'Pending')])
    medical_unfit_reason = fields.Char(track_visibility="onchange")
    cv_sent = fields.Boolean(track_visibility="onchange")
    agency = fields.Many2one('res.partner', track_visibility="onchange", domain=[('agency', '=', True)])
    agency_code = fields.Many2one('specify.agent', track_visibility="onchange")
    specify_agency = fields.Selection(
        [('draft', 'CV Available'), ('available', 'Specified'), ('sent', 'CV Sent'), ('selected', 'Selected')],
        track_visibility="onchange", string='Specify Agency State')
    update_id = fields.Boolean(compute='_compute_update_id')
    update_pass = fields.Boolean(compute='_compute_update_pass')

    @api.depends('state', 'register_with')
    def _compute_update_id(self):
        if self.state == 'confirmed' and self.register_with == 'nira':
            self.update_id = True
        else:
            self.update_id = False

    @api.depends('state', 'register_with')
    def _compute_update_pass(self):
        if self.state == 'confirmed' and self.register_with != 'passport':
            self.update_pass = True
        else:
            self.update_pass = False

    @api.multi
    def action_update_id_wizard(self):
        view_id = self.env.ref('master_data.labor_profile_national_id_wizard')
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []
        for record in self.env['labor.profile'].browse(active_ids):
            if len(active_ids) > 1:
                raise ValidationError(_('You cannot update national id more than one record'))
            return {
                'name': _('Passport Info'),
                'type': 'ir.actions.act_window',
                'res_model': 'labor.profile',
                'view_type': 'form',
                'view_mode': 'form',
                'view_id': view_id.id,
                'views': [(view_id.id, 'form')],
                'target': 'new',
                'res_id': record.id,
            }

    @api.multi
    def action_update_national_id(self):
        self.ensure_one()
        passport_request = self.env['nira.letter.request'].search([('labourer_id', '=', self.id)])
        for rec in passport_request:
            rec.national_id = self.national_id
            rec.end_date = self.end_date

    @api.multi
    def action_update_passport_wizard(self):
        view_id = self.env.ref('master_data.labor_profile_passport_wizard')
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []
        for record in self.env['labor.profile'].browse(active_ids):
            if len(active_ids) > 1:
                raise ValidationError(_('You cannot update passport more than one record'))
            return {
                'name': _('Passport Info'),
                'type': 'ir.actions.act_window',
                'res_model': 'labor.profile',
                'view_type': 'form',
                'view_mode': 'form',
                'view_id': view_id.id,
                'views': [(view_id.id, 'form')],
                'target': 'new',
                'res_id': record.id,
            }

    @api.multi
    def action_update_passport(self):
        passport_request = self.env['passport.request'].search([('labor_id', '=', self.id)])
        for rec in passport_request:
            rec.passport_no = self.passport_no
            rec.pass_start_date = self.pass_start_date
            rec.pass_end_date = self.pass_end_date

    @api.multi
    def create_passport_request(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []
        request_obj = self.env['passport.request']
        for record in self.env['labor.profile'].browse(active_ids):
            request = self.env['passport.request'].search([('labor_id', '=', record.id)])
            if request:
                raise ValidationError(_('there is a passport request for laborer %s') % record.name)
            request_obj.create({
                'labor_id': record.id,
                'labor_id_no_edit': record.id,
                'national_id': record.national_id,
                'religion': record.religion,
            })

    @api.multi
    def default_cv_values(self):
        view_id = self.env.ref('mail.email_compose_message_wizard_form')
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []
        attach_obj = self.env['ir.attachment']
        listrecord = []
        l = []
        labor = []
        attachment_ids = []
        body = 'Here are in attachments labors CVS '

        if any([record.specify_agency == 'draft' for record in self.env['labor.profile'].browse(active_ids)]):
            raise ValidationError(_('there are labors have no available agency!'))

        for record in self.env['labor.profile'].browse(active_ids):
            result = False
            listrecord.append(record.agency.id)
            if len(listrecord) > 0:
                result = all(elem == listrecord[0] for elem in listrecord)

            if not result:
                raise UserError(_('You must select same agency'))
            l.append(record.agency.id)

            body += record.agency_code.name + ' , '

            pdf_cv = self.env.ref('master_data.labor_cv_report_id').sudo().render_qweb_pdf([record.id])[0]
            result_cv = base64.b64encode(pdf_cv)
            report_name = record.name + '.pdf'
            attach_data = {
                'name': report_name,
                'datas': result_cv,
                'datas_fname': report_name,
                'res_model': 'ir.ui.view',
            }

            attach_id = attach_obj.create(attach_data)
            attachment_ids.append(attach_id.id)
            labor.append(record.id)
        return {
            'name': _('Send CVS'),
            'type': 'ir.actions.act_window',
            'res_model': 'mail.compose.message',
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
            'view_id': view_id.id,
            'views': [(view_id.id, 'form')],
            'context': {
                'default_model': 'specify.agent',
                'default_body': body,
                'default_subject': 'Labors CVS',
                'default_partner_ids': l,
                'default_composition_mode': 'comment',
                'force_email': True,
                'default_attachment_ids': [(6, 0, attachment_ids)],
                'default_labor_ids': [(6, 0, labor)],
            }

        }

    @api.multi
    def action_send_cv(self):
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        try:
            compose_form_id = ir_model_data.get_object_reference('mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False
        l = []
        labor = []
        l.append(self.agency.id)
        attach_obj = self.env['ir.attachment']

        pdf_cv = self.env.ref('master_data.labor_cv_report_id').sudo().render_qweb_pdf([self.id])[0]
        result_cv = base64.b64encode(pdf_cv)
        report_name = self.name + '.pdf'
        attach_data = {
            'name': report_name,
            'datas': result_cv,
            'datas_fname': report_name,
            'res_model': 'ir.ui.view',
        }
        attachment_ids = []
        attach_id = attach_obj.create(attach_data)
        attachment_ids.append(attach_id.id)
        labor.append(self.id)
        body = 'Dear ' + self.agency.name + '\n' + 'Here is in attachment a labor CV/ ' + self.agency_code.name
        return {
            'name': _('Compose Email'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': {'default_model': 'specify.agent',
                        'default_res_id': self.agency_code.ids[0],
                        'default_partner_ids': l,
                        'default_body': body,
                        'default_subject': 'Labors CVS',
                        'default_composition_mode': 'comment',
                        'custom_layout': "mail.mail_notification_paynow",
                        'force_email': True,
                        'default_attachment_ids': [(6, 0, attachment_ids)],
                        'default_labor_ids': [(6, 0, labor)],

                        }
        }

    @api.multi
    def action_resend_cv(self):
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        try:
            compose_form_id = ir_model_data.get_object_reference('mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False
        l = []
        labor = []
        l.append(self.agency.id)
        attach_obj = self.env['ir.attachment']

        pdf_cv = self.env.ref('master_data.labor_cv_report_id').sudo().render_qweb_pdf([self.id])[0]
        result_cv = base64.b64encode(pdf_cv)
        report_name = self.name + '.pdf'
        attach_data = {
            'name': report_name,
            'datas': result_cv,
            'datas_fname': report_name,
            'res_model': 'ir.ui.view',
        }
        attachment_ids = []
        attach_id = attach_obj.create(attach_data)
        attachment_ids.append(attach_id.id)
        labor.append(self.id)
        body = 'Dear ' + self.agency.name + '\n' + 'Here is in attachment a labor CV/ ' + self.agency_code.name
        return {
            'name': _('Compose Email'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': {'default_model': 'specify.agent',
                        'default_res_id': self.agency_code.ids[0],
                        'default_partner_ids': l,
                        'default_body': body,
                        'default_subject': 'Labors CVS',
                        'default_composition_mode': 'comment',
                        'custom_layout': "mail.mail_notification_paynow",
                        'force_email': True,
                        'default_attachment_ids': [(6, 0, attachment_ids)],
                        'default_labor_ids': [(6, 0, labor)],

                        }
        }

    allow_over_age = fields.Boolean(track_visibility="onchange")

    # allow_over_age = fields.Boolean()

    @api.onchange('date_of_birth')
    def _check_age(self):
        if self.date_of_birth and not self.allow_over_age:
            if self.age < 21 or self.age > 38:
                return {
                    'warning': {'title': _('Age Warning'),
                                'message': _('Age equals %s years.') % self.age}
                }

    @api.constrains('age')
    def age_const(self):
        if self.pre_medical_check == 'Fit' and not self.allow_over_age:
            if self.age < 21 or self.age > 38:
                raise ValidationError(_('Sorry, Cannot accept %s years.') % self.age)

    @api.constrains('pass_end_date')
    def _check_pass_end_date(self):
        check = (date.today() + relativedelta(years=1)).strftime('%Y-%m-%d')
        if str(self.pass_end_date) < check:
            raise ValidationError(_('Sorry, Not available passport Expiry date'))

    @api.constrains('national_id')
    def _const_national_id(self):
        if self.national_id:
            if len(self.national_id) < 14:
                raise ValidationError(_('ID must be 14!'))

    def _default_user(self):
        user = self.env.uid
        return user

    interview_by = fields.Many2one('res.users', default=_default_user, required=True, track_visibility='onchange')

    @api.multi
    def action_confirm(self):
        self.ensure_one()
        # if self.pre_medical_check == 'unfit'
        labor_confirmed = self.env['labor.profile'].search([('state', '=', 'confirmed'), ('id', '=', self.id)])
        if labor_confirmed:
            raise ValidationError(_('Confirmed before'))
        if self.occupation == 'house_maid':
            self.identification_code = self.env['ir.sequence'].next_by_code('house.maid')
            training_req = self.env['slave.training']
            training_req.create({
                'slave_id': self.id,
                'phone': self.phone,
            })
        elif self.occupation == 'pro_worker':
            self.identification_code = self.env['ir.sequence'].next_by_code('pro.worker')
        elif self.occupation == 'pro_maid':
            self.identification_code = self.env['ir.sequence'].next_by_code('pro.maid')
        if self.register_with == 'national_id':
            request_obj = self.env['passport.request']
            request_obj.create({
                'labor_id': self.id,
                'labor_id_no_edit': self.id,
                'national_id': self.national_id,
                'religion': self.religion,
            })
        if self.register_with == 'nira':
            self.request_nira()
        if self.register_with == 'passport':
            self.request_interpol()
            self.big_medical_request()
            self.specify_agency_request()
        if self.occupation == 'house_maid':
            price_total = 0.0
            price = 0.0
            name = ''
            invoice_line = []
            product = self.env['product.recruitment.config'].search([('type', '=', 'agent')], limit=1)
            if not product.journal_id:
                raise ValidationError(_('Please, you must select journal in agent from configration'))
            method = self.env['account.payment.method'].search([('payment_type', '=', 'outbound')])[0]
            accounts = product.product.product_tmpl_id.get_product_accounts()

            if self.register_with == 'national_id':
                price_total = self.agent.national_id_cost
                price = self.agent.national_id_cost * 0.5
                name = 'Agent cost document/national id ' + ',Labor/' + self.name
            elif self.register_with == 'passport':
                price_total = self.agent.passport_cost
                price = self.agent.passport_cost * 0.5
                name = 'Agent cost document/passport ' + ',Labor/' + self.name
            elif self.register_with == 'nira':
                price_total = self.agent.nira_cost
                price = self.agent.nira_cost * 0.5
                name = 'Agent cost document/nira ' + ',Labor/' + self.name
            append_labor = []
            append_labor.append(self.id)
            invoice_line.append((0, 0, {
                'product_id': product.product.id,
                'labors_id': [(6, 0, append_labor)],
                'name': name,
                'uom_id': product.product.uom_id.id,
                'price_unit': price_total,
                'discount': 0.0,
                'quantity': 1,
                'account_id': accounts.get('expense') and accounts['expense'].id or \
                              accounts['expense'].id,
            }))
            cr = self.env['account.invoice'].create({
                'partner_id': self.agent.id,
                'currency_id': product.currency_id.id,
                'state': 'draft',
                'type': 'in_invoice',
                'partner_type': self.agent.vendor_type,
                'origin': self.identification_code,
                'journal_id': product.journal_id.id,
                'account_id': self.agent.property_account_payable_id.id,
                'invoice_line_ids': invoice_line,

            })
            cr.action_invoice_open()
            self.agent_invoice = cr.id
            l = []
            l.append(self.agent_invoice.id)
            payment = self.env['account.payment'].create({
                'partner_id': self.agent.id,
                'partner_type': 'supplier',
                'payment_type': 'outbound',
                'journal_id': product.journal_id.id,
                'currency_id': product.currency_id.id,
                'payment_method_id': method.id,
                'payment': 'first',
                'communication': cr.number,
                'amount': price,
                'labor_id': self.id,
            })
            payment.invoice_ids = l
            line = []
            line.append((0, 0, {
                'type': 'agent_payment',
                'payment': 'first'

            }))
            line.append((0, 0, {
                'type': 'agent_commission',
            }))
            self.labor_process_ids = line
            self.show = True
        self.state = 'confirmed'

    @api.multi
    def action_block(self):
        self.ensure_one()
        labor_blocked = self.env['labor.profile'].search([('state', '=', 'block'), ('id', '=', self.id)])
        if labor_blocked:
            raise ValidationError(_('Blocked before'))
        training = self.env['slave.training'].search([('slave_id', '=', self.id), ('invoiced', '=', False)])
        for rec in training:
            rec.state = 'blocked'
        nira = self.env['nira.letter.request'].search([('labourer_id', '=', self.id), ('state', '!=', 'done')])
        for rec in nira:
            rec.state = 'blocked'
        passport = self.env['passport.request'].search(
            [('labor_id', '=', self.id), ('state', 'in', ('new', 'to_invoice'))])
        for rec in passport:
            rec.state = 'blocked'
        interpol = self.env['interpol.request'].search(
            [('labor_id', '=', self.id), ('state', 'in', ('new', 'assigned'))])
        for rec in interpol:
            rec.state = 'blocked'
        big_medical = self.env['big.medical'].search([('labor_id', '=', self.id), ('state', '=', 'new')])
        for rec in big_medical:
            rec.state = 'blocked'
        enjaz = self.env['labor.enjaz.stamping'].search(
            [('labor_id', '=', self.id), ('type', '=', 'enjaz'), ('state', '!=', 'done')])
        for rec in enjaz:
            rec.state = 'blocked'
        stamping = self.env['labor.enjaz.stamping'].search(
            [('labor_id', '=', self.id), ('type', '=', 'stamping'), ('state', '!=', 'done')])
        for rec in stamping:
            rec.state = 'blocked'
        clearance = self.env['labor.clearance'].search([('labor_id', '=', self.id)])
        for rec in clearance:
            rec.state = 'blocked'
        travel = self.env['travel.company'].search([('labor_id', '=', self.id), ('state', '!=', 'done')])
        for rec in travel:
            rec.state = 'blocked'
        pcr = self.env['pcr.exam'].search([('labour_id', '=', self.id)])
        for rec in pcr:
            rec.state = 'blocked'
        accommodation = self.env['labour.accommodation'].search(
            [('labour_id', '=', self.id), ('state', '!=', 'invoiced')])
        for rec in accommodation:
            rec.state = 'blocked'
        price = 0.0
        currency_id = self.env['product.recruitment.config'].search([('type', '=', "agent")]).currency_id
        process_price = 0
        for record in self.labor_process_ids:
            process_price = 0
            conf_type = self.env['product.recruitment.config'].search([('type', '=', record.type)])
            if conf_type.type == 'agency':
                continue
            if conf_type.type == 'clearance':
                continue
            if conf_type:
                proc_currency_id = conf_type.currency_id
                process_price = proc_currency_id._convert(record.total_cost, currency_id, self.env.user.company_id,
                                     fields.Date.today())
                print(conf_type.currency_id.name,"Currency Name")
                print(conf_type.type, "type Name")
                print(proc_currency_id.name, "process currency")
                print(currency_id.name, "agent currency")
                print(process_price, "process_price")
            elif record.type == "big_medical":
                conf_type = self.env['product.recruitment.config'].search([('type', '=', "hospital")])
                proc_currency_id = conf_type.currency_id
                process_price = proc_currency_id._convert(record.total_cost, currency_id, self.env.user.company_id,
                                                          fields.Date.today())
                print(conf_type.currency_id.name, "Currency Name")
                print(conf_type.type, "type Name")
                print(proc_currency_id.name, "process currency")
                print(currency_id.name, "agent currency")
                print(process_price, "process_price")
            elif record.type == "stamping":
                conf_type = self.env['product.recruitment.config'].search([('type', '=', "embassy")])
                proc_currency_id = conf_type.currency_id
                process_price = proc_currency_id._convert(record.total_cost, currency_id, self.env.user.company_id,
                                                          fields.Date.today())
                print(conf_type.currency_id.name, "Currency Name")
                print(conf_type.type, "type Name")
                print(proc_currency_id.name, "process currency")
                print(currency_id.name, "agent currency")
                print(process_price, "process_price")
            elif record.type == "agent_payment":
                conf_type = self.env['product.recruitment.config'].search([('type', '=', "agent")])
                proc_currency_id = conf_type.currency_id
                process_price = proc_currency_id._convert(record.total_cost, currency_id, self.env.user.company_id,
                                                          fields.Date.today())
                print(conf_type.currency_id.name, "Currency Name")
                print(conf_type.type, "type Name")
                print(proc_currency_id.name, "process currency")
                print(currency_id.name, "agent currency")
                print(process_price, "process_price")
            price += process_price
            print(price, "price")
        # if price:
        #     raise ValidationError((price))
        append_labor = []
        append_labor.append(self.id)
        invoice_line = []
        product = self.env['product.recruitment.config'].search([('type', '=', 'agent')])[0]
        if not product.journal_id:
            raise ValidationError(_('Please, you must select journal in agent from configration'))
        accounts = product.product.product_tmpl_id.get_product_accounts()
        invoice_line.append((0, 0, {
            'product_id': product.product.id,
            'labors_id': [(6, 0, append_labor)],
            'name': 'Block Laborer',
            'uom_id': product.product.uom_id.id,
            'price_unit': price,
            'discount': 0.0,
            'quantity': 1,
            'account_id': accounts.get('expense') and accounts['expense'].id or \
                          accounts['expense'].id,
        }))
        self.env['account.invoice'].create({
            'partner_id': self.agent.id,
            'currency_id': product.currency_id.id,
            'type': 'in_refund',
            'partner_type': self.agent.vendor_type,
            'origin': self.identification_code,
            'journal_id': product.journal_id.id,
            'account_id': self.agent.property_account_payable_id.id,
            'invoice_line_ids': invoice_line,

        })
        self.state = 'block'

    @api.multi
    def action_reject(self):
        self.ensure_one()
        labor_rejected = self.env['labor.profile'].search([('state', '=', 'rejected'), ('id', '=', self.id)])
        if labor_rejected:
            raise ValidationError(_('Rejected before'))
        append_labor = []
        append_labor.append(self.id)
        invoice_line = []
        purchase_journal = self.env['account.journal'].search([('type', '=', 'purchase')])[0]
        product = self.env['product.recruitment.config'].search([('type', '=', 'pre_medical_check')])[0]
        accounts = product.product.product_tmpl_id.get_product_accounts()
        invoice_line.append((0, 0, {
            'product_id': product.product.id,
            'labors_id': [(6, 0, append_labor)],
            'name': 'Pre Medical Check',
            'uom_id': product.product.uom_id.id,
            'price_unit': product.price,
            'discount': 0.0,
            'quantity': 1,
            'account_id': accounts.get('expense') and accounts['expense'].id or \
                          accounts['expense'].id,
        }))
        self.env['account.invoice'].create({
            'partner_id': self.agent.id,
            'currency_id': product.currency_id.id,
            'type': 'in_refund',
            'partner_type': self.agent.vendor_type,
            'origin': self.identification_code,
            'journal_id': purchase_journal.id,
            'account_id': self.agent.property_account_payable_id.id,
            'invoice_line_ids': invoice_line,

        })
        self.state = 'rejected'

    @api.multi
    def action_unlock(self):
        self.state = 'editing'

    @api.multi
    def action_lock(self):
        if self.pre_medical_check == 'unfit':
            self.state = 'rejected'
        else:
            self.state = 'confirmed'

    appear_confirm = fields.Boolean(compute='compute_confirm_button')

    @api.one
    @api.depends('state', 'pre_medical_check')
    def compute_confirm_button(self):
        if self.state == 'new' and self.pre_medical_check == 'Fit':
            self.appear_confirm = True
        else:
            self.appear_confirm = False

    appear_reject = fields.Boolean(compute='compute_reject_button')

    @api.one
    @api.depends('state', 'pre_medical_check')
    def compute_reject_button(self):
        if self.state == 'new' and self.pre_medical_check == 'Unfit':
            self.appear_reject = True
        else:
            self.appear_reject = False

    @api.onchange('pass_start_date')
    def onchange_passport_date(self):
        if self.pass_start_date:
            self.pass_end_date = (self.pass_start_date + relativedelta(years=10)).strftime('%Y-%m-%d')

    @api.onchange('national_id')
    def onchange_national_id(self):
        if self.national_id:
            if len(self.national_id) < 14:
                message = _(('ID must be 14!'))
                mess = {
                    'title': _('Warning'),
                    'message': message
                }
                return {'warning': mess}

    @api.depends('register_with', 'occupation')
    def passport_expense(self):
        for rec in self:
            if rec.occupation in ('pro_worker', 'pro_maid') and rec.register_with in ('national_id', 'nira'):
                rec.allow_passport = True
            else:
                rec.allow_passport = False

    @api.onchange('register_with')
    def _onchange_register(self):
        if self.occupation in ('pro_worker', 'pro_maid') and self.register_with in ('national_id', 'nira'):
            message = _(('%s ,must register with passport') % \
                        dict(self._fields['occupation'].selection).get(self.occupation))
            mess = {
                'title': _('Warning'),
                'message': message
            }
            return {'warning': mess}

    show = fields.Boolean()
    bill_count = fields.Integer(compute='_compute_bill', string='Bill', default=0)
    bill_ids = fields.Many2one('account.invoice', compute='_compute_bill', string='Bill', copy=False)

    def action_view_bill(self):
        action = self.env.ref('account.action_vendor_bill_template')
        result = action.read()[0]
        result.pop('id', None)
        result['context'] = {}
        b_ids = sum([line.bill_ids.ids for line in self], [])
        if len(b_ids) > 1:
            result['domain'] = "[('id','in',[" + ','.join(map(str, b_ids)) + "])]"
        elif len(b_ids) == 1:
            res = self.env.ref('account.invoice_supplier_form', False)
            result['views'] = [(res and res.id or False, 'form')]
            result['res_id'] = b_ids and b_ids[0] or False
        return result

    def _compute_bill(self):
        for line in self:
            line.bill_ids = self.agent_invoice.id
            line.bill_count = len(self.agent_invoice)

    payment_count = fields.Integer(compute='_compute_payment', string='Payment', default=0)
    payment_ids = fields.Many2many('account.payment', compute='_compute_payment', string='Payment', copy=False)

    def action_view_payment(self):
        action = self.env.ref('account.action_account_payments_payable')
        result = action.read()[0]
        result.pop('id', None)
        result['context'] = {}
        pay_ids = sum([line.payment_ids.ids for line in self], [])
        if len(pay_ids) > 1:
            result['domain'] = "[('id','in',[" + ','.join(map(str, pay_ids)) + "])]"
        elif len(pay_ids) == 1:
            res = self.env.ref('account.view_account_payment_form', False)
            result['views'] = [(res and res.id or False, 'form')]
            result['res_id'] = pay_ids and pay_ids[0] or False
        return result

    def _compute_payment(self):
        for line in self:
            payments = self.env['account.payment'].search([
                ('labor_id', '=', self.id)
            ])
            line.payment_ids = payments
            line.payment_count = len(payments)

    @api.model
    def create(self, vals):
        vals['is_slave'] = True
        vals['customer'] = True
        return super(LaborProfile, self).create(vals)

    @api.onchange('register_with')
    def _onchange_register_with(self):
        if self.register_with == 'nira':
            self.national_id = ''

    #
    # def unlink(self):
    #     for record in self:
    #         if record.state == 'confirmed':
    #             raise ValidationError(_('Sorry, Confirmed Profile.'))
    #     return super(LaborProfile, self).unlink()

    experience_ids_len = fields.Integer()

    @api.constrains('experience_ids')
    def len_experience_ids(self):
        self.experience_ids_len = len(self.experience_ids)

    @api.constrains('relative_ids', 'register_with')
    def relatives_const(self):
        l = []
        for rec in self.relative_ids:
            l.append(rec.relatives_degree)
        if len(set(l)) < 3 and self.register_with != 'passport' and self.pre_medical_check == 'Fit':
            raise ValidationError(_('You must enter all relative degrees(father,mother,next of kin)'))

    @api.constrains('relative_ids')
    def relative_ids_const(self):
        listrecord = []
        for record in self.relative_ids:
            if record.relatives_degree != 'next_of_kin':
                listrecord.append(record.national_id)
            if record.national_id and len(set(listrecord)) != len(listrecord):
                raise ValidationError(_('National id of relatives must be unique at labourer except next of kin'))

    @api.constrains('relative_ids', 'national_id')
    def labourer_relative_ids_const(self):
        listrecord = []
        for record in self.relative_ids:
            listrecord.append(record.national_id)

        if self.national_id and self.national_id in listrecord:
            raise ValidationError(_('National id of Labourer must be unique with national ids of relatives'))

    registration_date = fields.Datetime('Registration Time', readonly=True, index=True, default=fields.Datetime.now)
    date_of_birth = fields.Date("Date of Birth")
    pre_medical_check = fields.Selection([('Fit', 'Fit'),
                                          ('Unfit', 'Unfit')], default='Fit', required=True)
    reason = fields.Char()
    relative_ids = fields.One2many('labor.relatives', 'labourer_id')
    labor_process_ids = fields.One2many('labor.process', 'labor')
    vendor_type = fields.Selection([('Broker', 'Broker'), ('Tracker', 'Tracker'), ('Training', 'Training Center'),
                                    ('hospital', 'Hospital')])

    _sql_constraints = [
        ('phone_uniqe', 'unique(phone)', 'Phone must be unique!'),
        ('id_uniqe', 'unique(national_id)', 'National ID must be unique!')
        , ('passport_uniqe', 'unique(passport_no)', 'Passport No must be unique!')
    ]
    # type = fields.Selection([('pre_medical_check', 'Pre Medical Check'), ('agent', 'Agent'), ('nira', 'Nira Broker'),
    #                          ('passport', 'Passport Broker'), ('passport_placing_issue', 'Internal affairs'),
    #                          ('interpol', 'Interpol Broker'), ('gcc', 'GCC'), ('hospital', 'Big Medical'),
    #                          ('agency', 'Agency'), ('enjaz', 'Enjaz'), ('embassy', 'Stamping'),
    #                          ('travel_company', 'Travel'), ('training', 'Training'), ('lab', 'Lab'),
    #                          ('accommodation', 'Accommodation'),
    #                          ('labor_reject', 'Labor Reject')],
    #                         string='Type', track_visibility="onchange", required=True)
    # # @api.depends('labor_process_ids.state')
    # def labour_process_total_cost(self):
    #     if if


    # def labour_process_total_cost(self):
    #     for rec in self:
    #         total_cost = 0
    #         for line in rec.labor_process_ids:
    #             type = line.type
    #             type_conf = self.env['product.recruitment.config'].search([('type','=',type)])
    #             if type in ['gcc','embassy','travel_company']:
    #                 cost =
    #             elif type in ['pre_medical_check','agent','nira','passport','passport_placing_issue','interpol','hospital','enjaz',]:
    #
    #

    @api.onchange('date_of_birth')
    def _compute_slave_age(self):

        """Updates age field when birth_date is changed"""

        if self.date_of_birth:
            d1 = datetime.strptime(self.date_of_birth, "%Y-%m-%d").date()

            d2 = date.today()

            self.age = relativedelta(d2, d1).years

    @api.depends('date_of_birth')
    def _compute_slave_age(self):
        '''Method to calculate student age'''
        current_dt = date.today()
        for rec in self:
            if rec.date_of_birth:
                start = rec.date_of_birth
                age_calc = ((current_dt - start).days / 365)
                # Age should be greater than 0
                if age_calc > 0.0:
                    rec.age = age_calc

    passport_available = fields.Boolean()
    passport_no = fields.Char(track_visibility="onchange")
    pass_start_date = fields.Date("Issued Date", track_visibility="onchange")
    pass_end_date = fields.Date("Expire Date", track_visibility="onchange")
    pass_from = fields.Char('Place of Issue', track_visibility="onchange")

    id_available = fields.Boolean("ID")

    def id_is_available(self):
        self.id_available = True

    hide_request_nira = fields.Boolean('Hide Nira Request')

    def request_nira(self):
        nira = self.env['nira.letter.request']
        nira.create({
            'labourer_id': self.id,
            'name': self.name,
            'code': self.identification_code,
            'birth_date': self.date_of_birth,

        })

    def move_passport_available(self):
        self.passport_available = True
        print("Available")

    hide_request_passport = fields.Boolean('Hide Passport Request')

    def passport_request(self):
        request_obj = self.env['passport.request']
        request_obj.create({
            'labor_id': self.id,
            'labor_id_no_edit': self.id,
            'national_id': self.national_id,
            'religion': self.religion,
        })

    hide_request_interpol = fields.Boolean('Hide Interpol Request')

    def request_interpol(self):
        if self.passport_no:
            interpol = self.env['interpol.request']
            interpol.create({
                'labor_id': self.id,
                'labor': self.name,
                'national_id': self.national_id,
                'passport_no': self.passport_no,

            })
        else:
            raise UserError(_('There is no Passport No'))

    hide_request_medical = fields.Boolean('Hide Medical Request')

    def big_medical_request(self):
        if self.passport_no:
            interpol = self.env['big.medical']
            interpol.create({
                'labor_id': self.id,
                'labor': self.name,
                'national_id': self.national_id,
                'passport_no': self.passport_no,

            })
        else:
            raise UserError(_('There is no Passport No'))

    def specify_agency_request(self):
        specify_agency = self.env['specify.agent']
        specify_agency.create({
            'labor_id': self.id,
            'occupation': self.occupation,
            'labor_name': self.name,
            'passport_no': self.passport_no,
            'age': self.age,
            'religion': self.religion,
        })

    hide_request_training = fields.Boolean('Hide Training Request')

    def request_training(self):
        if self.state == 'confirmed':
            training_req = self.env['slave.training']
            training_req.create({
                'slave_id': self.id,
            })
        else:
            raise UserError(_('You must confirm record first'))
        if self.request_training:
            self.hide_request_training = True

    @api.one
    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        default = dict(default or {})
        if 'relative_ids' not in default:
            relative_ids = [(0, 0, line.copy_data()[0]) for line in
                            self.relative_ids]
        default.update({
            'name': self.name,
            'national_id': '',
            'passport_no': '',
            'stage': '',
            'pass_start_date': False,
            'pass_end_date': False,
            'agency': False,
            'agent_invoice': False,
            'identification_code': 'New',
            'phone': self.phone,
            'cv_sent': False,
            'agency_code': False,
            'specify_agency': False,
            'after_medical_check': False,
            'interpol_no': '',
            'interpol_start_date': False,
            'interpol_end_date': False,
            'relative_ids': relative_ids,

        })
        return super(LaborProfile, self).copy(default)


class Expeience(models.Model):
    _name = 'prior.experience'

    laborer_id = fields.Many2one('labor.profile')
    country_id = fields.Many2one('res.country', string='Country', required=True)

    def _get_years(self):
        current_year = datetime.today().year
        results = sorted([(str(x), str(x)) for x in range(1900, current_year + 1)], reverse=True)
        return results

    @api.depends('to_year', 'from_year')
    def compute_year_count(self):
        for rec in self:
            if rec.from_year and rec.to_year:
                rec.year_count = int(rec.to_year) - int(rec.from_year)

    from_year = fields.Selection(_get_years, 'From Year', required=True)
    to_year = fields.Selection(_get_years, 'To Year', required=True)
    year_count = fields.Integer(compute='compute_year_count')


class Children(models.Model):
    _name = 'children.number'

    laborer_id = fields.Many2one('labor.profile')
    number = fields.Char(string='#')
    age = fields.Integer(string='Age/Year')
    age_month = fields.Integer(string='Age/Month')


class LaborVillage(models.Model):
    _name = 'labor.village'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _sql_constraints = [('name_uniq', 'unique(Name)', 'Name must be unique!')]

    name = fields.Char(required=True)


class LaborParish(models.Model):
    _name = 'labor.parish'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _sql_constraints = [('name_uniq', 'unique(Name)', 'Name must be unique!')]
    name = fields.Char(required=True)


class LaborSubCounty(models.Model):
    _name = 'labor.subcounty'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _sql_constraints = [('name_uniq', 'unique(Name)', 'Name must be unique!')]
    name = fields.Char(required=True)


class LaborCounty(models.Model):
    _name = 'labor.county'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _sql_constraints = [('name_uniq', 'unique(Name)', 'Name must be unique!')]
    name = fields.Char(required=True)


class LaborDistrict(models.Model):
    _name = 'labor.district'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _sql_constraints = [('name_uniq', 'unique(Name)', 'Name must be unique!')]
    name = fields.Char(required=True)


class LaborTrip(models.Model):
    _name = 'labor.tribe'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _sql_constraints = [('name_uniq', 'unique(Name)', 'Name must be unique!')]
    name = fields.Char(required=True)


class LaborClan(models.Model):
    _name = 'labor.clan'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _sql_constraints = [('name_uniq', 'unique(Name)', 'Name must be unique!')]
    name = fields.Char(required=True)


class LaborStamping(models.Model):
    _name = 'labor.stamping'
    _description = 'LaborStamping'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Number", readonly=True, default='New')


class Laborembassy(models.Model):
    _name = 'labor.embassy'
    _description = 'Labor'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Number", readonly=True, default='New')


class embassylist(models.Model):
    _name = 'embassy.list'
    _description = 'Labor'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Number", readonly=True, default='New')


class Laborenjaz(models.Model):
    _name = 'labor.enjaz'
    _description = 'Labor'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Number", readonly=True, default='New')


class LaborRelatives(models.Model):
    _name = 'labor.relatives'

    name = fields.Char(required=True)
    relatives_degree = fields.Selection([('father', 'Father'), ('mother', 'Mother'), ('next_of_kin', 'Next Of Kin')],
                                        required=True, string='R Degrees')
    phone = fields.Char()
    national_id = fields.Char(string='ID', size=14)
    lc1 = fields.Many2one('labor.village', string='LC1')
    lc2 = fields.Many2one('labor.parish', string='LC2')
    lc3 = fields.Many2one('labor.subcounty', string='LC3')
    lc4 = fields.Many2one('labor.county', string='LC4')
    district = fields.Many2one('labor.district', string='District')
    tribe = fields.Many2one('labor.tribe')
    date_of_birth = fields.Date('DOB')
    nationality = fields.Many2one('res.country')
    note = fields.Char()
    labourer_id = fields.Many2one('labor.profile')
    age = fields.Integer(compute='_compute_relative_age', store=True)

    @api.onchange('date_of_birth')
    def _compute_relative_age(self):
        if self.date_of_birth:
            d1 = datetime.strptime(self.date_of_birth, "%Y-%m-%d").date()
            d2 = date.today()
            self.age = relativedelta(d2, d1).years

    @api.depends('date_of_birth')
    def _compute_relative_age(self):
        current_dt = date.today()
        for rec in self:
            if rec.date_of_birth:
                start = rec.date_of_birth
                age_calc = ((current_dt - start).days / 365)
                if age_calc > 0.0:
                    rec.age = age_calc

    @api.onchange('date_of_birth')
    def _check_age(self):
        if self.date_of_birth:
            if self.age < 20:
                return {
                    'warning': {'title': _('Age Warning'),
                                'message': _('Age equals %s years.') % self.age}
                }

    @api.constrains('age')
    def age_const(self):
        for rec in self:
            if rec.date_of_birth and rec.age < 20:
                raise ValidationError(_('Sorry, Cannot accept Relative %s years.') % rec.age)


class LaborProcessline(models.Model):
    _name = 'labor.process'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']

    labor = fields.Many2one('labor.profile')
    type = fields.Selection(
        [('agent_commission', 'Agent Commision'), ('agent_payment', 'Agent Payment'), ('nira', 'Nira'),
         ('passport', 'Passport'),
         ('interpol', 'Interpol'), ('big_medical', 'Big Medical'), ('agency', 'Agency'),
         ('enjaz', 'Enjaz'), ('stamping', 'Stamping'), ('clearance', 'Clearance'),
         ('travel_company', 'Travel'),
         ('training', 'Training'), ('accommodation', 'Accommodation')])
    state = fields.Char(compute='compute_state')
    payment = fields.Selection([('first', 'First'), ('last', 'Last')])
    cost = fields.Float('Paid Cost')
    total_cost = fields.Float(compute='compute_total_cost')

    @api.depends('type')
    def compute_total_cost(self):
        for record in self:
            if record.type == 'agent_payment' and record.payment == 'first':
                bill = self.env['account.payment'].search(
                    [('partner_id.vendor_type', '=', 'agent'), ('labor_id', '=', record.labor.id)])
                # record.total_cost = bill.amount
                for rec in bill:
                    record.total_cost += rec.amount
            if record.type == 'agent_payment' and record.payment == 'last':
                bill = self.env['account.payment'].search(
                    [('partner_id.vendor_type', '=', 'agent'), ('labor_id', '=', record.labor.id)])
                for rec in bill:
                    record.total_cost += rec.amount
                # record.total_cost = bill.amount
            if record.type == 'agent_commission':
                record.total_cost = record.labor.agent_invoice.amount_total

            if record.type == 'training':
                bill = self.env['account.invoice.line'].search(
                    [('partner_id.vendor_type', '=', 'training'), ('invoice_type', '=', 'in_invoice'),
                     ('accommodation', '=', False)])
                for rec in bill:
                    if record.labor in rec.labors_id:
                        record.total_cost += rec.price_unit
            if record.type == 'accommodation':
                bill = self.env['account.invoice.line'].search(
                    [('partner_id.vendor_type', '=', 'training'), ('invoice_type', '=', 'in_invoice'),
                     ('accommodation', '=', True)])
                for rec in bill:
                    if record.labor in rec.labors_id:
                        record.total_cost += rec.price_subtotal
            if record.type == 'nira':
                bill = self.env['account.invoice.line'].search(
                    [('partner_id.vendor_type', '=', 'nira_broker'), ('invoice_type', '=', 'in_invoice')])
                for rec in bill:
                    if record.labor in rec.labors_id:
                        record.total_cost = rec.price_unit

            if record.type == 'passport':
                bill = self.env['account.invoice.line'].search(
                    [('partner_id.vendor_type', '=', 'passport_broker'), ('invoice_type', '=', 'in_invoice')])
                bill2 = self.env['account.invoice.line'].search(
                    [('partner_id.vendor_type', '=', 'passport_placing_issue'), ('invoice_type', '=', 'in_invoice')])
                for rec in bill:
                    if record.labor in rec.labors_id:
                        record.total_cost += rec.price_unit
                for rec in bill2:
                    if record.labor in rec.labors_id:
                        record.total_cost += rec.price_unit
            if record.type == 'interpol':
                bill = self.env['account.invoice.line'].search(
                    [('partner_id.vendor_type', '=', 'interpol_broker'), ('invoice_type', '=', 'in_invoice')])
                for rec in bill:
                    if record.labor in rec.labors_id:
                        record.total_cost = rec.price_unit
            if record.type == 'big_medical':
                bill = self.env['account.invoice.line'].search(
                    [('partner_id.vendor_type', '=', 'hospital'), ('invoice_type', '=', 'in_invoice')])
                bill2 = self.env['account.invoice.line'].search(
                    [('partner_id.vendor_type', '=', 'gcc'), ('invoice_type', '=', 'in_invoice')])
                for rec in bill:
                    if record.labor in rec.labors_id:
                        record.total_cost += rec.price_unit
                for rec in bill2:
                    if record.labor in rec.labors_id:
                        record.total_cost += rec.price_unit

            if record.type == 'enjaz':
                bill = self.env['account.invoice.line'].search(
                    [('partner_id.vendor_type', '=', 'enjaz'), ('invoice_type', '=', 'in_invoice')])
                for rec in bill:
                    if record.labor in rec.labors_id:
                        record.total_cost += rec.price_unit
            if record.type == 'stamping':
                bill = self.env['account.invoice.line'].search(
                    [('partner_id.vendor_type', '=', 'embassy'), ('invoice_type', '=', 'in_invoice')])
                for rec in bill:
                    if record.labor in rec.labors_id:
                        record.total_cost += rec.price_unit
            if record.type == 'travel_company':
                bill = self.env['account.invoice.line'].search(
                    [('partner_id.vendor_type', '=', 'travel_company'), ('invoice_type', '=', 'in_invoice')])
                for rec in bill:
                    if record.labor in rec.labors_id:
                        record.total_cost += rec.price_unit

    @api.one
    @api.depends('type')
    def compute_state(self):

        if self.type == 'agent_payment' and self.payment == 'first':
            first_payment = self.env['account.payment'].search(
                [('labor_id', '=', self.labor.id), ('payment', '=', 'first')])
            self.state = dict(first_payment._fields['state'].selection).get(first_payment.state)
        if self.type == 'agent_payment' and self.payment == 'last':
            last_payment = self.env['account.payment'].search(
                [('labor_id', '=', self.labor.id), ('payment', '=', 'last')])
            self.state = dict(last_payment._fields['state'].selection).get(last_payment.state)
        if self.type == 'agent_commission':
            self.state = dict(self.labor.agent_invoice._fields['state'].selection).get(self.labor.agent_invoice.state)
        if self.type == 'training':
            training = self.env['slave.training'].search([('slave_id', '=', self.labor.id)])
            self.state = dict(training._fields['state'].selection).get(training.state)
        if self.type == 'nira':
            nira = self.env['nira.letter.request'].search([('labourer_id', '=', self.labor.id)])
            self.state = dict(nira._fields['state'].selection).get(nira.state)
        if self.type == 'passport':
            passport = self.env['passport.request'].search([('labor_id', '=', self.labor.id)])
            self.state = dict(passport._fields['state'].selection).get(passport.state)
        if self.type == 'interpol':
            interpol = self.env['interpol.request'].search([('labor_id', '=', self.labor.id)])
            self.state = dict(interpol._fields['state'].selection).get(interpol.state)
        if self.type == 'big_medical':
            big_medical = self.env['big.medical'].search([('labor_id', '=', self.labor.id)])
            self.state = dict(big_medical._fields['state'].selection).get(big_medical.state)
        if self.type == 'agency':
            agency = self.env['specify.agent'].search([('labor_id', '=', self.labor.id)])
            self.state = dict(agency._fields['state'].selection).get(agency.state)
        if self.type == 'enjaz':
            enjaz = self.env['labor.enjaz.stamping'].search([('labor_id', '=', self.labor.id), ('type', '=', 'enjaz')])
            self.state = dict(enjaz._fields['state'].selection).get(enjaz.state)
        if self.type == 'stamping':
            stamping = self.env['labor.enjaz.stamping'].search(
                [('labor_id', '=', self.labor.id), ('type', '=', 'stamping')])
            self.state = dict(stamping._fields['state'].selection).get(stamping.state)
        if self.type == 'clearance':
            clearance = self.env['labor.clearance'].search([('labor_id', '=', self.labor.id)])
            self.state = dict(clearance._fields['state'].selection).get(clearance.state)
        if self.type == 'travel_company':
            travel_company = self.env['travel.company'].search([('labor_id', '=', self.labor.id)])
            self.state = dict(travel_company._fields['state'].selection).get(travel_company.state)


class AgentPayment(models.Model):
    _inherit = 'account.payment'
    labor_id = fields.Many2one('labor.profile', readonly=True)
    payment = fields.Selection([('first', 'First'), ('last', 'Last')], readonly=True)
    vendor_type = fields.Selection(
        [('agent', 'Agent'), ('nira_broker', 'Nira Broker'), ('passport_broker', 'Passport Broker'),
         ('passport_placing_issue', 'Passport Placing Issue'), ('interpol_broker', 'Interpol Broker'), ('gcc', 'Gcc'),
         ('hospital', 'Hospital'), ('embassy', 'Embassy'), ('travel_company', 'Travel Company'),
         ('training', 'Training Center')], related='partner_id.vendor_type')

    @api.depends('invoice_ids')
    @api.onchange('invoice_ids')
    def _default_journal_id(self):
        if self.invoice_ids:
            self.journal_id = self.invoice_ids.journal_id

    @api.multi
    def post(self):
        for rec in self:
            if rec.labor_id and rec.partner_id.vendor_type == 'agent' and rec.payment == 'first':
                labor = self.env['labor.process'].search(
                    [('labor', '=', rec.labor_id.id), ('type', '=', 'agent_payment'), ('payment', '=', 'first')])
                labor.cost += rec.amount
            if rec.labor_id and rec.partner_id.vendor_type == 'agent' and rec.payment == 'last':
                labor = self.env['labor.process'].search(
                    [('labor', '=', rec.labor_id.id), ('type', '=', 'agent_payment'), ('payment', '=', 'last')])
                labor.cost += rec.amount

        return super(AgentPayment, self).post()


class SalaryCurrency(models.Model):
    _inherit = 'res.currency'

    @api.multi
    def name_get(self):
        res = []
        for rec in self:
            res.append((rec.id, '%s' % (rec.symbol)))
        return res

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100):
        if args is None:
            args = []
        if name:
            actions = self.search(['|', ('name', operator, name), ('symbol', operator, name)] + args, limit=limit)
            return actions.name_get()
        return super(SalaryCurrency, self)._name_search(name, args=args, operator=operator, limit=limit)


class PaymentRequest(models.Model):
    _name = 'payment.request'
    _description = 'Payment Request'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Number", readonly=True, default='New')
