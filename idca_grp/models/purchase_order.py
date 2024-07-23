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

    def get_all_plan_budget_from_json(self, analytic_plans, analytic_distribution, analytic_account_obj) -> dict:
        plan_dict = {}
        for analytic_plan_str in analytic_plans:
            percent = analytic_distribution[analytic_plan_str]
            analytic_plan_ids = analytic_plan_str.split(",")
            analytic_plans_ids = analytic_account_obj.browse([int(ap) for ap in analytic_plan_ids])
            for plan in analytic_plans_ids:
                if (plan.plan_id and
                        plan.plan_id.id != self.env.ref("idca_grp.account_analytic_plan_budget_data").id):
                    continue
                plan_dict[plan.id] = percent
        return plan_dict

    @staticmethod
    def get_analytic_plan_total_amount_and_name(plan_dict, date_order, analytic_account_obj):
        analytic_distribution_ls, analytic_distribution_less_ls = [], []
        total_plan_amount, total_practical_amount = 0, 0
        is_flag, is_less = False, False
        for exp in plan_dict.keys():
            exp = analytic_account_obj.browse(exp)
            if not exp.crossovered_budget_line:
                continue

            for line in exp.crossovered_budget_line:
                if not line.date_from and not line.date_to:
                    total_plan_amount += line.available_budget * plan_dict[exp.id] / 100
                    total_practical_amount += line.practical_amount
                    analytic_distribution_ls.append(exp.name)
                    is_flag = True

                    if line.practical_amount > line.available_budget:
                        analytic_distribution_less_ls.append(exp)
                        is_less = True

                if line.date_from and not line.date_to:
                    if fields.Date.from_string(line.date_from) >= date_order:
                        total_plan_amount += line.available_budget * plan_dict[exp.id] / 100
                        total_practical_amount += line.practical_amount
                        analytic_distribution_ls.append(exp.name)
                        is_flag = True

                        if line.practical_amount > line.available_budget:
                            analytic_distribution_less_ls.append(exp)
                            is_less = True

                if line.date_from and line.date_to:
                    if fields.Date.from_string(line.date_from) <= date_order <= fields.Date.from_string(line.date_to):
                        total_plan_amount += line.available_budget * plan_dict[exp.id] / 100
                        total_practical_amount += line.practical_amount
                        analytic_distribution_ls.append(exp.name)
                        is_flag = True

                        if line.practical_amount > line.available_budget:
                            analytic_distribution_less_ls.append(exp)
                            is_less = True

        analytic_distribution_str = analytic_distribution_ls and "\n".join(analytic_distribution_ls) or ""
        analytic_distribution_less_str = analytic_distribution_less_ls and "\n".join(analytic_distribution_less_ls) or ""
        return (is_flag, is_less, total_plan_amount, total_practical_amount,
                analytic_distribution_str, analytic_distribution_less_str)

    @api.constrains("analytic_distribution", "price_subtotal")
    def _validate_analytic_distribution_on_lines(self):
        """action will be called when create and edit"""
        analytic_account_obj = self.env["account.analytic.account"]
        for record in self:
            if record.analytic_distribution:
                analytic_plans = record.analytic_distribution.keys()
                plan_dict = self.get_all_plan_budget_from_json(analytic_plans, record.analytic_distribution, analytic_account_obj)
                # Modify date_order if is str
                date_order = record.date_order
                if isinstance(date_order, str):
                    date_order = fields.Date.from_string(date_order)

                date_order = date_order.date()
                (is_flag, is_less, total_plan_amount, total_practical_amount,
                 analytic_distribution_str, analytic_distribution_less_str) = self.get_analytic_plan_total_amount_and_name(plan_dict, date_order, analytic_account_obj)

                if is_flag and record.price_subtotal > total_plan_amount:
                    raise ValidationError(
                        _("El monto total de la línea de compra debe ser menor o igual al monto de la distribución analítica."
                          "\nDetalles: \n%s" % analytic_distribution_str))

                if is_less:
                    raise ValidationError(
                        _("El monto del presupuesto debe ser mayor que cero.\nDetalles: \n%s" % analytic_distribution_less_str))

    @api.onchange("analytic_distribution", "price_subtotal")
    def onchange_analytic_distribution_on_lines(self):
        """ action will be called when change data on lines"""
        if self.analytic_distribution:
            analytic_plans = self.analytic_distribution.keys()
            analytic_account_obj = self.env["account.analytic.account"]
            plan_dict = self.get_all_plan_budget_from_json(analytic_plans, self.analytic_distribution, analytic_account_obj)
            # Modify date_order if is str
            date_order = self.date_order
            if isinstance(date_order, str):
                date_order = fields.Date.from_string(date_order)

            date_order = date_order.date()
            (is_flag, is_less, total_plan_amount, total_practical_amount,
             analytic_distribution_str, analytic_distribution_less_str) = self.get_analytic_plan_total_amount_and_name(
                plan_dict, date_order, analytic_account_obj)

            if is_flag and self.price_subtotal > total_plan_amount:
                raise ValidationError(
                    _("El monto total de la línea de compra debe ser menor o igual al monto de la distribución analítica."
                      "\nDetalles: \n%s" % analytic_distribution_str))

            if is_less:
                raise ValidationError(
                    _("El monto del presupuesto debe ser mayor que cero.\nDetalles: \n%s" % analytic_distribution_less_str))


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
