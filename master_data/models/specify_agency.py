import base64
from datetime import date

from odoo import fields, models, api, _, tools
from odoo.exceptions import ValidationError, UserError


class SpecifyAgent(models.Model):
    _name = 'specify.agent'
    _description = 'Labourer'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char('Sequence', default='New', readonly=True)
    labor_id = fields.Many2one('labor.profile', required=True)
    user_id = fields.Many2one('res.users')
    labor_name = fields.Char()
    passport_no = fields.Char(required=True, related='labor_id.passport_no')
    religion = fields.Selection([('muslim', 'Muslim'), ('christian', 'Christian'), ('jew', 'Jew'), ('other', 'Other')],
                                'Religion')
    age = fields.Integer()
    state = fields.Selection(
        [('draft', 'CV Available'), ('available', 'Specified'), ('sent', 'CV Sent'), ('selected', 'Selected'),
         ('traveled', 'Traveled'), ('edit_after_selected', 'Edit After Selected'), ('blocked', 'Blocked')],
        default='draft',
        track_visibility="onchange")
    request_date = fields.Date(default=date.today())
    available_date = fields.Date()
    select_date = fields.Date('Selection Date')
    employer = fields.Char()
    employer_mobile = fields.Char()
    agency = fields.Many2one('res.partner', domain=[('agency', '=', True)])
    agency_short_code = fields.Char(related='agency.short_code')
    destination_city = fields.Many2one('res.country.state')
    visa_no = fields.Char()
    interpol_state = fields.Selection([('new', 'New'), ('assigned', 'Assigned'), ('rejected', 'rejected'),
                                       ('done', 'Done'), ('blocked', 'Blocked')], track_visibility="onchange")
    medical_state = fields.Selection(
        [('new', 'New'), ('pending', 'On Examination'), ('fit', 'Finished'), ('rejected', 'Rejected'),
         ('unfit', 'Unfit'), ('blocked', 'Blocked')], track_visibility="onchange")

    edit_selected = fields.Boolean(compute='compute_edit_selected')
    occupation = fields.Selection(
        [('house_maid', 'House Maid'), ('pro_maid', 'Pro Maid'), ('pro_worker', 'Pro Worker')], string='Occupation')
    _sql_constraints = [('visa_uniq', 'unique(visa_no , labor_id)', 'Visa# must be unique!'),
                        ('laborer_unique', 'unique(labor_id)', 'Created with this Laborer before!')]

    """interpol_state = fields.Char(compute='compute_interpol_state',store=True)
    big_medical_state = fields.Char(compute='compute_interpol_state',store=True)

    def compute_interpol_state(self):
        interpol = self.env['interpol.request'].search([('labor_id', '=', self.labor_id.id)])
        big_medical = self.env['big.medical'].search([('labor_id', '=', self.labor_id.id)])
        self.interpol_state = dict(interpol._fields['state'].selection).get(interpol.state)
        self.big_medical_state = dict(big_medical._fields['state'].selection).get(big_medical.state)"""

    @api.multi
    def unlock(self):
        self.state = 'edit_after_selected'

    @api.multi
    def lock(self):
        self.state = 'selected'

    @api.depends('state')
    def compute_edit_selected(self):
        if self.state == 'edit_after_selected' and self.env.user.has_group(
                'master_data.group_registeration_manager') or self.state in ('draft', 'available', 'sent'):
            self.edit_selected = True
        else:
            self.edit_selected = False

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
        labor.append(self.labor_id.id)
        attach_obj = self.env['ir.attachment']

        pdf_cv = self.env.ref('master_data.labor_cv_report_id').sudo().render_qweb_pdf([self.labor_id.id])[0]
        result_cv = base64.b64encode(pdf_cv)
        report_name = self.labor_id.name + '.pdf'
        attach_data = {
            'name': report_name,
            'datas': result_cv,
            'datas_fname': report_name,
            'res_model': 'ir.ui.view',
        }
        attachment_ids = []
        attach_id = attach_obj.create(attach_data)
        attachment_ids.append(attach_id.id)
        subject = 'New Application/ ' + self.env.user.company_id.name
        body = 'Dear ' + self.agency.name + '\n' + 'Here is in attachment a labor CV/ ' + self.name
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
                        'default_res_id': self.ids[0],
                        'default_partner_ids': l,
                        'default_body': body,
                        'default_subject': subject,
                        'default_composition_mode': 'comment',
                        'custom_layout': "mail.mail_notification_paynow",
                        'force_email': True,
                        'default_labor_ids': [(6, 0, labor)],
                        'default_attachment_ids': [(6, 0, attachment_ids)]
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
        labor.append(self.labor_id.id)
        attach_obj = self.env['ir.attachment']
        pdf_cv = self.env.ref('master_data.labor_cv_report_id').sudo().render_qweb_pdf([self.labor_id.id])[0]
        result_cv = base64.b64encode(pdf_cv)
        report_name = self.labor_id.name + '.pdf'
        attach_data = {
            'name': report_name,
            'datas': result_cv,
            'datas_fname': report_name,
            'res_model': 'ir.ui.view',
        }
        attachment_ids = []
        attach_id = attach_obj.create(attach_data)
        attachment_ids.append(attach_id.id)
        subject = 'New Application/ ' + self.env.user.company_id.name
        body = 'Dear ' + self.agency.name + '\n' + 'Here is in attachment a labor CV/ ' + self.name
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
                        'default_res_id': self.ids[0],
                        'default_partner_ids': l,
                        'default_subject': subject,
                        'default_body': body,
                        'default_composition_mode': 'comment',
                        'custom_layout': "mail.mail_notification_paynow",
                        'force_email': True,
                        'default_labor_ids': [(6, 0, labor)],
                        'default_attachment_ids': [(6, 0, attachment_ids)]
                        }
        }

    @api.multi
    def send_more_cv(self):
        view_id = self.env.ref('mail.email_compose_message_wizard_form')
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []
        attach_obj = self.env['ir.attachment']
        listrecord = []
        l = []
        labor = []
        attachment_ids = []
        body = 'Here are in attachments labors CVS '
        for record in self.env['specify.agent'].browse(active_ids):
            if not record.agency:
                raise ValidationError(_('Please, Specify agency first'))
            result = False
            listrecord.append(record.agency.id)
            if len(listrecord) > 0:
                result = all(elem == listrecord[0] for elem in listrecord)
            if not result:
                raise UserError(_('You must select same agency'))
            l.append(record.agency.id)
            body += record.name + ' , '
            pdf_cv = self.env.ref('master_data.labor_cv_report_id').sudo().render_qweb_pdf([record.labor_id.id])[0]
            result_cv = base64.b64encode(pdf_cv)
            report_name = record.labor_id.name + '.pdf'
            attach_data = {
                'name': report_name,
                'datas': result_cv,
                'datas_fname': report_name,
                'res_model': 'ir.ui.view',
            }
            attach_id = attach_obj.create(attach_data)
            attachment_ids.append(attach_id.id)
            labor.append(record.labor_id.id)
        subject = 'New Application/ ' + self.env.user.company_id.name
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
                'default_subject': subject,
                'default_partner_ids': l,
                'default_composition_mode': 'comment',
                'force_email': True,
                'default_attachment_ids': [(6, 0, attachment_ids)],
                'default_labor_ids': [(6, 0, labor)],
            }
        }

    @api.multi
    def set_to_draft(self):
        self.agency = False
        self.name = "/"
        self.state = 'draft'

    @api.multi
    def move_to_available(self):
        self.ensure_one()
        for rec in self:
            if not rec.agency:
                raise ValidationError(_('you must enter agency'))
            rec.labor_id.agency = rec.agency.id
            rec.labor_id.specify_agency = 'available'
            rec.labor_id.agency_code = rec.id
            sequence = self.env['ir.sequence'].next_by_code(rec.agency.name)
            if sequence:
                rec.name = rec.agency.short_code + '-' + sequence
            else:
                raise ValidationError('please we need agency sequence %s %s' % (rec.agency.short_code, str(sequence)))
            rec.state = 'available'
            rec.available_date = date.today()
            interpol = self.env['interpol.request'].search([('labor_id', '=', rec.labor_id.id)])
            if rec.labor_id.occupation == 'house_maid':
                training = self.env['slave.training'].search([('slave_id', '=', rec.labor_id.id)])
                if training.state == 'finished' and interpol.state == 'done':
                    print("rec labour name",rec.labor_id.name,"clearance")
                    lab_clearance = self.env['labor.clearance'].search([('labor_id','=',rec.labor_id.id)],limit=1)
                    values ={
                        'labor_id': rec.labor_id.id,
                        'labor_name': rec.labor_name,
                        'passport_no': rec.passport_no,
                        'gender': rec.labor_id.gender,
                        'job_title': rec.labor_id.occupation,
                        'contact': rec.labor_id.phone,
                        'lc1': rec.labor_id.lc1.id,
                        'lc2': rec.labor_id.lc2.id,
                        'lc3': rec.labor_id.lc3.id,
                        'district': rec.labor_id.district.id,
                        'agency': rec.agency.id,
                        'agency_code': rec.name,
                        'destination_city': rec.destination_city.id,
                    }
                    if lab_clearance:
                        print("Update")
                        print(values)
                        lab_cle = lab_clearance.write(values)
                        print(lab_cle)
                    else:
                        print("Create")
                        lab_cle_c = self.env['labor.clearance'].create(values)
                        print(lab_cle_c)
            else:
                if interpol.state == 'done':
                    lab_clearance = self.env['labor.clearance'].search([('labor_id', '=', rec.labor_id.id)], limit=1)
                    values = {
                        'labor_id': rec.labor_id.id,
                        'labor_name': rec.labor_name,
                        'passport_no': rec.passport_no,
                        'gender': rec.labor_id.gender,
                        'job_title': rec.labor_id.occupation,
                        'contact': rec.labor_id.phone,
                        'lc1': rec.labor_id.lc1.id,
                        'lc2': rec.labor_id.lc2.id,
                        'lc3': rec.labor_id.lc3.id,
                        'district': rec.labor_id.district.id,
                        'agency': rec.agency.id,
                        'agency_code': rec.name,
                        'destination_city': rec.destination_city.id,
                    }
                    if lab_clearance:
                        print("Update")
                        print(values)
                        lab_cle = lab_clearance.write(values)
                        print(lab_cle)
                    else:
                        print("Create")
                        lab_cle_c = self.env['labor.clearance'].create(values)
                        print(lab_cle_c)

    @api.multi
    def select(self):
        self.ensure_one()
        if self.state == 'selected':
            raise ValidationError(_('Done before'))
        if not self.employer:
            raise ValidationError(_('Enter employer'))
        if not self.employer_mobile:
            raise ValidationError(_('Enter employer mobile'))
        if not self.destination_city:
            raise ValidationError(_('Enter destination city'))
        if not self.visa_no:
            raise ValidationError(_('Enter visa no'))
        self.state = 'selected'
        self.select_date = date.today()
        self.labor_id.specify_agency = 'selected'
        if self.labor_id.interpol_no and self.labor_id.after_medical_check == 'fit':
            self.env['labor.enjaz.stamping'].create({
                'labor_id': self.labor_id.id,
                'labor_name': self.labor_name,
                'type': 'enjaz',
                'agency': self.agency.id,
                'agency_code': self.name,
                'employer': self.employer,
                'passport_no': self.passport_no,
                'city': self.destination_city.id,
                'visa_no': self.visa_no,
            })

    @api.model
    def create(self, vals):
        labor = self.env['labor.profile'].search([('id', '=', vals['labor_id'])])
        labor.specify_agency = 'draft'
        line = []
        line.append((0, 0, {
            'type': 'agency',

        }))
        labor.labor_process_ids = line
        return super(SpecifyAgent, self).create(vals)


