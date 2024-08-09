import logging
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
_logger = logging.getLogger(__name__)


class AccountAnalyticAccount(models.Model):
    _inherit = 'account.analytic.account'

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