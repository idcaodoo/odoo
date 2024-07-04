from odoo import models, fields

class Funcion(models.Model):
    _name = 'idca.funcion'
    _description = 'Función'

    name = fields.Char(string='Nombre', required=True)
    description = fields.Text(string='Descripción')
