/** @odoo-module **/
import { registry } from "@web/core/registry";
const actionRegistry = registry.category("actions");
import { useService } from "@web/core/utils/hooks";
import { Component, useState, onMounted } from "@odoo/owl";


class PendingApvDashboard extends Component {

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");

        this.state = useState({
            data: [],
            PendingApvData: [],
            approvers: [],
            selectedType: "",
            selectedApprover: "",
        });

        onMounted(() => {
            this.fetchPendingApvData();
        });
    }

    async fetchPendingApvData() {
        const result = await this.orm.call("account.move", "get_pending_approvals_data", [], {});
        this.state.data = result;
        this.state.PendingApvData = result;
        this.state.approvers = [...new Set(result.map(r => r.approver))];
    }

    openRecord(recordId) {
        this.action.doAction({
            type: 'ir.actions.act_window',
            res_model: 'account.move',
            name: 'Invoice/Bill',
            view_mode: 'form',
            view_type: 'form',
            views: [[false, 'form']],
            target: 'current',
            res_id: recordId,
        });
    }

    onTypeChange(ev) {
        this.state.selectedType = ev.target.value;
        this.applyFilters();
    }

    onApproverChange(ev) {
        this.state.selectedApprover = ev.target.value;
        this.applyFilters();
    }

    applyFilters() {
        this.state.PendingApvData = this.state.data.filter(record => {
            const typeMatch = this.state.selectedType ? record.move_type === this.state.selectedType : true;
            const approverMatch = this.state.selectedApprover ? record.approver === this.state.selectedApprover : true;
            return typeMatch && approverMatch;
        });
    }

    async approveData(recordId) {
        const result = await this.orm.call("account.move", "approve_data", [recordId], {});
        const record = this.state.PendingApvData.find(r => r.id === recordId);
        if (record) {
            record.state = 'Approved'
        }
    }

    async onExportClick(){
        const result = await this.orm.call("account.move", "export_approval_request_report", [], {});
        if (result && result.url) {
            window.open(result.url, "_blank");
        }
    }


    async rejectData(recordId) {
        this.action.doAction({
            type: 'ir.actions.act_window',
            res_model: 'reject.reason.wizard',
            name: 'Reject Reason',
            view_mode: 'form',
            view_type: 'form',
            views: [[false, 'form']],
            target: 'new',
            context: {'default_in_form': true, 'default_account_move_id': recordId}
        });
        const record = this.state.PendingApvData.find(r => r.id === recordId);
            if (record) {
                record.state = 'Rejected'
            }
    }

}

PendingApvDashboard.template = "kg_raw_fisheries_accounting.PendingApvDashboard";
actionRegistry.add("pending_apv_dashboard_tag", PendingApvDashboard);
