from odoo import models, fields

class AccountMove(models.Model):
    _inherit = 'account.move'

    serie = fields.Char(string='Serie')