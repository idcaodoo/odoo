# -*- encoding: utf-8 -*-
from odoo import api, fields, models, _, tools


ESTATUS_REQUEST = [
    ('0', 'Finalizada'),
    ('1', 'Aceptada'),
    ('2', 'En proceso'),
    ('3', 'Terminada'),
    ('4', 'Error'),
    ('5', 'Rechazada'),
    ('6', 'Vencida')
]
CODIGOS_REQUEST = [
    ('300', 'Usuario no válido'),
    ('301', 'XML mal formado'),
    ('302', 'Sello mal formado'),
    ('303', 'Sello no corresponde con RfcSolicitante'),
    ('304', 'Certificado Revocado o Caduco'),
    ('305', 'Certificado Inválido'),
    ('404', 'Error no Controlado'),
    ('5000', 'Solicitud recibida con éxito'),
    ('5002', 'Se agotó las solicitudes de por vida'),
    ('5003', 'Tope máximo'),
    ('5004', 'No se encontró la información'),
    ('5005', 'Solicitud duplicada'),
    ('5008', 'Máximo de descargas permitidas'),
]


class CfdiDownloadRequest(models.Model):
    _name = "cfdi.download.request"
    _description = "Solicitud de descarga SAT"
    _rec_name = 'id_solicitud'
    _order = 'create_date desc'
    # 
    fiel_id = fields.Many2one(comodel_name='cfdi.download.fiel', string="FIEL", ondelete='cascade')
    id_solicitud = fields.Char(string="Id. Solicitud", required=True)
    rfc_solicitante = fields.Char(string="RFC solicitante", required=True)
    rfc_emisor = fields.Char(string="RFC emisor", required=True)
    rfc_receptor = fields.Char(string="RFC receptor", required=True)
    fecha_inicial =fields.Date(string="Fecha inicial", required=True)
    fecha_final = fields.Date(string="Fecha final", required=True)   
    cod_estatus = fields.Char(string="Cod. Estatus solicitud", required=True)
    mensaje = fields.Char(string="Mensaje solicitud", required=True)
    request_type = fields.Selection([
        ('emitidos', 'Emitidos'),
        ('recibidos', 'Recibidos')
    ], string="Tipo", default='recibidos', required=True)
    #
    cod_estatus_ver = fields.Char(string="Cod. Estatus verificación")
    mensaje_ver = fields.Char(string="Mensaje verificación")
    estado_solicitud = fields.Char(string="Estado solicitud.")
    estado_solicitud_type = fields.Selection(ESTATUS_REQUEST, string="Estado solicitud")
    codigo_estado_solicitud = fields.Char(string="Código estado solicitud")
    codigo_estado_solicitud_type = fields.Selection(CODIGOS_REQUEST, string="Mensaje")
    numero_cfdis = fields.Integer(string="CFDI's")
    paquetes = fields.Char(string="Contenido paquetes")   
    num_paquetes = fields.Integer(string="Paquetes")   
    company_id = fields.Many2one(
        "res.company", string="Compañia",
        default=lambda self: self.env.company, copy=True, required=True)

    def verfication_request(self):
        vals = {
            'fiel_id': self.fiel_id.id,
            'request_id': self.id,
            'request_type': 'emitidos',          
        }
        wizard_id = self.env['request.wizard'].create(vals)
        wizard_id.action_verfication_request() 
        return True

    def download_request(self):
        vals = {
            'fiel_id': self.fiel_id.id,
            'request_id': self.id,  
            'request_type': 'emitidos',          
        }
        wizard_id = self.env['request.wizard'].create(vals)
        wizard_id.action_download_request() 
        return True

    def view_packs(self):                           
        # Obtenemos los packs
        pack_ids = self.env['cfdi.download.pack'].search([('request_id', '=', self.id)])
        if pack_ids:
            # Obtenemos el action       
            action_id = self.env["ir.actions.actions"]._for_xml_id("cfdi_boveda_fiscal.cfdi_download_pack_action")    
            # Se actualiza el domain     
            action_id.update({'domain': "[('id','in',%s)]" % (str(pack_ids.ids))})
            return action_id
    
    def view_cfdis(self):    
        cfdi_obj = self.env['cfdi.download.data']                       
        #  Obtenemos los packs
        pack_ids = self.env['cfdi.download.pack'].search([('request_id', '=', self.id)])
        if pack_ids:
            # Obtenemos el action       
            action_id = self.env["ir.actions.actions"]._for_xml_id("cfdi_boveda_fiscal.cfdi_download_data_action")    
            # Se obtienen los paquetes de la solicitud
            for pack_id in pack_ids:
                xmls = pack_id.generate_xml_vals()
                for xml in xmls:
                    # Se busca el uuid
                    xml_id = cfdi_obj.search([('uuid', '=', xml.get('uuid'))])
                    if not xml_id:
                        vals = {
                            'uuid': xml.get('uuid'),
                            'filename': xml.get('filename'),                          
                            'request_id': self.id,
                            'pack_id': pack_id.id,
                            'emisor': xml.get('emisor'),
                            'rs_emisor': xml.get('rs_emisor'),
                            'fecha': xml.get('Fecha'),
                            'tipo': xml.get('TipoDeComprobante'),
                            'serie': xml.get('Serie'),
                            'folio': xml.get('Folio'),
                            'total': xml.get('Total'),
                            'conceptos': xml.get('Conceptos')
                        }
                        cfdi_obj.create(vals)
                        
            xml_ids = cfdi_obj.search([('request_id', '=', self.id)])
            # Se actualiza el domain     
            action_id.update({'domain': "[('id','in',%s)]" % (str(xml_ids.ids))})
            return action_id
    
    def generate_zip(self):
        view = {}
        # Se buscan paquetes de la solicitud de descarga
        pack_ids = self.env['cfdi.download.pack'].search([('request_id', '=', self.id)])
        #
        if len(pack_ids) == 1:          
            view = pack_ids[0].generate_zip()           
        else:
            view = self.view_packs()
        return view
