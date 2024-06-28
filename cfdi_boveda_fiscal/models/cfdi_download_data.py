# -*- encoding: utf-8 -*-
from base64 import b64decode, b64encode
from zipfile import ZipFile
from odoo import api, fields, models, _, tools
from odoo.exceptions import UserError


class CfdiDownloadData(models.Model):
    _name = "cfdi.download.data"
    _description = "CFDI Download Data"
    _rec_name = 'uuid'

    request_id = fields.Many2one(comodel_name='cfdi.download.request', string="Solicitud", required=True, ondelete='cascade')
    pack_id = fields.Many2one(comodel_name='cfdi.download.pack', string="Paquete", required=True, ondelete='cascade')
    uuid = fields.Char(string="UUID", required=True)    
    filename = fields.Char(string="Archivo XML", required=True)    
    emisor = fields.Char(string="RFC emisor", required=True)
    rs_emisor = fields.Char(string="Razón social emisor", required=True)
    fecha = fields.Char(string="Fecha", required=True)
    tipo = fields.Char(string="Tipo", required=True)
    serie = fields.Char(string="Serie", required=False)
    folio = fields.Char(string="Folio", required=True)
    total = fields.Char(string="Total", required=True)
    conceptos = fields.Text(string="Conceptos")
    invoice_id = fields.Many2one(comodel_name='account.move', string="Factura")
    invoice_payment_state = fields.Selection(related='invoice_id.payment_state')
    company_id = fields.Many2one(comodel_name="res.company", string="Compañia", default=lambda self: self.env.company, copy=True)

    def view_invoice(self):
        # Obtenemos el action       
        action_id = self.env["ir.actions.actions"]._for_xml_id("account.action_move_in_invoice_type")
        # Se actualiza el domain     
        action_id.update({'domain': "[('id', '=', %s)]" % str(self.invoice_id.id)})
        return action_id     

    def create_invoice(self):
        for rec in self:
            # Si ya tiene factura
            if rec.invoice_id:
                continue            
            # Se busca el partner y se crea si no existe
            partner_id = self.env['res.partner'].search([('name', '=', self.rs_emisor)])
            if not partner_id:
                partner_id = self.env['res.partner'].create({'name': self.rs_emisor})
            # Se crea la factura
            vals = {
                'partner_id': partner_id.id,
                'move_type': 'in_invoice',
                'state': 'draft',
                'invoice_date': self.fecha.split('T')[0]
            }
            invoice_id = self.env['account.move'].create(vals)
            # Se obtienen los conceptos y se crea una linea para cada concepto
            cons = eval(rec.conceptos)    
            for c in cons:
                # Para cada traslado se busca un impuesto 
                traslados = c.get('Traslados')
                # Se buscan los impuestos 
                tax_ids = []
                total_concepto = 0
                for traslado in traslados:
                    total_concepto += float(traslado.get('Base')) + float(traslado.get('Importe'))
                    tax_id = self.env['account.tax'].search([
                        ('active', '=', True),
                        ('type_tax_use', '=', 'purchase'),
                        ('amount', '=', 100 * float(traslado.get('TasaOCuota')))
                    ])
                    if not tax_id:
                        raise UserError(
                            "No se ha configurado el impuesto tipo {} con tasa {}".format(
                                traslado.get('Impuesto'),
                                traslado('TasaOCuota')))
                    tax_ids.append((4, tax_id.id, 0))
                    tax_repartition_line_id = self.env['account.tax.repartition.line'].search([
                        ('tax_id', '=', tax_id.id),
                        ('company_id', '=', self.env.company.id),
                        ('repartition_type', '=', 'tax')
                    ], limit=1)
                    # Linea de impuesto
                    tax_line = {
                        'move_id': invoice_id.id,
                        'account_id': tax_id.cash_basis_transition_account_id.id, 
                        'quantity': 1,
                        'name': tax_id.name,
                        'price_unit': float(traslado.get('Importe')),           
                        'debit': float(traslado.get('Importe')),
                        'tax_line_id': tax_id.id,
                        'tax_group_id': tax_id.tax_group_id.id,
                        'tax_base_amount': float(traslado.get('Base')),
                        'tax_repartition_line_id': tax_repartition_line_id.id if tax_repartition_line_id else False,
                        # 'exclude_from_invoice_tab': True,
                    }
                    self.env['account.move.line'].with_context(check_move_validity=False).create(tax_line)
                # Linea de débito
                valor_unitario = float(c.get('ValorUnitario'))
                if c.get('Descuento') != 'None':
                    valor_unitario -= float(c.get('Descuento'))
                debit_line = {
                    'move_id': invoice_id.id,
                    'account_id': invoice_id.journal_id.default_account_id.id,
                    'quantity': float(c.get('Cantidad')),
                    'price_unit': valor_unitario,
                    'debit': valor_unitario * float(c.get('Cantidad')),
                    'product_id': False,
                    'name': c.get('Descripcion'),
                    'tax_ids': tax_ids if tax_ids else False
                }            
                self.env['account.move.line'].with_context(check_move_validity=False).create(debit_line)

                # Linea de crédito
                credit_line = {
                    'move_id': invoice_id.id,
                    'account_id': invoice_id.partner_id.property_account_payable_id.id,
                    'quantity': float(c.get('Cantidad')),
                    'credit': total_concepto,
                    # 'exclude_from_invoice_tab': True,
                    'tax_ids': tax_ids if tax_ids else False
                    }
                self.env['account.move.line'].with_context(check_move_validity=False).create(credit_line)
                                    
            # Se lee el archivo zip
            zip_file = open('./'+self.pack_id.id_paquete, "wb")
            zip_file.write(b64decode(self.pack_id.paquete_b64))
            zip_file.close()          
            # 
            with ZipFile('./'+self.pack_id.id_paquete) as zf:
                vals_list = []    
                # Para cada xml de zip        
                for file in zf.namelist():               
                    if not file.endswith('.xml'):
                        continue
                    if file == self.filename:              
                        with zf.open(file) as f:                     
                            # Se adjunta el xml
                            self.env['ir.attachment'].create({
                                'name': file,
                                'type': 'binary',
                                'datas': b64encode(f.read()),
                                'res_model': 'account.move',
                                'res_id': invoice_id.id,
                                'mimetype': 'application/xml'
                            })
                        break            
            # Se actualiza el campo de la factura
            rec.invoice_id = invoice_id.id                    
        return True
