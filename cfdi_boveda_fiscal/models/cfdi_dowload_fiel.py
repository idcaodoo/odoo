# -*- encoding: utf-8 -*-
from odoo import api, fields, models, _, tools
from odoo.exceptions import UserError


class CfdiDownloadFiel(models.Model):
    _name = "cfdi.download.fiel"
    _description = "CFDI Download FIEL"
    _rec_name = 'rfc'

    rfc = fields.Char(string="RFC", required=True)
    cer_name = fields.Char(string="Certificado")
    cer_file = fields.Binary(string='Archivo (.cer)', required=True)
    key_name = fields.Char(string="Llave")
    key_file = fields.Binary(string='Archivo (.key)', required=True)
    password = fields.Char(string='Contraseña', required=True)
    company_id = fields.Many2one("res.company", string="Compañia", default=lambda self: self.env.company, copy=True)

    @api.model_create_multi
    def create(self, vals_list):
        # Obtenemos las FIELS del usuario
        n = self.search_count([])
        if n > 0:        
            raise UserError('Ya existe un registro de FIEL.')
        res = super(CfdiDownloadFiel, self).create(vals_list)
        return res
