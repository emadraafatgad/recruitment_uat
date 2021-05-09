
from odoo.tools.misc import xlwt
import io
import base64
from odoo import api, fields, models, _

class RecruitmentReport(models.TransientModel):
    _name = 'recruitment.report'

    report_file = fields.Binary('Recruitment Report')
    file_name = fields.Char('File Name')
    printed = fields.Boolean()
    choose = fields.Selection([
        ('passport', 'Passport'), ('big_medical', 'Big Medical'),('travel_company', 'Travel Company')], default='passport', string='Choose', store=True)

    @api.multi
    def print_report(self):
        workbook = xlwt.Workbook()
        worksheet = workbook.add_sheet('Report')
        column_heading_style = xlwt.easyxf('font:height 200;font:bold True;')
        row = 2
        for wizard in self:
            report_head = dict(wizard._fields['choose'].selection).get(wizard.choose)+' Report'
            worksheet.write_merge(0, 0, 0, 2, report_head, xlwt.easyxf(
                'font:height 300; align: vertical center; align: horiz center;pattern: pattern solid, fore_color black; font: color white; font:bold True;' "borders: top thin,bottom thin"))
            worksheet.col(0).width = 5000
            worksheet.col(1).width = 5000
            worksheet.col(2).width = 5000
            worksheet.col(3).width = 5000
            worksheet.col(4).width = 5000
            worksheet.col(5).width = 5000
            worksheet.col(6).width = 5000
            worksheet.col(7).width = 5000
            worksheet.row(0).height = 500

            if self.choose == 'passport':
                worksheet.write(1, 0, _('Name'), column_heading_style)
                worksheet.write(1, 1, _('Personal Mobile'), column_heading_style)
                worksheet.write(1, 2, _('Other Mobile'), column_heading_style)
                worksheet.write(1, 3, _('Father Mobile'), column_heading_style)
                worksheet.write(1, 4, _('Mother Mobile'), column_heading_style)
                worksheet.write(1, 5, _('Next Of Kin Mobile'), column_heading_style)
                worksheet.write(1, 6, _('Agent'), column_heading_style)
                worksheet.write(1, 7, _('Agent Mobile'), column_heading_style)
                passport = self.env['passport.request'].search([('state', '=', 'new')])
                for rec in passport:
                    father = ''
                    mother = ''
                    next_of_kin = ''
                    for line in rec.labor_id.relative_ids:
                        if line.relatives_degree == 'father':
                            father = line.phone
                        if line.relatives_degree == 'mother':
                            mother = line.phone
                        if line.relatives_degree == 'next_of_kin':
                            next_of_kin = line.phone

                    worksheet.write(row, 0, rec.labor_id.name)
                    worksheet.write(row, 1, rec.labor_id.phone)
                    worksheet.write(row, 2, rec.labor_id.other_mob)
                    worksheet.write(row, 3, father)
                    worksheet.write(row, 4, mother)
                    worksheet.write(row, 5, next_of_kin)
                    worksheet.write(row, 6, rec.labor_id.agent.name)
                    worksheet.write(row, 7, rec.labor_id.agent.mobile)
                    row += 1

            if self.choose == 'big_medical':

                worksheet.write(1, 0, _('Name'), column_heading_style)
                worksheet.write(1, 1, _('Agent'), column_heading_style)
                worksheet.write(1, 2, _('Other Mobile'), column_heading_style)
                worksheet.write(1, 3, _('Father Mobile'), column_heading_style)
                worksheet.write(1, 4, _('Mother Mobile'), column_heading_style)
                worksheet.write(1, 5, _('Next Of Kin Mobile'), column_heading_style)
                worksheet.write(1, 6, _('Agent'), column_heading_style)
                worksheet.write(1, 7, _('Agent Mobile'), column_heading_style)
                big_medical = self.env['big.medical'].search([('state', '=', 'new')])
                for rec in big_medical:
                    father = ''
                    mother = ''
                    next_of_kin = ''
                    for line in rec.labor_id.relative_ids:
                        if line.relatives_degree == 'father':
                            father = line.phone
                        if line.relatives_degree == 'mother':
                            mother = line.phone
                        if line.relatives_degree == 'next_of_kin':
                            next_of_kin = line.phone
                    worksheet.write(row, 0, rec.labor_id.name)
                    worksheet.write(row, 1, rec.labor_id.phone)
                    worksheet.write(row, 2, rec.labor_id.other_mob)
                    worksheet.write(row, 3, father)
                    worksheet.write(row, 4, mother)
                    worksheet.write(row, 5, next_of_kin)
                    worksheet.write(row, 6, rec.labor_id.agent.name)
                    worksheet.write(row, 7, rec.labor_id.agent.mobile)
                    row += 1

            if self.choose == 'travel_company':
                worksheet.write(1, 0, _('Name'), column_heading_style)
                worksheet.write(1, 1, _('Agent'), column_heading_style)
                worksheet.write(1, 2, _('Other Mobile'), column_heading_style)
                worksheet.write(1, 3, _('Father Mobile'), column_heading_style)
                worksheet.write(1, 4, _('Mother Mobile'), column_heading_style)
                worksheet.write(1, 5, _('Next Of Kin Mobile'), column_heading_style)
                worksheet.write(1, 6, _('Agent'), column_heading_style)
                worksheet.write(1, 7, _('Agent Mobile'), column_heading_style)
                travel_company = self.env['travel.company'].search([('state', '=', 'new')])
                for rec in travel_company:
                    father = ''
                    mother = ''
                    next_of_kin = ''
                    for line in rec.labor_id.relative_ids:
                        if line.relatives_degree == 'father':
                            father = line.phone
                        if line.relatives_degree == 'mother':
                            mother = line.phone
                        if line.relatives_degree == 'next_of_kin':
                            next_of_kin = line.phone

                    worksheet.write(row, 0, rec.labor_id.name)
                    worksheet.write(row, 1, rec.labor_id.phone)
                    worksheet.write(row, 2, rec.labor_id.other_mob)
                    worksheet.write(row, 3, father)
                    worksheet.write(row, 4, mother)
                    worksheet.write(row, 5, next_of_kin)
                    worksheet.write(row, 6, rec.labor_id.agent.name)
                    worksheet.write(row, 7, rec.labor_id.agent.mobile)
                    row += 1

            fp = io.BytesIO()
            workbook.save(fp)
            excel_file = base64.encodestring(fp.getvalue())
            wizard.report_file = excel_file
            wizard.file_name = dict(wizard._fields['choose'].selection).get(wizard.choose)+' Report.xls'
            wizard.printed = True
            fp.close()
            return {
                'view_mode': 'form',
                'res_id': wizard.id,
                'res_model': 'recruitment.report',
                'view_type': 'form',
                'type': 'ir.actions.act_window',
                'context': self.env.context,
                'target': 'new',
            }












