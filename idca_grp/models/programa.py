from odoo import models, fields

class Programa(models.Model):
    _name = 'idca.programa'
    _description = 'Programa'

    name = fields.Char(string='Nombre', required=True)
    description = fields.Text(string='Descripción')
