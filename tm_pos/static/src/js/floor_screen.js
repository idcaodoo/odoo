/** @odoo-module **/

import { FloorScreen } from "@pos_restaurant/app/floor_screen/floor_screen";
import { patch } from "@web/core/utils/patch";
import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";
import { ConfirmPopup } from "@point_of_sale/app/utils/confirm_popup/confirm_popup";
import { _t } from "@web/core/l10n/translation";
const { Component, useState } = owl;
import { useService } from "@web/core/utils/hooks";
import { jsonrpc } from "@web/core/network/rpc_service";
import { registry } from "@web/core/registry";
import { ConnectionLostError, RPCError } from '@web/core/network/rpc_service';
import { TextInputPopup } from "@point_of_sale/app/utils/input_popups/text_input_popup";
import { Orderline } from "@point_of_sale/app/store/models";
import { Order } from "@point_of_sale/app/store/models";

const CACHE = {};
/**
 * Patching the Order class to add custom functionality.
 */
patch(FloorScreen.prototype, {
    /**
     * Add Mostrador logic
     */
    async addMostrador() {
        const activeFloorId = await this.orm.call("restaurant.floor", "get_restaurant_floor_para_llevar");
        let activeFloor = this.activeFloor;
        try {
            activeFloor = activeFloorId ? this.pos.floors_by_id[activeFloorId] : this.activeFloor;
        } catch {
            // noop
        }
        if (!activeFloor) { activeFloor = this.activeFloor; }
        this.selectFloor(activeFloor);
        const selectedTables = this.selectedTables;
        let table = null;
        if (selectedTables.length == 0) {
            const tables = activeFloor.tables;
            for (const activeTable of tables) {
                if (activeTable.order_count != 0) {
                    continue;
                }
                table = activeTable;
                break;
            }
        }
        if (!table) {
            // if not exists floor Para Llevar
            if (!activeFloorId) {
                const title = _t("Warning!");
                const body = _t("The number of usable tables has been exhausted.");
                this.popup.add(ErrorPopup, { title, body });
                return;
            }
            // create new table for this floor Para llevar
            const activeTableObject = await this.orm.call("restaurant.table", "create_active_table_from_floor", [activeFloorId]);
            // push new table to floor.
            this.state.selectedTableIds.push(activeTableObject.id);
            activeFloor.table_ids.push(activeTableObject.id);
            const tables = activeTableObject.newTable.floor.tables;
            for (const activeTable of tables) {
                if (activeTable.order_count != 0) {
                    continue;
                }
                table = activeTable;
                break;
            }
        }
        let order = null;
        // Setup POS ORDER.
        if (this.pos.isEditMode) {
            if (ev.ctrlKey || ev.metaKey) {
                this.state.selectedTableIds.push(table.id);
            } else {
                this.state.selectedTableIds = [];
                this.state.selectedTableIds.push(table.id);
            }
        } else {
            if (this.pos.orderToTransfer) {
                await this.pos.transferTable(table);
            } else {
                try {
                    await this.pos.setTable(table);
                } catch (e) {
                    if (!(e instanceof ConnectionLostError)) {
                        throw e;
                    }
                    // Reject error in a separate stack to display the offline popup, but continue the flow
                    Promise.reject(e);
                }
            }
            order = this.pos.get_order();
        }
        let { confirmed, payload: note } = await this.popup.add(TextInputPopup, {
            title: _t("Add note:"),
            startingValue: "",
            placeholder: _t("Enter your note"),
            cancelText: _t("Cancel"),
            confirmText: _t("Confirm"),
        });
        const partner = await this._getPartnerByClienteMostrador("Cliente Mostrador");
        order.set_partner(partner);
        if (confirmed) {
            note = note.trim();
            if (note !== "") {
                order.note = "Mostrador - " + note;
            } else {
                order.note = "Mostrador";
            }
            order.set_order_note(order.note);
            return this.pos.showScreen(order.get_screen_data().name);
        }
        return;
    },

    async _getPartnerByClienteMostrador(code) {
        let partner = this.pos.db.get_partner_by_barcode(code.code);
        if (!partner) {
            // find the partner in the backend by the barcode
            const foundPartnerIds = await this.orm.search("res.partner", [
                ["name", "=", code],
            ]);
            if (foundPartnerIds.length) {
                await this.pos._loadPartners(foundPartnerIds);
                // assume that the result is unique.
                partner = this.pos.db.get_partner_by_id(foundPartnerIds[0]);
            }
        }
        return partner;
    },

    load(store, deft) {
        if (CACHE[store] !== undefined) {
            return CACHE[store];
        }
        var data = localStorage[this.name + "_" + store];
        if (data !== undefined && data !== "") {
            data = JSON.parse(data);
            CACHE[store] = data;
            return data;
        } else {
            return deft;
        }
    },

    save(store, data) {
        localStorage[this.name + "_" + store] = JSON.stringify(data);
        CACHE[store] = data;
    },

    get_orders() {
        return this.load("orders", []);
    },

    get_order(order_id) {
        var orders = this.get_orders();
        for (var i = 0, len = orders.length; i < len; i++) {
            if (orders[i].id === order_id) {
                return orders[i];
            }
        }
        return undefined;
    },

    /**
     * Add Domicilio logic
     */
    async addDomicilio() {
        // FIXME, find order to refund when we are in the ticket-screen.
        const currentOrder = this.get_order();
        const ev = {"isTrusted": true}
        // .. SETUP FLOOR
        const activeFloorId = await this.orm.call("restaurant.floor", "get_restaurant_floor_para_llevar");
        let activeFloor = this.activeFloor;
        try {
            activeFloor = activeFloorId ? this.pos.floors_by_id[activeFloorId] : this.activeFloor;
        } catch {
            // noop
        }
        if (!activeFloor) { activeFloor = this.activeFloor; }
        this.selectFloor(activeFloor);
        // SETUP TABLE
        const selectedTables = this.selectedTables;
        let table = null;
        if (selectedTables.length == 0) {
            const tables = activeFloor.tables;
            for (const activeTable of tables) {
                if (activeTable.order_count != 0) {
                    continue;
                }
                table = activeTable;
                break;
            }
        }
        if (!table) {
            if (!activeFloorId) {
                const title = _t("Warning!");
                const body = _t("The number of usable tables has been exhausted.");
                this.popup.add(ErrorPopup, { title, body });
                return;
            }
            // create new table for this floor Para llevar
            const activeTableObject = await this.orm.call("restaurant.table", "create_active_table_from_floor", [activeFloorId]);
            // push new table to floor.
            this.state.selectedTableIds.push(activeTableObject.id);
            activeFloor.table_ids.push(activeTableObject.id);
            const tables = activeTableObject.newTable.floor.tables;
            for (const activeTable of tables) {
                if (activeTable.order_count != 0) {
                    continue;
                }
                table = activeTable;
                break;
            }
        }
        let order = null;
        // Setup POS ORDER.
        if (this.pos.isEditMode) {
            if (ev.ctrlKey || ev.metaKey) {
                this.state.selectedTableIds.push(table.id);
            } else {
                this.state.selectedTableIds = [];
                this.state.selectedTableIds.push(table.id);
            }
        } else {
            if (this.pos.orderToTransfer) {
                await this.pos.transferTable(table);
            } else {
                try {
                    await this.pos.setTable(table);
                } catch (e) {
                    if (!(e instanceof ConnectionLostError)) {
                        throw e;
                    }
                    // Reject error in a separate stack to display the offline popup, but continue the flow
                    Promise.reject(e);
                }
            }
            order = this.pos.get_order();
        }

        if (!order) { return; }

        let floorScreenUI = $('.floor-screen.screen');
        if (floorScreenUI.length >= 1) {
            floorScreenUI.addClass("d-none");
        }

        const { confirmed, payload: newPartner } = await this.pos.showTempScreen("PartnerListScreen");
        if (confirmed) {
            order.note = "Domicilio";
            order.set_partner(newPartner);
            return this.pos.showScreen(order.get_screen_data().name);
        } else {
            if (floorScreenUI.length >= 1) {
                floorScreenUI.removeClass("d-none");
            }
        }

        /*let { confirmed, payload: note } = await this.popup.add(TextInputPopup, {
            title: _t("Add note:"),
            startingValue: "",
            placeholder: _t("Enter your note"),
            cancelText: _t("Cancel"),
            confirmText: _t("Confirm"),
        });
        const partner = await this._getPartnerByClienteMostrador("Cliente Aplicaciones");
        order.set_partner(partner);
        if (confirmed) {
            note = note.trim();
            if (note !== "") {
                order.note = "Domicilio - " + note;
            } else {
                order.note = "Domicilio";
            }
            order.set_order_note(order.note);
            return this.pos.showScreen(order.get_screen_data().name);
        }*/
        return;
    },

    /**
     * Add Aplicaciones logic
     */
    async addAplicaciones() {
        const currentOrder = this.get_order();
        const ev = {"isTrusted": true}
        // .. SETUP FLOOR
        const activeFloorId = await this.orm.call("restaurant.floor", "get_restaurant_floor_para_llevar");
        let activeFloor = this.activeFloor;
        try {
            activeFloor = activeFloorId ? this.pos.floors_by_id[activeFloorId] : this.activeFloor;
        } catch {
            // noop
        }
        if (!activeFloor) { activeFloor = this.activeFloor; }
        this.selectFloor(activeFloor);
        const selectedTables = this.selectedTables;
        let table = null;
        if (selectedTables.length == 0) {
            const tables = this.activeFloor.tables;
            for (const activeTable of tables) {
                if (activeTable.order_count != 0) {
                    continue;
                }
                table = activeTable;
                break;
            }
        }
        if (!table) {
            if (!activeFloorId) {
                const title = _t("Warning!");
                const body = _t("The number of usable tables has been exhausted.");
                this.popup.add(ErrorPopup, { title, body });
                return;
            }
            // create new table for this floor Para llevar
            const activeTableObject = await this.orm.call("restaurant.table", "create_active_table_from_floor", [activeFloorId]);
            // push new table to floor.
            this.state.selectedTableIds.push(activeTableObject.id);
            activeFloor.table_ids.push(activeTableObject.id);
            const tables = activeTableObject.newTable.floor.tables;
            for (const activeTable of tables) {
                if (activeTable.order_count != 0) {
                    continue;
                }
                table = activeTable;
                break;
            }
        }
        let order = null;
        // Setup POS ORDER.
        if (this.pos.isEditMode) {
            if (ev.ctrlKey || ev.metaKey) {
                this.state.selectedTableIds.push(table.id);
            } else {
                this.state.selectedTableIds = [];
                this.state.selectedTableIds.push(table.id);
            }
        } else {
            if (this.pos.orderToTransfer) {
                await this.pos.transferTable(table);
            } else {
                try {
                    await this.pos.setTable(table);
                } catch (e) {
                    if (!(e instanceof ConnectionLostError)) {
                        throw e;
                    }
                    // Reject error in a separate stack to display the offline popup, but continue the flow
                    Promise.reject(e);
                }
            }
            order = this.pos.get_order();
        }
        const { is_confirmed, payload: isDelivery } = await this.pos.showTempScreen("MostradorConfirm");
        if (isDelivery) {
            // open form note
            let { confirmed, payload: note } = await this.popup.add(TextInputPopup, {
                title: _t("Add note:"),
                startingValue: "",
                placeholder: _t("Enter your note"),
                cancelText: _t("Cancel"),
                confirmText: _t("Confirm"),
            });
            let aplicacionesUber = "Cliente Uber";
            if (isDelivery == "DiDi") {
                aplicacionesUber = "Cliente DiDi";
            }
            if (isDelivery == "Rappi") {
                aplicacionesUber = "Cliente Rappi";
            }
            const partner = await this._getPartnerByClienteMostrador(aplicacionesUber);
            order.set_partner(partner);
            if (confirmed) {
                note = note.trim();
                if (note !== "") {
                    order.note = "Aplicaciones - " + isDelivery + " - " + note;
                } else {
                    order.note = "Aplicaciones - " + isDelivery;
                }
                order.set_order_note(order.note);
                return this.pos.showScreen(order.get_screen_data().name);
            }
            return;
        }
    }
});

patch(Order.prototype, {
    // Note: service_mostrador = this.pos.table_service_note
    // Note: note = this.note
    setup(_defaultObj, options) {
        super.setup(...arguments);
        this.note = this.pos.note || "";
    },

    //@override
    export_as_JSON() {
        const json = super.export_as_JSON(...arguments);
        json.note = this.note;
        return json;
    },

    //@override
    init_from_JSON(json) {
        super.init_from_JSON(...arguments);
        this.note = json.note;
    },

    set_order_note(note) {
        this.note = note;
    },

    get_order_note() {
        return this.note;
    },

    export_for_printing() {
        const result = super.export_for_printing(...arguments);
        const order = this.pos.get_order();
        result.headerData.note = this.get_order_note() || order.note || this.pos.note;
        return result;
    }
});
