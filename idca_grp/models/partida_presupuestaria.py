from odoo import models, fields

class PartidaPresupuestaria(models.Model):
    _name = 'idca.partida.presupuestaria'
    _description = 'Partida Presupuestaria'

    name = fields.Char(string='Nombre', required=True)
    description = fields.Text(string='Descripción')
