from typing import Dict
from odoo import api, fields, models


class PosOrderInherit(models.Model):
    _inherit = "pos.order"

    table_service_note = fields.Text(string="Table Note", compute="_compute_table_service_note", compute_sudo=True, store=True)

    @api.depends("lines", "lines.table_service_note", "table_id", "note")
    def _compute_table_service_note(self):
        for record in self:
            service_name = ""
            if record.lines:
                service_name = record.lines[0].table_service_note
            if record.note:
                service_name = record.note
            record.table_service_note = f"{service_name}"

    @api.model
    def _order_fields(self, ui_order):
        order_data = super(PosOrderInherit, self)._order_fields(ui_order)
        order_data["note"] = ui_order.get("note", "")
        order_data["table_service_note"] = ui_order.get("table_service_note", "")
        return order_data

    def _export_for_self_order(self) -> Dict:
        self.ensure_one()
        export_self_order = super(PosOrderInherit, self)._export_for_self_order()
        export_self_order["table_service_note"] = self.table_service_note
        return export_self_order


class PosOrderLineInherit(models.Model):
    _inherit = "pos.order.line"

    table_service_note = fields.Char(string="Table Note")


class PosPreparationDisplayOrder(models.Model):
    _inherit = 'pos_preparation_display.order'

    table_service_note = fields.Char(string="Table Note")

    def _export_for_ui(self, preparation_display):
        result = super(PosPreparationDisplayOrder, self)._export_for_ui(preparation_display)
        if result and result.get("tracking_number", False):
            pos_order = self.env["pos.order"].search(
                self.env["pos.order"]._search_tracking_number("ilike", result["tracking_number"]), limit=1)
            result["table_service_note"] = pos_order and pos_order.note or ""
            self.table_service_note = result["table_service_note"]
        return result


class PosPreparationDisplay(models.Model):
    _inherit = 'pos_preparation_display.display'

    table_service_note = fields.Char(string="Table Note")

    def get_preparation_display_data(self):
        result = super(PosPreparationDisplay, self).get_preparation_display_data()
        return result
