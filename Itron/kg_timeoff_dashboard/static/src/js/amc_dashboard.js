/**@odoo-module **/
import { registry } from '@web/core/registry';
import { useService } from "@web/core/utils/hooks";
const { Component, onMounted } = owl;
import { _t } from "@web/core/l10n/translation";
import { useState } from "@odoo/owl";

export class AMCDashboard extends Component {
    setup() {
        this.action = useService("action");
        this.orm = useService("orm");
        this.rpc = useService("rpc");
        onMounted(this.onMounted.bind(this));
        this.state = useState({
            contracts: [],
            amc_contracts: [],
            results:{},
            selectedCustomerId: 0,
            selectedContractType:'',
            selectedStatusId:'done',
            StatusVals: [],
            customerss:[],
        });
    }

    async onMounted() {
        await this.render_dashboards();
    }

     updateStatusFilter(event) {
        this.state.selectedStatusId = event.target.value;
        this.updateFilterResult();
    }

    updateCustomerFilter(event) {
        this.state.selectedCustomerId = parseInt(event.target.value) || 0;
        this.updateFilterResult();
    }


    async render_dashboards() {
        const result = await this.orm.call('project.contract.request', 'contract_request', [[]]);
        this.state.contracts = result.amc_contracts;
        this.state.results = result.amc_contracts;
//        this.state.StatusVals = result.state_val;
        this.state.StatusVals = result.rebion_status_val;
        this.state.customerss = result.customerss || [];
        if (!this.state.StatusVals.find(s => s[0] === 'done')) {
        this.state.selectedStatusId = '';
        }else {
            this.state.selectedStatusId = 'done';
        }
        this.updateFilterResult();
    }
     async updateFilterResult() {
         const { results, selectedCustomerId, selectedStatusId} = this.state;
         let filtered = [...results];
         if (selectedCustomerId && selectedCustomerId !== 0) {
            filtered = filtered.filter(result => result.customer_id === selectedCustomerId);
         }
//         if (selectedStatusId && selectedStatusId !== '') {
//            filtered = filtered.filter(result => result.state_key === selectedStatusId);
//        }
         if (selectedStatusId && selectedStatusId !== '') {
                filtered = filtered.filter(result => result.rebion_status_key === selectedStatusId);
            }

         this.state.amc_contracts = filtered;
    }



    async tot_amc_contracts(e,oid) {
            e.stopPropagation();
            e.preventDefault();
            var options = {
                on_reverse_breadcrumb: this.on_reverse_breadcrumb,
            };

            for(var x  of this.state.amc_contracts){
                if(x['id'] == oid){
                    var amc_contracts = x['id'];
                }
            }
            this.action.doAction({
                name: _t("amc_contracts"),
                type: 'ir.actions.act_window',
                res_model: 'project.contract.request.amc',
                domain: [
                    ["id", "=", amc_contracts]
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

AMCDashboard.template = "AMCDashboard";
registry.category("actions").add("kg_amc_dashboard", AMCDashboard);
