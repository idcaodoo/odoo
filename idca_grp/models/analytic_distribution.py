from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class AnalyticDistributor(models.Model):
    _name = "analytic.distributor"
    _description = "Analytic Distributor"

    name = fields.Char(string="Presupuesto disponible", required=1)
    percentage = fields.Float(string="Percentage")
    budget = fields.Float(string="#Budget")
    purchase_order_line_id = fields.Many2one("purchase.order.line", string="#Purchase Order Line")

    @api.constrains("budget")
    def _validate_budget_value(self):
        for record in self:
            if record.budget < 0:
                raise ValidationError(_("Sorry, the budget must greater than or equal zero!"))
