# -*- encoding: utf-8 -*-
from base64 import b64decode
import os
from zipfile import ZipFile
from odoo import api, fields, models, _, tools


class CfdiDownloadPack(models.Model):
    _name = "cfdi.download.pack"
    _description = "CFDI Download pack"
    _rec_name = 'id_paquete'
    _order = 'create_date desc'

    request_id = fields.Many2one(comodel_name='cfdi.download.request', string="Solicitud", required=True, ondelete='cascade')
    id_paquete = fields.Char(string="ID paquete", required=True)
    rfc_solicitante = fields.Char(string="RFC solicitante")
    numero_cfdis = fields.Integer(string="Número cfdis", related='request_id.numero_cfdis')
    fecha_inicial = fields.Date(string="Fecha inicial", related='request_id.fecha_inicial')
    fecha_final = fields.Date(string="Fecha final", related='request_id.fecha_final')
    request_type = fields.Selection([
        ('emitidos', 'Emitidos'),
        ('recibidos', 'Recibidos')
    ], string="Tipo", compute='_compute_request_type', compute_sudo=True, store=True)
    cod_estatus = fields.Char(string="Cod. Estatus", required=True)
    mensaje = fields.Char(string="Mensaje solicitud", required=True)
    paquete_b64 = fields.Text(string="Paquete b64", required=True)
    company_id = fields.Many2one("res.company", string="Compañia", default=lambda self: self.env.company, copy=True)

    @api.depends("request_id", "request_id.request_type")
    def _compute_request_type(self):
        for record in self:
            if record.request_id:
                record.request_type = record.request_id.request_type
            else:
                record.request_type = False

    def generate_zip(self):
        if self.cod_estatus == '5000':   
            # Get content 
            output = b64decode(self.paquete_b64)           
            # get base url
            base_url = self.env['ir.config_parameter'].get_param('web.base.url')      
            # create attachment
            attachment_id = self.env['ir.attachment'].create({
                'name': self.id_paquete+'.zip', 
                'db_datas': output
            })
            # prepare download url
            download_url = '/web/content/' + str(attachment_id.id) + '?download=true'
            # download
            return {
                "type": "ir.actions.act_url",
                "url": str(base_url) + str(download_url),
                "target": "self",
            }

    def generate_xml_vals(self):
        # Se lee el archivo zip
        zip_file = open('./'+self.id_paquete, "wb")
        zip_file.write(b64decode(self.paquete_b64))
        zip_file.close()
        TipoDeComprobante = {
            'Ingreso': 'I',
            'Egreso': 'E',
            'Traslado': 'T',
            'Pago': 'P',
            'Nómina': 'N',
        }
        with ZipFile('./'+self.id_paquete) as zf:
            vals_list = []            
            for file in zf.namelist():               
                if not file.endswith('.xml'):
                    continue
                with zf.open(file) as f:
                    vals = self.env['request.wizard']._parse_xml_cfdi(f.read())                      
                    if vals:                         
                        val = {                           
                            'uuid': vals.get('uuid'),
                            'filename': file,                            
                            'emisor': vals.get('emisor'),
                            'rs_emisor': vals.get('rs_emisor'),
                            'receptor': vals.get('receptor'),
                            'rs_receptor': vals.get('rs_receptor'),
                            'TipoDeComprobante': TipoDeComprobante.get(vals.get('TipoDeComprobante')),
                            'Serie': vals.get('Serie'),
                            'Folio': vals.get('Folio'),
                            'Fecha': vals.get('Fecha'),
                            'SubTotal': vals.get('SubTotal'),
                            'Descuento': vals.get('Descuento'),
                            'TotalImpuestosTrasladados': vals.get('TotalImpuestosTrasladados'),
                            'TipoImpuestoTrasladado': vals.get('TipoImpuestoTrasladado'),
                            'TotalImpuestosRetenidos': vals.get('TotalImpuestosRetenidos'),
                            'TipoImpuestoRetenido': vals.get('TipoImpuestoRetenido'),
                            'Total': vals.get('Total'),
                            'MetodoPago': vals.get('MetodoPago'),
                            'FormaPago': vals.get('FormaPago'),
                            'Moneda': vals.get('Moneda'),
                            'TipoCambio': vals.get('TipoCambio'),
                            'Version': vals.get('Version'),
                            'UsoCFDI': vals.get('UsoCFDI'),
                            'RegimenFiscal': vals.get('RegimenFiscal'),
                            'Conceptos': vals.get('Conceptos'), 
                        }                                           
                        vals_list.append(val)
        # Se elimina el zip
        os.remove('./'+self.id_paquete)
        return vals_list     
