from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class PurchaseList(models.Model):
    _name = "purchase.list"
    _description = "Purchase List"
    _order = "create_date desc"

    name = fields.Char(string="Order Reference", required=True, default="/")
    purchase_ids = fields.Many2many("purchase.order", string="Purchase Orders")
    allowed_partners = fields.Many2many(
        "res.partner", "vendor_purchase_order_list_rel",
        "list_id", "partner_id", compute="_compute_allowed_partners", string="Allowed Supplier")
    supplier_ids = fields.Many2many("res.partner", domain="[('id', 'in', allowed_partners)]", string="Supplier")
    supplier_name = fields.Char(string="Supplier Name", compute="_compute_supplier_name", compute_sudo=True, store=True)
    state = fields.Selection([
        ("ongoing", "Ongoing"),
        ("done", "Done"),
    ], string="State", default="ongoing", required=True)

    confirm_order_and_entry = fields.Boolean(string="Confirmed orders and Entries", default=False)
    missing_product = fields.Boolean(string="Missing Product", default=False)
    # Purchase List
    purchase_list_lines = fields.One2many("purchase.list.line", "list_id", string="Purchase List")
    purchased = fields.Boolean(string="Purchased", compute="_compute_purchased", compute_sudo=True, store=True)

    @api.depends("purchase_ids", "purchase_ids.partner_id")
    def _compute_allowed_partners(self):
        for record in self:
            if record.purchase_ids:
                record.allowed_partners = [(6, 0, record.purchase_ids.mapped("partner_id").ids)]
            else:
                record.allowed_partners = False

    @api.depends("purchase_list_lines", "purchase_list_lines.purchased")
    def _compute_purchased(self):
        for record in self:
            purchased = False
            if record.purchase_list_lines:
                purchased = all([pl.purchased for pl in record.purchase_list_lines])
            record.purchased = purchased

    @api.depends("supplier_ids", "supplier_ids.name")
    def _compute_supplier_name(self):
        for record in self:
            if record.supplier_ids:
                record.supplier_name = ",".join(record.supplier_ids.mapped("name"))
            else:
                record.supplier_name = False

    @api.onchange("supplier_ids")
    def onchange_supplier_to_set_purchase_list(self):
        _cr = self.env.cr
        reordering_rules = self.env["stock.warehouse.orderpoint"]
        if self.supplier_ids:
            purchases = self.purchase_ids.filtered(lambda x: x.partner_id.id in self.supplier_ids.ids)
            values = self._modify_purchase_order_to_purchase_list(purchases, reordering_rules)
            lines = [(5, 0)]
            for key in values:
                lines.append((0, 0, {
                    "product_id": key,
                    "purchase_order_ids": [(6, 0, values[key]["purchase_ids"])],
                    "supplier_ids": [(6, 0, values[key]["supplier_ids"])],
                    "orderpoint_ids": [(6, 0, values[key]["orderpoint_ids"])],
                    "product_qty": values[key]["product_qty"]
                }))
            self.purchase_list_lines = lines
        else:
            self.supplier_ids = [(6, 0, [self.env.ref("purchase_order_list.res_partner_not_purchased").id])]
            values = self._modify_purchase_order_to_purchase_list(self.purchase_ids, reordering_rules)
            lines = [(5, 0)]
            for key in values:
                lines.append((0, 0, {
                    "product_id": key,
                    "purchase_order_ids": [(6, 0, values[key]["purchase_ids"])],
                    "supplier_ids": [(6, 0, values[key]["supplier_ids"])],
                    "orderpoint_ids": [(6, 0, values[key]["orderpoint_ids"])],
                    "product_qty": values[key]["product_qty"]
                }))
            self.purchase_list_lines = lines

    @staticmethod
    def _modify_purchase_order_to_purchase_list(purchase_rqf_ids, reordering_rules):
        values = {}
        for rfq in purchase_rqf_ids:
            if not rfq.order_line:
                continue
            lines = rfq.order_line
            product_ids = lines.mapped("product_id")
            for prod in product_ids:
                product_uom_qty = sum([ll.product_qty for ll in lines.filtered(lambda line: line.product_id == prod)])
                order_point = reordering_rules.search([("product_id", "=", prod.id)])
                # Not orderpoint record.
                if not order_point:
                    if prod.id not in values.keys():
                        values[prod.id] = {
                            "product_id": prod.id,
                            "purchase_ids": [rfq.id],
                            "supplier_ids": [rfq.partner_id.id],
                            "orderpoint_ids": [],
                            "missing_product": True,
                            "product_qty": product_uom_qty
                        }
                    else:
                        purchase_ids = values[prod.id]
                        if rfq.id not in purchase_ids:
                            values[prod.id]["purchase_ids"].append(rfq.id)
                            values[prod.id]["supplier_ids"].append(rfq.partner_id.id)
                            values[prod.id]["product_qty"] += product_uom_qty
                    continue
                if prod.id not in values.keys():
                    values[prod.id] = {
                        "product_id": prod.id,
                        "purchase_ids": [rfq.id],
                        "supplier_ids": [rfq.partner_id.id],
                        "orderpoint_ids": order_point.ids,
                        "product_qty": product_uom_qty
                    }
                else:
                    purchase_ids = values[prod.id]
                    if rfq.id not in purchase_ids:
                        values[prod.id]["purchase_ids"].append(rfq.id)
                        values[prod.id]["supplier_ids"].append(rfq.partner_id.id)
                        values[prod.id]["product_qty"] += product_uom_qty
        return values

    def action_gen_purchase_list(self):
        purchase_rqf_ids = self.env["purchase.order"].search([("state", "=", "draft")])
        if not purchase_rqf_ids:
            return self.action_notification(message="Generate Purchase List successful.\nHaven't Purchase Orders are Draft")

        reordering_rules = self.env["stock.warehouse.orderpoint"]

        list_values = {"name": self.env["ir.sequence"].next_by_code("purchase.order.list.sequence") or "/",
                       "supplier_ids": False, "purchase_ids": False, "purchase_list_lines": False}
        values = self._modify_purchase_order_to_purchase_list(purchase_rqf_ids, reordering_rules)
        purchase_list_lines = []

        if values:
            ll_supplier_ids, ll_purchase_ids = [], []
            for key in values:
                purchase_list_lines.append((0, 0, {
                    "product_id": key,
                    "purchase_order_ids": [(6, 0, values[key]["purchase_ids"])],
                    "supplier_ids": [(6, 0, values[key]["supplier_ids"])],
                    "orderpoint_ids": [(6, 0, values[key]["orderpoint_ids"])],
                    "product_qty": values[key]["product_qty"]
                }))
                ll_supplier_ids.extend(values[key]["supplier_ids"])
                ll_purchase_ids.extend(values[key]["purchase_ids"])

            if purchase_list_lines:
                list_values.update({
                    "purchase_list_lines": purchase_list_lines,
                    "purchase_ids": [(6, 0, list(set(ll_purchase_ids)))],
                    "supplier_ids": [(6, 0, list(set(ll_supplier_ids)))],
                })

            self.env["purchase.list"].create(list_values)
        return self.action_notification(message="Generate Purchase List successful.")

    def action_confirm_orders_and_entries(self):
        def action_validate_picking(picking_record):
            try:
                move_ids_without_package = picking_record.move_ids_without_package
                if not move_ids_without_package:
                    return True
                update_values = []
                for pk in move_ids_without_package:
                    if pk.quantity == 0 or pk.product_uom_qty != pk.quantity:
                        update_values.append((1, pk.id, {"quantity": pk.product_uom_qty}))
                if update_values:
                    picking.write({"move_ids_without_package": update_values})
                picking.with_context(skip_sms=True).button_validate()
            except Exception as e:
                return self.action_notification(message="Confirm orders and Entries error!\n%s" % e, notification_type="warning")

        purchase_lists = self.env["purchase.list"]
        for record in self:
            if record.confirm_order_and_entry:
                continue
            if all([line.purchased for line in record.purchase_list_lines]):
                purchase_lists += record
        if not purchase_lists:
            raise ValidationError(_("Sorry, You can not Confirm Purchase Orders & Picking when all records are not purchased or Records has been Confirm ago."))
        for record in purchase_lists:
            purchase_orders = record.purchase_list_lines.mapped("purchase_order_ids")
            if purchase_orders:
                for po in purchase_orders:
                    if po.state == "draft":
                        po.button_confirm()
                self.env.cr.commit()
            stock_pickings = purchase_orders.mapped("picking_ids")
            draft_pickings = stock_pickings.filtered(lambda p: p.state == "draft")
            ready_pickings = stock_pickings.filtered(lambda p: p.state in ["waiting", "confirmed"])
            assigned_pickings = stock_pickings.filtered(lambda p: p.state == "assigned")
            # confirm picking ready
            for picking in ready_pickings:
                action_validate_picking(picking)
            # confirm picking DRAFT
            for picking in draft_pickings:
                picking.action_confirm()
                action_validate_picking(picking)
            for picking in assigned_pickings:
                action_validate_picking(picking)

            record.write({"confirm_order_and_entry": True, "state": "done"})
        return self.action_notification(message="Confirm orders and Entries successful.")

    def action_notification(self, message, notification_type="success"):
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'target': 'new',
            'params': {
                'message': message,
                'type': notification_type,
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }

    @api.model_create_multi
    def create(self, vals_list):
        res = super(PurchaseList, self).create(vals_list)
        return res


