/** @odoo-module */
import { registry } from '@web/core/registry';
import { useService } from "@web/core/utils/hooks";
const { Component, onMounted } = owl;
import { jsonrpc } from "@web/core/network/rpc_service";
import { _t } from "@web/core/l10n/translation";
import { useState } from "@odoo/owl";


export class InventoryValuationDashboard extends Component {
    setup() {
        this.action = useService("action");
        this.notification = useService("notification");
        this.orm = useService("orm");
        this.rpc = useService("rpc");
        onMounted(this.onMounted.bind(this));
        this.state = useState({
            allResults: [],
            result: [],
            companies: [],
            selectedCompanyId: null,
        });
    }

    async onMounted() {
        await this.render_material_waiting_datas();
    }

    async render_material_waiting_datas() {
        const result = await this.orm.call('stock.quant', 'get_stock_count', [[]]);
        this.state.allResults = result['requests'];
        this.state.result = result['requests'];
        this.state.companies = result['companies'];
    }

    onCompanyChange(event) {
        const selectedCompanyId = event.target.value;
        this.state.selectedCompanyId = selectedCompanyId;

        if (selectedCompanyId) {
            this.state.result = this.state.allResults.filter(leave => {
                const leaveCompanyId = String(leave.company_id);
                return leaveCompanyId === selectedCompanyId;
            });
        } else {
            this.state.result = [...this.state.allResults];
        }
    }


   async onclick_valuation(event, inventoryId) {
        event.stopPropagation();
        event.preventDefault();

        // Open the material request form view
        this.action.doAction({
            name: _t("Inventory"),
            type: 'ir.actions.act_window',
            res_model: 'stock.quant',
            res_id: inventoryId,
            view_mode: 'form',
            views: [
                [false, 'form'],
            ],
            target: 'current',
        });
    }

}

InventoryValuationDashboard.template = "InventoryValuationDashboard";
registry.category("actions").add("valuation_dashboard_tag", InventoryValuationDashboard);
