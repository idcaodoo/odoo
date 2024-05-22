import logging
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)
POSITION_P = 162
POSITION_V = 230
MAX_TABLE_LINE = 6


class RestaurantTableInherit(models.Model):
    _inherit = "restaurant.table"

    @api.model
    def create_active_table_from_floor(self, floor_id):
        create_values = {
            "seats": 2,
            "floor_id": floor_id,
            "width": 100.00,
            "height": 100.00,
            "color": "#35D374",
            "shape": "square"
        }
        other_tables = self.env["restaurant.table"].search([("floor_id", "=", floor_id)], order="id desc")
        if not other_tables:
            create_values.update({
                "name": "PL1",
                "position_h": 50.00,
                "position_v": 50.00,
            })
        else:
            total_tables = len(other_tables) or 1
            lines = (total_tables // MAX_TABLE_LINE) + 1
            position_h = 50.00 + (POSITION_P * (total_tables - ((lines - 1) * MAX_TABLE_LINE)))
            position_v = 50.00 + (POSITION_V * (lines - 1))
            create_values.update({
                "name": "PL%s" % (total_tables + 1),
                "position_h": position_h,
                "position_v": position_v
            })
        table_id = self.env["restaurant.table"].create(create_values)
        floor = self.env["restaurant.floor"].browse(floor_id)
        create_values.update({
            "floor_id": [floor_id, floor.name or ""],
            "floor": {
                "background_color": floor.background_color,
                "changes_count": 0,
                "id": floor.id,
                "name": floor.name,
                "sequence": floor.sequence,
                "table_ids": floor.table_ids.ids,
                "tables": [{
                    "active": table.active,
                    "changes_count": 0,
                    "color": table.color,
                    "height": table.height,
                    "width": table.width,
                    "id": table.id,
                    "name": table.name,
                    "order_count": 0 if table.id == table_id.id else 1,
                    "position_h": table.position_h,
                    "position_v": table.position_v,
                    "seats": table.seats,
                    "shape": table.shape,
                    "skip_changes": 0,
                    "floor_id": [floor_id, floor.name or ""]
                } for table in floor.table_ids],
            }
        })
        return {"id": table_id.id, "newTable": create_values}


class RestaurantFloorInherit(models.Model):
    _inherit = "restaurant.floor"

    @api.model
    def get_restaurant_floor_para_llevar(self):
        try:
            return self.env.ref("tm_pos.restaurant_para_llever_floor").id
        except Exception as e:
            return False

    def unlink(self):
        for record in self:
            if record.id == self.env.ref("tm_pos.restaurant_para_llever_floor").id:
                raise ValidationError(_("Sorry, You can't delete Para llevar floor."))
        return super(RestaurantFloorInherit, self).unlink()
