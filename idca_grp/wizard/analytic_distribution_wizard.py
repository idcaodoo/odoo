from odoo import api, fields, models


class AnalyticDistributionWizard(models.TransientModel):
    _name = "analytic.distribution.wizard"

    purchase_order_id = fields.Many2one("purchase.order.line", string="#Purchase Order")
    analytic_distribution_ids = fields.One2many(
        "analytic.distributor.wizard.line", "wizard_id",
        string="Analytic"
    )

    def action_confirm(self):
        self.ensure_one()
        self.purchase_order_id.write({"analytic_distribution_ids": [(5, 0)] + [
            (0, 0, {
                "name": line.name,
                "percentage": line.percentage,
                "budget": line.budget
            }) for line in self.analytic_distribution_ids]})


class AnalyticDistributorWizardLine(models.TransientModel):
    _name = "analytic.distributor.wizard.line"
    _description = "Analytic Distributor"

    name = fields.Char(string="Presupuesto disponible", required=1)
    percentage = fields.Float(string="Percentage")
    budget = fields.Float(string="#Budget")
    wizard_id = fields.Many2one("analytic.distribution.wizard", string="#WizardID")
