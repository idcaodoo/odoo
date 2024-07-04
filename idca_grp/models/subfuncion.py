from odoo import models, fields

class Subfuncion(models.Model):
    _name = 'idca.subfuncion'
    _description = 'Subfunción'

    name = fields.Char(string='Nombre', required=True)
    description = fields.Text(string='Descripción')
