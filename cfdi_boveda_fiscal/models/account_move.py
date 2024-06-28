from odoo import fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    serie = fields.Char(string="Serie")