class MassAgency(models.TransientModel):
    _name = 'mass.agency'
    agency = fields.Many2one('res.partner', required=True, domain=[('agency', '=', True)])

    @api.multi
    def enter_agency(self):
        if not self.agency.agency:
            raise ValidationError(_('Please, select Agency checkbox in agency'))
        view_id = self.env.ref('mail.email_compose_message_wizard_form')
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []
        attach_obj = self.env['ir.attachment']
        l = []
        labor = []
        attachment_ids = []
        body = 'Here are in attachments labors CVS '
        for record in self.env['specify.agent'].browse(active_ids):
            if record.state != 'draft':
                raise ValidationError(_('All states must be draft!'))
            record.agency = self.agency.id
            record.move_to_available()
            l.append(record.agency.id)
            body += record.name + ' , '
            pdf_cv = self.env.ref('master_data.labor_cv_report_id').sudo().render_qweb_pdf([record.labor_id.id])[0]
            result_cv = base64.b64encode(pdf_cv)
            report_name = record.labor_id.name + '.pdf'
            attach_data = {
                'name': report_name,
                'datas': result_cv,
                'datas_fname': report_name,
                'res_model': 'ir.ui.view',
            }

            attach_id = attach_obj.create(attach_data)
            attachment_ids.append(attach_id.id)
            labor.append(record.labor_id.id)
        subject = 'New Application/ ' + self.env.user.company_id.name
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
                'default_subject': subject,
                'default_partner_ids': l,
                'default_composition_mode': 'comment',
                'force_email': True,
                'default_attachment_ids': [(6, 0, attachment_ids)],
                'default_labor_ids': [(6, 0, labor)],
            }

        }


