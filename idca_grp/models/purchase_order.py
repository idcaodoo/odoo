from odoo import models, fields

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    analytic_distribution = fields.Json('Analytic Distribution', widget='analytic_distribution')

    def _prepare_account_move_line(self):
        res = super(PurchaseOrderLine, self)._prepare_account_move_line()
        res['analytic_distribution'] = self.analytic_distribution
        return res