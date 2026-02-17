/** @odoo-module */
import { registry } from '@web/core/registry';
import { useService } from "@web/core/utils/hooks";
const { Component, onMounted } = owl;
import { jsonrpc } from "@web/core/network/rpc_service";
import { _t } from "@web/core/l10n/translation";
import { useState } from "@odoo/owl";


export class MaterialRequestDashboard extends Component {
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
        const result = await this.orm.call('kg.material.request', 'get_material_values', [[]]);
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

    async handleApproveRecord(record) {
        try {
            console.log("Approving record:", record);

            // Show loading notification
            const loadingNotification = this.notification.add("Processing approval...", {
                type: "info",
                title: "Please wait",
            });

            // Call the approve method from the backend
            const result = await this.orm.call('kg.material.request', 'action_approve_button', [[record.id]]);

            console.log("Approval result:", result);

            // Clear loading notification
            if (loadingNotification && loadingNotification.close) {
                loadingNotification.close();
            }

            // Show success notification
            this.notification.add("Material request approved successfully!", {
                type: "success",
                title: "Approved",
            });

            // Refresh the dashboard data
            await this.render_material_waiting_datas();

        } catch (error) {
            console.error("Error approving the request:", error);
            console.error("Error details:", error.message);
            console.error("Error data:", error.data);

            // Show detailed error notification
            let errorMessage = "Failed to approve the request. Please try again.";
            if (error.data && error.data.message) {
                errorMessage = error.data.message;
            } else if (error.message) {
                errorMessage = error.message;
            }

            this.notification.add(errorMessage, {
                type: "danger",
                title: "Error",
            });
        }
    }
//     async handleRejectRecord(record) {

      async handleRejectRecord(record) {
//        event.stopPropagation();
//        event.preventDefault();
        console.log('rid',record)
        const action = {
        type: 'ir.actions.act_window',
        res_model: 'rejects.reason.wizard',
        views: [[false, 'form']],
        view_mode: 'form',
        target: 'new',
        context: { from_dashboard: true, default_material_id: record.id },
    };
         this.action.doAction(action).then(() => {
        // Only reload after modal is closed (submitted or cancelled)
    });

   }




   async onclick_material_request(event, requestId) {
        event.stopPropagation();
        event.preventDefault();

        // Open the material request form view
        this.action.doAction({
            name: _t("Material Request"),
            type: 'ir.actions.act_window',
            res_model: 'kg.material.request',
            res_id: requestId,
            view_mode: 'form',
            views: [
                [false, 'form'],
            ],
            target: 'current',
        });
    }

}

MaterialRequestDashboard.template = "MaterialRequestDashboard";
registry.category("actions").add("material_dashboard_tag", MaterialRequestDashboard);
