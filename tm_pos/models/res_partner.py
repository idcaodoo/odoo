from odoo import api, models, _
from odoo.exceptions import ValidationError


class ResPartnerPosOrder(models.Model):
    _inherit = "res.partner"

    @api.constrains("name")
    def _validate_change_name_with_core_name(self):
        for record in self:
            try:
                if record.id in [self.env.ref("tm_pos.res_partner_cliente_mostrador").id,
                                 self.env.ref("tm_pos.res_partner_cliente_uber").id,
                                 self.env.ref("tm_pos.res_partner_cliente_didi").id,
                                 self.env.ref("tm_pos.res_partner_cliente_rappi").id]:
                    raise ValidationError(_("Sorry, You can't change the name of this customer. Please contact to Developer for more information."))
            except Exception as e:
                pass

    def unlink(self):
        for record in self:
            if record.id in [self.env.ref("tm_pos.res_partner_cliente_mostrador").id,
                             self.env.ref("tm_pos.res_partner_cliente_uber").id,
                             self.env.ref("tm_pos.res_partner_cliente_didi").id,
                             self.env.ref("tm_pos.res_partner_cliente_rappi").id]:
                raise ValidationError(_("Sorry! You can't delete this customer. Please contact to Developer for more information."))
        return super(ResPartnerPosOrder, self).unlink()
