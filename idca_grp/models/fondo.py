from odoo import models, fields

class Fondo(models.Model):
    _name = 'idca.fondo'
    _description = 'Fondo'

    name = fields.Char(string='Nombre', required=True)
    description = fields.Text(string='Descripción')
