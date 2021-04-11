from odoo import models

class ClearanceXlsx(models.AbstractModel):
    _name = 'report.master_data.report_clearance_xlx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, lines):

        format1 = workbook.add_format({'font_size': 13,'align': 'vcenter','bold': True})
        format2 = workbook.add_format({'font_size': 11,'align': 'vcenter'})
        sheet = workbook.add_worksheet('Clearance List')
        sheet.set_column(0,0,20)
        sheet.set_column(1,1,20)
        sheet.set_column(2,2,20)
        sheet.set_column(3,3,20)
        sheet.set_column(4,4,20)
        sheet.set_column(5,5,20)
        sheet.set_column(6,6,20)
        sheet.set_column(7,7,20)
        sheet.set_column(8,8,20)
        sheet.set_column(9,9,20)
        sheet.set_column(10,10,20)

        row = 0

        sheet.write(row, 0, 'Name', format1)
        sheet.write(row, 1, 'Passport No', format1)
        sheet.write(row, 2, 'Gender', format1)
        sheet.write(row, 3, 'Job Title', format1)
        sheet.write(row, 4, 'Contact', format1)
        sheet.write(row, 5, 'LC1', format1)
        sheet.write(row, 6, 'LC2', format1)
        sheet.write(row, 7, 'LC3', format1)
        sheet.write(row, 8, 'District', format1)
        sheet.write(row, 9, 'Company', format1)
        sheet.write(row, 10, 'Destination', format1)

        for obj in lines.clearance_list:
            row = row + 1
            sheet.write(row, 0, obj.labor_id.name, format2)
            sheet.write(row, 1, obj.passport_no, format2)
            sheet.write(row, 2, obj.gender, format2)
            sheet.write(row, 3, dict(obj._fields['job_title'].selection).get(obj.job_title), format2)
            sheet.write(row, 4, obj.contact, format2)
            sheet.write(row, 5, obj.lc1.name, format2)
            sheet.write(row, 6, obj.lc2.name, format2)
            sheet.write(row, 7, obj.lc3.name, format2)
            sheet.write(row, 8, obj.district.name, format2)
            sheet.write(row, 9, obj.agency.name, format2)
            sheet.write(row, 10, obj.destination_city.name, format2)
