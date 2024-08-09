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

    budget_account_analytic = fields.Char(string="Budget Account Analytic", compute="_compute_budget_account_analytic")

    def _compute_budget_account_analytic(self):
        for record in self:
            if record.budget_details_id and record.analytic_account_id:
                record.budget_account_analytic = f"{record.budget_details_id.name} - {record.analytic_account_id.name}"
            else:
                record.budget_account_analytic = ''


    importe_comprometido = fields.Float(string="Importe comprometido", compute="_compute_importe_comprometido")
    importe_devengado = fields.Float(string="Importe devengado", compute="_compute_importe_devengado")
    available_budget = fields.Float(string="Presupuesto disponible", compute="_compute_available_budget")

    def _compute_available_budget(self):
        for line in self:
            line.available_budget = line.planned_amount + line.practical_amount




    #Check for importe_comprometido
    def _compute_importe_comprometido(self):
        for line in self:
            if line.analytic_account_id:
                purchase_lines = self.env['purchase.order.line'].search([
                    ('order_id.state', '=', 'draft'),
                    ('analytic_distribution', 'ilike', line.analytic_account_id.id)
                ])
                line.importe_comprometido = sum(purchase_lines.mapped('price_total'))
            else:
                line.importe_comprometido = 0.0


    #Check for importe_devengado
    def _compute_importe_devengado(self):
        for line in self:
            if line.analytic_account_id:
                purchase_lines = self.env['purchase.order.line'].search([
                    ('order_id.state', '=', 'purchase'),
                    ('analytic_distribution', 'ilike', line.analytic_account_id.id)
                ])
                line.importe_devengado = sum(purchase_lines.mapped('price_total'))
            else:
                line.importe_devengado = 0.0

