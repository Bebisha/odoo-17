/**@odoo-module **/
import { registry } from '@web/core/registry';
import { useService } from "@web/core/utils/hooks";
const { Component, onMounted } = owl;
import { _t } from "@web/core/l10n/translation";
import { useState } from "@odoo/owl";

export class ContractOrderDashboard extends Component {
    setup() {
        this.action = useService("action");
        this.orm = useService("orm");
        this.rpc = useService("rpc");
        onMounted(this.onMounted.bind(this));
        this.state = useState({
            results: {},
            customers: [],
            contracts: [],
            contract_order: [],
            projects: [],
            contractTypes: [],  // Will store available contract types
            selectedContractType: '',
            startDate: null,
            selectedCustomerId: 0,
            selectedProjectId: 0,
        });
    }

    async onMounted() {
        await this.render_dashboards();
    }

//    async filterByStartDate(event) {
//        const selectedStartDate = event.target.value;
//        this.state.startDate = selectedStartDate;
//        this.updateFilterResult();
//    }
    filterByStartDate(event) {
            this.state.startDate = event.target.value || null;
            this.updateFilterResult();
    }
    updateSuccessEndDate(event) {
            this.state.endDate = event.target.value || null;
            this.updateFilterResult();
    }

    updateProjectFilter(event) {
        this.state.selectedProjectId = parseInt(event.target.value) || 0;
        this.updateFilterResult();
    }

    updateCustomerFilter(event) {
        this.state.selectedCustomerId = parseInt(event.target.value) || 0;
        this.updateFilterResult();
    }
    updateContractTypeFilter(event) {
        this.state.selectedContractType = event.target.value;
        this.updateFilterResult();
    }

    async render_dashboards() {
        const results = await this.orm.call('sale.order', 'get_contract_order_data', [[]]);
        this.state.results = results.contract_order_data;
        this.state.contracts = results.contracts;
        this.state.customers = results.customers;
        this.state.projects = results.projects; // Fixed typo (was missing this line)
        this.state.contractTypes = results.contract_types || [];
        this.state.contract_order = results.contract_order_data;
        this.updateFilterResult();
    }

    async updateFilterResult() {
        const { results, selectedCustomerId, selectedProjectId,selectedContractType,startDate,endDate} = this.state;
        let filtered = [...results];
        const parseDMY = (dateStr) => {
            if (!dateStr) return null;
            const [day, month, year] = dateStr.split('/');
            return new Date(year, month - 1, day);
        };

        if (startDate) {
            const filterStart = new Date(startDate);
            filterStart.setHours(0, 0, 0, 0);
            filtered = filtered.filter(result => {
                const resultStart = parseDMY(result.date_start);
                return resultStart && resultStart >= filterStart;
            });
        }
        if (endDate) {
            const filterEnd = new Date(endDate);
            filterEnd.setHours(0, 0, 0, 0);
            filtered = filtered.filter(result => {
                const resultEnd = parseDMY(result.date_end);
                return resultEnd && resultEnd <= filterEnd;
            });
        }

        // Apply customer filter
        if (selectedCustomerId) {
            filtered = filtered.filter(result => {
                const customer = this.state.customers.find(c => c.id === selectedCustomerId);
                return customer && result.customers === customer.name;
            });
        }

        // Apply project filter
        if (selectedProjectId) {
            filtered = filtered.filter(result => {
                const project = this.state.projects.find(p => p.id === selectedProjectId);
                return project && result.project_id === project.name;
            });
        }

       if (selectedContractType) {
        filtered = filtered.filter(result => {
            return result.contract_type_key === selectedContractType;
        });
    }

        this.state.contract_order = filtered;
    }

    async show_contracts(e, oid) {
        e.stopPropagation();
        e.preventDefault();
        var options = {
            on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        };
        for(var x of this.state.contract_order){
            if(x['id'] == oid){
                var contract_order = x['id'];
            }
        }
        this.action.doAction({
            name: _t("contract_order"),
            type: 'ir.actions.act_window',
            res_model: 'sale.order',
            domain: [
                ["id", "=", contract_order]
            ],
            view_mode: 'tree,form',
            views: [
                [false, 'list'],
                [false, 'form'],
            ],
            target: 'current'
        }, options);
    }
}
ContractOrderDashboard.template = "ContractOrderDashboard";
registry.category("actions").add("kg_contract_order_dashboard_tag", ContractOrderDashboard);