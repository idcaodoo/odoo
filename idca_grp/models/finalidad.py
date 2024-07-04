from odoo import models, fields

class Finalidad(models.Model):
    _name = 'idca.finalidad'
    _description = 'Finalidad'

    name = fields.Char(string='Nombre', required=True)
    description = fields.Text(string='Descripción')
