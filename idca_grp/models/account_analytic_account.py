import logging
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
_logger = logging.getLogger(__name__)


class AccountAnalyticAccount(models.Model):
    _inherit = 'account.analytic.account'

    available_budget = fields.Float(string="Presupuesto disponible", compute="_compute_available_budget")

    def _compute_available_budget(self):
        for line in self:
            line.available_budget = line.planned_amount + line.practical_amount