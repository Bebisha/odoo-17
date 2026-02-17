/** @odoo-module */
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, useState, onMounted } from "@odoo/owl";
const actionRegistry = registry.category("actions");

class VesselRevenueDashboard extends Component {
    setup() {
        this.orm = useService("orm");
        this.state = useState({
            data: [],
            filteredData: [],
            vessels: [],
        });

        onMounted(() => {
            this.fetchInventoryData();
        });
    }

    async fetchInventoryData() {
        const result = await this.orm.call("sale.order", "get_vessel_revenue_data", [], {});
        this.state.data = result;
        this.state.filteredData = result;
        this.state.vessels = [...new Set(result.map(r => r.vessel))];

    }

    onVesselChange(ev) {
        const selectedVessel = ev.target.value;
        if (selectedVessel) {
            this.state.filteredData = this.state.data.filter(r => r.vessel === selectedVessel);
        } else {
            this.state.filteredData = this.state.data;
        }
    }
}

VesselRevenueDashboard.template = "kg_raw_fisheries_dashboard.VesselRevenueTemplate"
registry.category("actions").add("vessel_revenue_dashboard", VesselRevenueDashboard)