class MailComposeMessageInherit(models.TransientModel):
    _inherit = 'mail.compose.message'
    labor_ids = fields.Many2many('labor.profile')

    @api.multi
    def action_send_mail(self):
        if self.labor_ids:
            for rec in self.labor_ids:
                agency = self.env['specify.agent'].search([('labor_id', '=', rec.id)])
                labor = self.env['labor.profile'].search([('id', '=', rec.id)])
                agency.state = 'sent'
                labor.cv_sent = True
        return super(MailComposeMessageInherit, self).action_send_mail()

    @api.model
    def get_record_data(self, values):
        """ Returns a defaults-like dict with initial values for the composition
        wizard when sending an email related a previous email (parent_id) or
        a document (model, res_id). This is based on previously computed default
        values. """
        result, subject = {}, False
        if values.get('parent_id'):
            parent = self.env['mail.message'].browse(values.get('parent_id'))
            result['record_name'] = parent.record_name,
            subject = tools.ustr(parent.subject or parent.record_name or '')
            if not values.get('model'):
                result['model'] = parent.model
            if not values.get('res_id'):
                result['res_id'] = parent.res_id
            partner_ids = values.get('partner_ids', list()) + [(4, id) for id in parent.partner_ids.ids]
            if self._context.get(
                    'is_private') and parent.author_id:  # check message is private then add author also in partner list.
                partner_ids += [(4, parent.author_id.id)]
            result['partner_ids'] = partner_ids
        elif values.get('model') and values.get('res_id'):
            doc_name_get = self.env[values.get('model')].browse(values.get('res_id')).name_get()
            result['record_name'] = doc_name_get and doc_name_get[0][1] or ''
            subject = tools.ustr(result['record_name'])

        re_prefix = _('Re:')
        if subject and not (subject.startswith('Re:') or subject.startswith(re_prefix)):
            subject = "%s %s" % (re_prefix, subject)
        return result


class LaborProfile(models.Model):
    _inherit = 'labor.profile'

    specify_agency_ids = fields.One2many('specify.agent', 'labor_id')
    agency_state = fields.Selection(
        [('draft', 'CV Available'), ('available', 'Specified'), ('sent', 'CV Sent'), ('selected', 'Selected'),
         ('traveled', 'Traveled'), ('edit_after_selected', 'Edit After Selected'), ('blocked', 'Blocked')],
        compute="get_agency_state", store=True)

    @api.depends('specify_agency_ids')
    def get_agency_state(self):
        for rec in self:
            agency = self.env['specify.agent'].search([('labor_id', '=', rec.id)], limit=1)
            rec.agency_state = agency.state
