/** @odoo-module */

import { registry } from "@web/core/registry";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { Component } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";

import { NumberPopup } from "@point_of_sale/app/utils/input_popups/number_popup";
import { SelectionPopup } from "@point_of_sale/app/utils/input_popups/selection_popup";
import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";
import { useService } from "@web/core/utils/hooks";


export function useMostradorSelector(
    { onMostradorChanged, exclusive } = { onMostradorChanged: () => {}, exclusive: false }
) {
    const popup = useService("popup");
    const pos = usePos();

    /**
     * Select a cashier, the returning value will either be an object or nothing (undefined)
     */
    return async function selectUBER() {
        pos.isUber = true;
        pos.isDiDi = false;
        pos.isRappi = false;
    };

    return async function selectDIDI() {
        pos.isDiDi = true;
        pos.isUber = false;
        pos.isRappi = false;
    };

    return async function selectRAPPI() {
        pos.isRappi = true;
        pos.isDiDi = false;
        pos.isUber = false;
    };
}


export class MostradorConfirm extends Component {
    static template = "tm_pos.MostradorConfirm";

    setup() {
        super.setup(...arguments);
        this.pos = usePos();
        this.currentPos = this.pos.get_order();
        this.selectAplicaciones = useMostradorSelector({
            onMostradorChanged: () => this.back(),
            exclusive: true, // takes exclusive control on the barcode reader
        });
        this.isUber = null;
        this.isDiDi = null;
        this.isRappi = null;
    }

    back() {
        this.props.resolve({ confirmed: false, payload: false });
        this.pos.closeTempScreen();
        this.pos.selectAplicaciones = this.selectAplicaciones;
        this.pos.openCashControl();
    }

    async selectUBER() {
        this.isUber = true;
        this.isDiDi = false;
        this.isRappi = false;
        this.confirm();
    };

    async selectDIDI() {
        this.isDiDi = true;
        this.isUber = false;
        this.isRappi = false;
        this.confirm();
    };

    async selectRAPPI() {
        this.isRappi = true;
        this.isDiDi = false;
        this.isUber = false;
        this.confirm();
    };

    get shopName() {
        return this.pos.config.name;
    }

    confirm() {
        let isDelivery = this.isDiDi && "DiDi" || null;
        if (!isDelivery) {
            isDelivery = this.isUber && "Uber" || null;
        }
        if (!isDelivery) {
            isDelivery = this.isRappi && "Rappi" || null;
        }
        this.props.resolve({ confirmed: true, payload: isDelivery });
        this.pos.closeTempScreen();
    }
}

registry.category("pos_screens").add("MostradorConfirm", MostradorConfirm);