class PurchaseListLine(models.Model):
    _name = "purchase.list.line"
    _description = "Purchase List Line"

    list_id = fields.Many2one("purchase.list", string="PurchaseListID")
    product_id = fields.Many2one("product.product", string="Product")
    image_1920 = fields.Image(related="product_id.image_1920", string="Image")
    product_name = fields.Text(string="Product Name", compute="_compute_product_name", store=True)
    purchased = fields.Boolean(string="Purchased", default=False)
    purchase_order_ids = fields.Many2many(
        "purchase.order", "purchase_order_purchase_list_line_rel",
        "line_id", "order_id", string="Purchase Orders")
    orderpoint_ids = fields.Many2many(
        "stock.warehouse.orderpoint", "purchase_list_line_stock_warehouse_orderpoint_rel",
        "list_id", "orderpoint_id", string="Reordering Rules")
    supplier_ids = fields.Many2many(
        "res.partner", "res_partner_purchase_list_line_rel",
        "list_id", "partner_id", string="Supplier")
    product_qty = fields.Float(string="Purchase Qty")

    @api.depends('product_id')
    def _compute_product_name(self):
        for line in self:
            line.product_name = line.product_id.name if line.product_id else ''


class ResPartnerPurchaseList(models.Model):
    _inherit = "res.partner"

    def unlink(self):
        for record in self:
            if record.id in [self.env.ref("purchase_order_list.res_partner_not_purchased").id]:
                raise ValidationError(_("Sorry! You can't delete this customer. Please contact to Developer for more information."))
        return super(ResPartnerPurchaseList, self).unlink()
