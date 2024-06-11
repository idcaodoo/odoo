from odoo import api, fields, models


class POSProductCategory(models.Model):
    _inherit = "pos.category"

    mostrador = fields.Boolean(string="Mostrador")

    @api.model
    def get_mostrador_product_category(self, pos_config):
        try:
            pos_config_id = self.env["pos.config"].sudo().browse(pos_config)
            if not pos_config_id:
                return False
            allowed_categories = pos_config_id.iface_available_categ_ids.ids
            mostrador_id = self.env.ref("tm_pos.pos_product_category_mostrador").id
            return mostrador_id in allowed_categories and mostrador_id or False
        except Exception as e:
            return False
