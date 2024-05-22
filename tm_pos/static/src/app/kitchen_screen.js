/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { Order } from "@pos_preparation_display/app/models/order";

patch(Order.prototype, {
    setup(order) {
        super.setup(...arguments);
        console.log(order);
        this.table_service_note = order.table_service_note;
    },

});