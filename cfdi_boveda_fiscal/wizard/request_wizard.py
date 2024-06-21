# -*- coding: utf-8 -*-
from base64 import b64decode
from datetime import datetime

from cfdiclient import Fiel
from cfdiclient import Autenticacion
from cfdiclient import SolicitaDescarga
from cfdiclient import VerificaSolicitudDescarga
from cfdiclient import DescargaMasiva
import time
import xml.etree.cElementTree as ET

from odoo import api, fields, models, _, tools
from odoo.exceptions import UserError


class RequestWizard(models.TransientModel):
    _name = "request.wizard"
    _description = "Request Wizard"
    
    request_id = fields.Many2one(comodel_name='cfdi.download.request', string="Solicitud")
    fiel_id = fields.Many2one(comodel_name='cfdi.download.fiel', string="FIEL")   
    request_type = fields.Selection([
        ('emitidos', 'Emitidos'),
        ('recibidos', 'Recibidos')], string="Tipo de solicitud", required=True)
    fecha_inicial = fields.Date(string="Fecha inicial")
    fecha_final = fields.Date(string="Fecha final")

    @api.onchange('request_type')
    def on_change_request_type(self):
        if self.request_type:
            fiel_id = self.env['cfdi.download.fiel'].search([('company_id', '=', self.env.company.id)], limit=1)
            self.fiel_id = fiel_id and fiel_id.id or False
            self.fecha_inicial = False
            self.fecha_final = False
    
    @api.onchange('fecha_inicial')
    def on_change_fecha_inicial(self):
        if self.fecha_inicial:
            self.fecha_final = self.fecha_inicial
    
    @api.onchange('fecha_final')
    def on_change_fecha_final(self):
        if self.fecha_final:
            delta = self.fecha_final - self.fecha_inicial
            if delta.days < 0:
                self.fecha_final = self.fecha_inicial

    def action_request(self):
        # Solicitar descarga
        # Validamos periodo
        if not self.fecha_inicial and not self.fecha_final:
            return True
        delta = self.fecha_final - self.fecha_inicial
        if delta.days > 31:
            raise UserError("Solo puede hacer solictudes por un periodo de hasta 31 días.")                      
        #
        if not self.fiel_id.cer_file:
            raise UserError("Archivo (.cer) debe ser obligatorio.")
        if not self.fiel_id.key_file:
            raise UserError("Archivo (.key) debe ser obligatorio.")
        cer_der = b64decode(self.fiel_id.cer_file)
        key_der = b64decode(self.fiel_id.key_file)
        password = self.fiel_id.password
        try:        
            fiel = Fiel(cer_der, key_der, password)
            # Autenticar
            auth = Autenticacion(fiel)
            token = auth.obtener_token()
            # Solicitar
            descarga = SolicitaDescarga(fiel)
            fecha_inicial = datetime(self.fecha_inicial.year, self.fecha_inicial.month, self.fecha_inicial.day)
            fecha_final = datetime(self.fecha_final.year, self.fecha_final.month, self.fecha_final.day)
            #
            if self.request_type == 'recibidos':
                result = descarga.solicitar_descarga(token, self.fiel_id.rfc, fecha_inicial, fecha_final, rfc_receptor=self.fiel_id.rfc)
            elif self.request_type == 'emitidos':
                result = descarga.solicitar_descarga(token, self.fiel_id.rfc, fecha_inicial, fecha_final, rfc_emisor=self.fiel_id.rfc)
            else:
                return True
            # Se crea la solicitud
            vals = {           
                'fiel_id': self.fiel_id.id,
                'id_solicitud': result.get('id_solicitud'),
                'rfc_solicitante': self.fiel_id.rfc,
                'rfc_emisor': self.fiel_id.rfc,
                'rfc_receptor': self.fiel_id.rfc,
                'fecha_inicial': self.fecha_inicial,
                'fecha_final': self.fecha_final,
                'cod_estatus': result.get('cod_estatus'),
                'mensaje': result.get('mensaje'),
                'request_type': self.request_type,            
            }
            request_id = self.env['cfdi.download.request'].create(vals)     
            #
            time.sleep(3)
            request_id.verfication_request()
            if request_id.estado_solicitud_type == '3':
                request_id.download_request()
            action_id = self.env["ir.actions.actions"]._for_xml_id("cfdi_boveda_fiscal.cfdi_download_request_action")
            return action_id
        except ValueError:
            raise UserError('* Revise que tenga una conexión a internet.\n * Revise que la contraseña de la FIEL sea correcta,')           

    def action_verfication_request(self):
        if self.request_id.estado_solicitud_type in ['1', '2', '3', False]:
            cer_der = b64decode(self.fiel_id.cer_file)
            key_der = b64decode(self.fiel_id.key_file)
            password = self.fiel_id.password
            try:
                fiel = Fiel(cer_der, key_der, password)
                # Autenticar
                auth = Autenticacion(fiel)
                token = auth.obtener_token()
                # Verificar descarga
                v_descarga = VerificaSolicitudDescarga(fiel)                
                result = v_descarga.verificar_descarga(token, self.request_id.rfc_solicitante, self.request_id.id_solicitud)
                self.request_id.cod_estatus_ver = result.get('cod_estatus')
                self.request_id.mensaje_ver = result.get('mensaje')
                self.request_id.estado_solicitud = result.get('estado_solicitud')
                self.request_id.estado_solicitud_type = result.get('estado_solicitud')
                self.request_id.codigo_estado_solicitud = result.get('codigo_estado_solicitud')
                self.request_id.codigo_estado_solicitud_type = result.get('codigo_estado_solicitud')
                self.request_id.numero_cfdis = int(result.get('numero_cfdis'))
                self.request_id.paquetes = result.get('paquetes')        
                self.request_id.num_paquetes = len(result.get('paquetes'))
            except Exception as e:
                raise UserError("Error de conexión.")
        return True

    def action_download_request(self):
        # Se buscan paquetes de la solicitud de descarga
        pack_ids = self.env['cfdi.download.pack'].search([('request_id', '=', self.request_id.id)])
        # Si el estatus de la solicitud es 3 y no tiene paquetes desacargados se procede a la descarga
        if self.request_id.estado_solicitud_type in ['3'] and not pack_ids:
            cer_der = b64decode(self.fiel_id.cer_file)
            key_der = b64decode(self.fiel_id.key_file)
            password = self.fiel_id.password       
            #
            try: 
                fiel = Fiel(cer_der, key_der, password)
                # Autenticar
                auth = Autenticacion(fiel)
                token = auth.obtener_token()

                descarga = DescargaMasiva(fiel)      
                paquetes = eval(self.request_id.paquetes)
                # Para cada paquete
                for id_paquete in paquetes:    
                    result = descarga.descargar_paquete(token, self.request_id.rfc_solicitante, id_paquete)           
                    #
                    cod_estatus = int(result.get('cod_estatus'))
                    #
                    if cod_estatus == 5000:
                        # Se guarda el pack
                        vals = {
                            'request_id': self.request_id.id,  
                            'id_paquete': id_paquete,
                            'cod_estatus': result.get('cod_estatus'),
                            'mensaje': result.get('mensaje'),
                            'paquete_b64': result.get('paquete_b64'),
                            'rfc_solicitante': self.request_id.rfc_solicitante, 
                            } 
                        #
                        self.env['cfdi.download.pack'].create(vals)
                        #
                        self.request_id.estado_solicitud_type = '0'  
                        self.request_id.estado_solicitud = '0'                      
                    #
                    if cod_estatus == 5008:                   
                        # Se pone en estatus realizada
                        self.request_id.estado_solicitud_type = '0'
                        self.request_id.estado_solicitud = '0'
            except Exception as e:
                raise UserError("Error de conexión.")

    def _parse_xml_cfdi(self, xml=False):
        if not xml:
            return False
        root = ET.fromstring(xml)
        root_tag = root.tag.replace('Comprobante', '')
        # Emisor
        emisor = ''
        # RegimenFiscal
        RegimenFiscal = ''
        for e in root.findall(root_tag + 'Emisor'):    
            emisor = e.get('Rfc')
            rs_emisor = e.get('Nombre') 
            RegimenFiscal = e.get('RegimenFiscal')                       
        # Receptor
        receptor = ''
        UsoCFDI = ''
        for e in root.findall(root_tag + 'Receptor'):    
            receptor = e.get('Rfc')
            rs_receptor = e.get('Nombre')   
            UsoCFDI = e.get('UsoCFDI')             
        # uuid
        uuid = ''
        for c in root.findall(root_tag + 'Complemento'):
            for e in c:        
                uuid = e.get('UUID')
        # fechaTimbrado
        fechaTimbrado = ''
        for c in root.findall(root_tag + 'Complemento'):
            for e in c:        
                fechaTimbrado = e.get('FechaTimbrado')    
        # RfcProvCertif
        for c in root.findall(root_tag + 'Complemento'):
            for e in c:        
                RfcProvCertif = e.get('RfcProvCertif')    
        
        # TotalImpuestosTrasladados                            
        TotalImpuestosTrasladados = 0
        for e in root.findall(root_tag + 'Impuestos'):    
            TotalImpuestosTrasladados = e.get('TotalImpuestosTrasladados')
        # TotalImpuestosRetenidos                            
        TotalImpuestosRetenidos = 0
        for e in root.findall(root_tag + 'Impuestos'):    
            TotalImpuestosRetenidos = e.get('TotalImpuestosRetenidos')
        # Conceptos
        Conceptos = '['
        for e in root.findall(root_tag + 'Conceptos'):            
            for c in e.findall(root_tag + 'Concepto'):
                # Impuestos trasladados
                Traslados = '['
                for i in c.findall(root_tag + 'Impuestos'):        
                    for ts in i.findall(root_tag + 'Traslados'):
                        for t in ts.findall(root_tag + 'Traslado'):
                            traslado = """
                                'Base': '{}',
                                'Importe': '{}',
                                'Impuesto': '{}',
                                'TasaOCuota': '{}',
                                'TipoFactor': '{}'                    
                                """.format(t.get('Base'), t.get('Importe'), t.get('Impuesto'), t.get('TasaOCuota'), t.get('TipoFactor'))
                            Traslados += '{' + traslado + '},'
                Traslados = Traslados[:-1] + ']' if len(Traslados) > 1 else '[]'

                concepto = """
                    'Cantidad': '{}', 
                    'ClaveProdServ': '{}', 
                    'ClaveUnidad': '{}', 
                    'Descripcion': '{}', 
                    'Descuento': '{}', 
                    'Importe': '{}', 
                    'ValorUnitario': '{}',
                    'Traslados': {}""".format(c.get('Cantidad'), c.get('ClaveProdServ'), c.get('ClaveUnidad'),
                                              c.get('Descripcion'), c.get('Descuento'), c.get('Importe'),
                                              c.get('ValorUnitario'), Traslados)
                Conceptos += '{' + concepto + '},'
        Conceptos = Conceptos[:-1] + ']'                                  
        # TipoDeComprobante
        tiposComprobante = {'I': 'Ingreso', 'E': 'Egreso', 'T': 'Traslado', 'P': 'Pago', 'N': 'Nómina'}

        vals = {
            'emisor': emisor,
            'rs_emisor': rs_emisor,
            'receptor': receptor,
            'rs_receptor': rs_receptor,
            'TipoDeComprobante': tiposComprobante.get(root.get('TipoDeComprobante')),
            'Serie': root.get('Serie'),
            'Folio': root.get('Folio'),
            'Fecha': root.get('Fecha'),
            'SubTotal': root.get('SubTotal'),
            'Descuento': root.get('Descuento'),
            'TotalImpuestosTrasladados': TotalImpuestosTrasladados,
            'TipoImpuestoTrasladado': '',
            'TotalImpuestosRetenidos': TotalImpuestosRetenidos,
            'TipoImpuestoRetenido': '',
            'Total': root.get('Total'),
            'MetodoPago': root.get('MetodoPago'),
            'FormaPago': root.get('FormaPago'),
            'Moneda': root.get('Moneda'),
            'TipoCambio': root.get('TipoCambio') or 1,
            'Version': root.get('Version'),
            'UsoCFDI': UsoCFDI,
            'RegimenFiscal': RegimenFiscal,
            'Conceptos': Conceptos,
            'uuid': uuid,
            'Fecha': root.get('Fecha'),
            'FechaTimbrado': fechaTimbrado,
            'RfcProvCertif': RfcProvCertif,
            'Conceptos': Conceptos
        }
        return vals
