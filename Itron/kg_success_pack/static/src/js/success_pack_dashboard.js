/** @odoo-module */
import { registry } from '@web/core/registry';
import { useService } from "@web/core/utils/hooks";
const { Component, onMounted } = owl;
import { jsonrpc } from "@web/core/network/rpc_service";
import { _t } from "@web/core/l10n/translation";
import { useState } from "@odoo/owl";


export class SuccessPackDashboard extends Component {
    setup() {
        this.action = useService("action");
        this.orm = useService("orm");
        this.rpc = useService("rpc");
        onMounted(this.onMounted);
        this.state = useState({
            results:{},
            selectedCompanyId:0,
            is_admin:0,
            companies:[],
            projects: [],
            packages: [],
            customers: [],
            status: [],
            filteredResult:[],
            startDate: null,
            endDate: null,
        });
    }

    async onMounted() {
        this.render_success_pack();
    }


     async render_success_pack() {
        const results = await this.orm.call('pack.projects', 'get_success_pack_line_data',[[]]);
        console.log("results.projects",results.projects)
        this.state.results = results.vals;
        this.state.companies = results.company_data;
        this.state.projects = results.projects;
        this.state.packages = results.packages;
        this.state.customers = results.customers;
        this.state.is_admin = results.is_admin;
        this.state.status = results.status;
//        if (!this.state.is_admin){
//            this.state.selectedCompanyId = results.company_data[0]['id']
//        }
        this.filterEmployees();

    }
     async FilterCompanytasks(event) {
        const selectedCompanyId = event.target.value;
        this.state.selectedCompanyId = parseInt(selectedCompanyId) || null;
        this.filterEmployees();
        }

     async updateSuccessByStartDate(event) {
        const selectedStartDate = event.target.value;
        this.state.startDate = selectedStartDate;
        this.filterEmployees();
    }

    updateSuccessEndDate(event) {
            this.state.endDate = event.target.value || null;
            this.filterEmployees();
    }
    updateProjectFilter(event) {
        this.state.selectedProjectId = parseInt(event.target.value) || 0;
        this.filterEmployees();
    }
    updatePackFilter(event) {
        this.state.selectedPackId = parseInt(event.target.value) || 0;
        this.filterEmployees();
    }
     updateCustomerFilter(event) {
        this.state.selectedCustomerId = parseInt(event.target.value) || 0;
        this.filterEmployees();
    }
    updateStatusFilter(event) {
        this.state.selectedStatus = event.target.value || 0;
        this.filterEmployees();
    }

    filterEmployees() {
        const { selectedCompanyId, selectedProjectId,selectedPackId, selectedCustomerId, startDate, endDate, results ,selectedStatus} = this.state;
        let filtered = [...results];

        const parseDMY = (dateStr) => {
            if (!dateStr) return null;
            const [day, month, year] = dateStr.split('/');
            return new Date(year, month - 1, day);
        };
            if (selectedCompanyId) {
            filtered = filtered.filter(result => result.company_id === selectedCompanyId);
        }
        if (selectedCustomerId) {
            filtered = filtered.filter(result => result.partner_id === selectedCustomerId);
        }
        if (selectedProjectId) {
            filtered = filtered.filter(result => result.project_id === selectedProjectId);
        }
        if (selectedPackId) {
            filtered = filtered.filter(result => result.pack_id === selectedPackId);
        }
        if (selectedStatus) {
            filtered = filtered.filter(result => result.status === selectedStatus);
        }
            if (startDate) {
            const filterStart = new Date(startDate);
            filterStart.setHours(0, 0, 0, 0);
            filtered = filtered.filter(result => {
                const resultStart = parseDMY(result.start_date);
                return resultStart && resultStart >= filterStart;
            });
        }

        if (endDate) {
            const filterEnd = new Date(endDate);
            filterEnd.setHours(23, 59, 59, 999);
            filtered = filtered.filter(result => {
                const resultEnd = parseDMY(result.end_date);
                return resultEnd && resultEnd <= filterEnd;
            });
        }

        filtered = filtered.map((result, index) => ({
            ...result,
            id: result.project_id || index,
        }));

        this.state.filteredResult = filtered;
        console.log("gggggggggggggggggggggggggg",filtered)
    }

     async onViewTimesheet(e,oid) {
     console.log("vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv",oid.project_id);

        this.action.doAction({
             type: "ir.actions.act_window",
             name: "Time sheet",
             res_model: "account.analytic.line",
             view_mode: "tree",
            domain: [
            ['project_id', '=', oid.project_id],
            ['date', '>=', oid.start_date],
            ['date', '<=', oid.end_date],
            ['task_id.success_pack_id', '=', oid.pack_id]
            ],
             views: [[false, "tree"], [false, "form"]],
             target: "current",
       });
     }
    async onViewHours(e,oid) {
    console.log("jjjjjjjjjjjjjjjjjjjjj",oid.id);
        const action = await this.orm.call('pack.projects', 'action_view_timesheet', [oid.id]);
        console.log("jjjjjjjjjjjjjjnnnnnnnnnnnnnnnnn",action)
         this.action.doAction(action);
    }

    async onDownloadTimesheet(e,oid) {
        const action = await this.orm.call('pack.projects', 'action_print_pdf', [oid.id]);
        console.log("action", action)
        this.action.doAction(action);

    }
}

SuccessPackDashboard.template = "SuccessPackDashboard";
registry.category("actions").add("success_pack_dashboard", SuccessPackDashboard);
