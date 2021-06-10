import time
from odoo import api, fields, models
from odoo import api, models, _


class ReportOverdue(models.AbstractModel):
    _inherit = 'report.account.report_overdue'

    
    @api.model
    def get_report_values(self, docids, data=None):
        totals = {}
        
        res = self.env['res.partner'].browse(docids[0])
        
        lines = self._get_account_move_lines(docids)
        lines_to_display = {}
        partner_dic = {'0-30':res.first_thirty_day,'30-60':res.thirty_sixty_days,
                        '60-90':res.sixty_ninty_days,'90+':res.ninty_plus_days,'total':res.total}
        company_currency = self.env.user.company_id.currency_id
        for partner_id in docids:
            lines_to_display[partner_id] = {}
            totals[partner_id] = {}
            for line_tmp in lines[partner_id]:
                line = line_tmp.copy()
                currency = line['currency_id'] and self.env['res.currency'].browse(line['currency_id']) or company_currency
                if currency not in lines_to_display[partner_id]:
                    lines_to_display[partner_id][currency] = []
                    totals[partner_id][currency] = dict((fn, 0.0) for fn in ['due', 'paid', 'mat', 'total'])
                if line['debit'] and line['currency_id']:
                    line['debit'] = line['amount_currency']
                if line['credit'] and line['currency_id']:
                    line['credit'] = line['amount_currency']
                if line['mat'] and line['currency_id']:
                    line['mat'] = line['amount_currency']
                lines_to_display[partner_id][currency].append(line)
                if not line['blocked']:
                    totals[partner_id][currency]['due'] += line['debit']
                    totals[partner_id][currency]['paid'] += line['credit']
                    totals[partner_id][currency]['mat'] += line['mat']
                    totals[partner_id][currency]['total'] += line['debit'] - line['credit']
        return {
            'doc_ids': docids,
            'doc_model': 'res.partner',
            'partner_dic' : partner_dic,
            'docs': self.env['res.partner'].browse(docids),
            'time': time,
            'Lines': lines_to_display,
            'Totals': totals,
            'Date': fields.date.today(),
        }
