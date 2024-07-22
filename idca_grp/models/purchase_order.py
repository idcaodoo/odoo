import logging
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
_logger = logging.getLogger(__name__)


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    analytic_distribution = fields.Json('Analytic Distribution', widget='analytic_distribution')

    def _prepare_account_move_line(self):
        res = super(PurchaseOrderLine, self)._prepare_account_move_line()
        res['analytic_distribution'] = self.analytic_distribution
        return res

    @api.onchange("analytic_distribution", "price_subtotal")
    def onchange_analytic_distribution_on_lines(self):
        if self.analytic_distribution:
            analytic_plans = self.analytic_distribution.keys()
            plan_dict = {}
            for analytic_plan_str in analytic_plans:
                percent = self.analytic_distribution[analytic_plan_str]

                analytic_plan_ids = analytic_plan_str.split(",")
                analytic_plans_ids = self.env["account.analytic.account"].browse([int(ap) for ap in analytic_plan_ids])

                for plan in analytic_plans_ids:
                    if (plan.plan_id and
                             plan.plan_id.id != self.env.ref("idca_grp.account_analytic_plan_budget_data").id):
                        continue
                    plan_dict[plan.id] = percent

            date_order = self.date_order
            if isinstance(date_order, str):
                date_order = fields.Date.from_string(date_order)

            date_order = date_order.date()
            is_flag = False
            total_plan_amount, total_practical_amount = 0, 0
            for exp in plan_dict.keys():
                exp = self.env["account.analytic.account"].browse(exp)

                if not exp.crossovered_budget_line:
                    continue

                for line in exp.crossovered_budget_line:
                    if not line.date_from and not line.date_to:
                        total_plan_amount += line.planned_amount * plan_dict[exp.id] / 100
                        total_practical_amount += line.practical_amount
                        is_flag = True

                    if line.date_from and not line.date_to:
                        if fields.Date.from_string(line.date_from) >= date_order:

                            total_plan_amount += line.planned_amount * plan_dict[exp.id] / 100
                            total_practical_amount += line.practical_amount
                            is_flag = True

                    if line.date_from and line.date_to:
                        if fields.Date.from_string(line.date_from) <= date_order <= fields.Date.from_string(line.date_to):

                            total_plan_amount += line.planned_amount * plan_dict[exp.id] / 100
                            total_practical_amount += line.practical_amount
                            is_flag = True

            if is_flag and self.price_subtotal > total_plan_amount:
                raise ValidationError(
                    _("El monto total de la línea de compra debe ser menor o igual al monto de la distribución analítica."))

            if is_flag and total_practical_amount > total_plan_amount:
                raise ValidationError(_("El monto del presupuesto debe ser mayor que cero."))


class AccountAnalyticPlanInherit(models.Model):
    _inherit = "account.analytic.plan"

    def unlink(self):
        for record in self:
            try:
                if record.id == self.env.ref("idca_grp.account_analytic_plan_budget_data").id:
                    raise ValidationError(_("No puedes eliminar los datos predeterminados del presupuesto."))
            except Exception as exp:
                _logger.warning(exp)
                pass
        return super(AccountAnalyticPlanInherit, self).unlink()
