from odoo import models, fields


class CrossoveredBudgetLines(models.Model):
    _inherit = 'crossovered.budget.lines'

    budget_details_id = fields.Many2one('budget.details', string="Detalles GRP")
    partida_presupuestaria_id = fields.Many2one('idca.partida.presupuestaria', string="Partida Presupuestaria")
    fondo_id = fields.Many2one('idca.fondo', string="Fondo")
    programa_id = fields.Many2one('idca.programa', string="Programa")
    finalidad_id = fields.Many2one('idca.finalidad', string="Finalidad")
    funcion_id = fields.Many2one('idca.funcion', string="Función")
    subfuncion_id = fields.Many2one('idca.subfuncion', string="Subfunción")

    available_budget = fields.Float(string="Presupuesto disponible", compute="_compute_available_budget")

    def _compute_available_budget(self):
        for line in self:
            line.available_budget = line.planned_amount + line.practical_amount

