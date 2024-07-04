from odoo import models, fields

class CrossoveredBudgetLines(models.Model):
    _inherit = 'crossovered.budget.lines'

    partida_presupuestaria_id = fields.Many2one('idca.partida.presupuestaria', string="Partida Presupuestaria")
    fondo_id = fields.Many2one('idca.fondo', string="Fondo")
    programa_id = fields.Many2one('idca.programa', string="Programa")
    finalidad_id = fields.Many2one('idca.finalidad', string="Finalidad")
    funcion_id = fields.Many2one('idca.funcion', string="Función")
    subfuncion_id = fields.Many2one('idca.subfuncion', string="Subfunción")
