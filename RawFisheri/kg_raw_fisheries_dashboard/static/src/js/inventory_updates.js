/** @odoo-module **/
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, useState, onMounted } from "@odoo/owl";

const actionRegistry = registry.category("actions");

class InventoryUpdatesDashboard extends Component {
    setup() {
        this.orm = useService("orm");

        this.state = useState({
            data: [],
            filteredData: [],
            vessels: [],
            batches: [],
            sortField: null,
            sortAsc: true,
        });

        onMounted(() => {
            this.fetchInventoryData();
        });
    }

    async fetchInventoryData() {
        const result = await this.orm.call("inventory.update", "get_inventory_update_data", [], {});
        this.state.data = result;
        this.state.filteredData = [...result];
        this.state.vessels = [...new Set(result.map(r => r.vessel))];
        this.state.batches = [...new Set(result.map(r => r.batch_id))];
    }

    applyFilters() {
        let filtered = this.state.data;

        const selectedVessel = this.state.selectedVessel;
        const selectedBatch = this.state.selectedBatch;

        if (selectedVessel) {
            filtered = filtered.filter(r => r.vessel === selectedVessel);
        }

        if (selectedBatch) {
            filtered = filtered.filter(r => r.batch_id === selectedBatch);
        }

        this.state.filteredData = [...filtered];

        if (this.state.sortField) {
            this.sortBy(this.state.sortField, true);
        }
    }

    onVesselChange(ev) {
        this.state.selectedVessel = ev.target.value;
        this.applyFilters();
    }

    onBatchChange(ev) {
        this.state.selectedBatch = ev.target.value;
        this.applyFilters();
    }


    sortBy(field, preserveOrder = false) {
        if (!preserveOrder) {
            if (this.state.sortField === field) {
                this.state.sortAsc = !this.state.sortAsc;
            } else {
                this.state.sortField = field;
                this.state.sortAsc = true;
            }
        }

        const sortAsc = this.state.sortAsc;
        const sorted = [...this.state.filteredData].sort((a, b) => {
            let valA = a[field];
            let valB = b[field];

            if (valA == null) return 1;
            if (valB == null) return -1;

            if (typeof valA === "string") {
                return sortAsc ? valA.localeCompare(valB) : valB.localeCompare(valA);
            }

            return sortAsc ? valA - valB : valB - valA;
        });

        this.state.filteredData = sorted;
    }
}

InventoryUpdatesDashboard.template = "kg_raw_fisheries_dashboard.InventoryUpdatesTemplate";
actionRegistry.add("inventory_updates_dashboard", InventoryUpdatesDashboard);






///** @odoo-module **/
//import { registry } from "@web/core/registry";
//import { useService } from "@web/core/utils/hooks";
//import { Component, useState, onMounted } from "@odoo/owl";
//const actionRegistry = registry.category("actions");
//
//class InventoryUpdatesDashboard extends Component {
//    setup() {
//        this.orm = useService("orm");
//        this.state = useState({
//            data: [],
//            filteredData: [],
//            vessels: [],
//
//        });
//
//        onMounted(() => {
//            this.fetchInventoryData();
//        });
//    }
//
//    async fetchInventoryData() {
//        const result = await this.orm.call("inventory.update", "get_inventory_update_data", [], {});
//        this.state.data = result;
//        this.state.filteredData = result;
//        this.state.vessels = [...new Set(result.map(r => r.vessel))];
//    }
//
//    onVesselChange(ev) {
//        const selectedVessel = ev.target.value;
//        if (selectedVessel) {
//            this.state.filteredData = this.state.data.filter(r => r.vessel === selectedVessel);
//        } else {
//            this.state.filteredData = this.state.data;
//        }
//    }
//}
//
//InventoryUpdatesDashboard.template = "kg_raw_fisheries_dashboard.InventoryUpdatesTemplate";
//actionRegistry.add("inventory_updates_dashboard", InventoryUpdatesDashboard);
