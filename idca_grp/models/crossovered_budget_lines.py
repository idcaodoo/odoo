from odoo import models, fields

class CrossoveredBudgetLines(models.Model):
    _inherit = 'crossovered.budget.lines'

    
    budget_details_id = fields.Many2one('budget.details', string="Detalles GRP")

    available_budget = fields.Float(string="Presupuesto disponible", compute="_compute_available_budget")

    def _compute_available_budget(self):
        for line in self:
            line.available_budget = line.planned_amount + line.practical_amount