# -*- coding: utf-8 -*-

from odoo import api, models, fields, _

class PosConfig(models.Model):
    _inherit = 'pos.config'

    enable_customer_info = fields.Boolean('Información del cliente en el ticket')

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    enable_customer_info = fields.Boolean(related='pos_config_id.enable_customer_info',readonly=False)
