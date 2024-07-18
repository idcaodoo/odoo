from odoo import models, fields

class BudgetDetails(models.Model):
    _name = 'budget.details'
    _description = 'Budget Details'
    _rec_name = 'name'

    name = fields.Char(string="Plantilla")
    partida_presupuestaria_id = fields.Many2one('idca.partida.presupuestaria', string="Partida Presupuestaria")
    fondo_id = fields.Many2one('idca.fondo', string="Fondo")
    programa_id = fields.Many2one('idca.programa', string="Programa")
    finalidad_id = fields.Many2one('idca.finalidad', string="Finalidad")
    funcion_id = fields.Many2one('idca.funcion', string="Función")
    subfuncion_id = fields.Many2one('idca.subfuncion', string="Subfunción")
