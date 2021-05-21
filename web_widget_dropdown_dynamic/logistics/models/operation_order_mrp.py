from odoo import models, fields, api,_
from odoo.exceptions import ValidationError


class OperationOrderMRPPlan(models.Model):
     _name = 'operation.order.mrp'
     _inherit = ['operation.order', 'portal.mixin', 'mail.thread', 'mail.activity.mixin']
     _description = 'Order Manufacturing'
     _rec_name = 'code'

     _sql_constraints = [('order_no_uniq', 'unique (order_no)', 'Order no must be unique !')]

     code = fields.Char(default='New')
     order_no = fields.Many2one('operation.order',string='Origin')
     state = fields.Selection([('new', 'New'), ('confirmed', 'Confirmed')], default='new', track_visibility="onchange")
     plan_lines = fields.One2many('order.mrp.line','plan_id')

     @api.multi
     def action_confirm(self):
          if not self.plan_lines:
               raise ValidationError(_('You must enter lines.'))
          bom_line=[]
          for line in self.plan_lines:
               if line.product_qty <= 0:
                    raise ValidationError(_('Qty of lines must be bigger than zero.'))
               bom_line.append((0, 0, {
                    'product_id': line.product_id.id,
                    'product_qty': line.product_qty,
                    'product_uom_id': line.product_uom.id,

               }))
          bom = self.env['mrp.bom'].create({
               'product_tmpl_id': self.product.id,
               'product_uom_id': self.product.uom_id.id,
               'product_qty': self.total_weight,
               'plan_id': self.id,
               'type': 'normal',
               'bom_line_ids': bom_line,
               })
          self.env['mrp.production'].create({
               'bom_id': bom.id,
               'product_id': self.product.id,
               'product_qty': bom.product_qty,
               'product_uom_id': self.product.uom_id.id,
               })
          self.state = 'confirmed'

     @api.multi
     def unlink(self):
          for rec in self:
               if rec.contract_no:
                    raise ValidationError(_('You cannot delete %s as it comes from contract') % rec.name)
               if rec.state != 'new':
                    raise ValidationError(_('You cannot delete %s as it is confirmed') % rec.name)

          return super(OperationOrderMRPPlan, self).unlink()

     @api.model
     def create(self, vals):
          vals['code'] = self.env['ir.sequence'].next_by_code('operation.order.mrp')
          return super(OperationOrderMRPPlan, self).create(vals)


class MRPPlanLine(models.Model):
     _name = 'order.mrp.line'

     plan_id = fields.Many2one('operation.order.mrp')
     product_id = fields.Many2one('product.product')
     product_qty = fields.Float()
     product_uom = fields.Many2one('uom.uom',related='product_id.uom_po_id' ,string='Product Uom')


class MRPBomInherit(models.Model):
     _inherit =  'mrp.bom'
     plan_id = fields.Many2one('operation.order.mrp',string='Order Plan',readonly=True)