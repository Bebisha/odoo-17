/**@odoo-module **/
import { registry } from '@web/core/registry';
import { useService } from "@web/core/utils/hooks";
const { Component, onMounted } = owl;
import { _t } from "@web/core/l10n/translation";
import { useState } from "@odoo/owl";

export class WaitingDashboard extends Component {
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
        await this.render_waiting_dashboards();
    }

    async render_waiting_dashboards() {
        const result = await this.orm.call('hr.leave', 'get_values', [[]]);
        this.state.allResults = result['leaves'];
        this.state.result = result['leaves'];
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
        const result = await this.orm.call('hr.leave', 'action_approve', [[record.id]]);
        window.location.reload();
        }catch (error) {
            console.error("Error approving the request:", error);
            alert("Please select the Employee's Company for approval.");
        }
    }

     async handleSecondApproveRecord(record) {
      try {
      const hasApprovalAccess = await this.orm.call('hr.leave', 'check_qualified_for_second_approver', [record.id]);

//    if (!hasApprovalAccess) {
//        this.notification.add("You do not have permission to approve this request.", {
//                type: "warning",
//                title: "Access Denied",
//            });
//            return;
//    }
        const result = await this.orm.call('hr.leave', 'action_validate', [[record.id]]);
        window.location.reload();
         }catch (error) {
            console.error("Error approving the request:", error);
            alert("Please select the Employee's Company for approval.");
        }
    }

     async handleRejectRecord(record) {
     try{
//      if (record.state === 'Second Approval') {
//         const hasApprovalAccess = await this.orm.call('hr.leave', 'check_qualified_for_second_approver', [record.sudo().id]);
//
//    if (!hasApprovalAccess) {
//        this.notification.add("You do not have permission to reject this request.", {
//                type: "warning",
//                title: "Access Denied",
//            });
//            return;
//    }
//    }
        const result = await this.orm.call('hr.leave', 'action_refuse', [[record.id]]);
        window.location.reload();
         }catch (error) {
            console.error("Error approving the request:", error);
            alert("Please select the Employee's Company for approval.");
        }
    }

    async onclick_leaves(event, oid, type) {
        event.stopPropagation();
        event.preventDefault();
        let domain = [];

        if (type === "leave") {
            domain = [["id", "=", oid]];
        } else if (type === "employee") {
            const selectedLeave = this.state.result.find(x => x.id === oid);
            if (selectedLeave) {
                domain = [["id", "in", selectedLeave.leaves]];
            }
        }

        this.action.doAction({
            name: _t("Leaves"),
            type: 'ir.actions.act_window',
            res_model: 'hr.leave',
            domain: domain,
            view_mode: 'tree,form',
            views: [
                [false, 'list'],
                [false, 'form'],
            ],
            target: 'current',
        }, {
            on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        });
    }
}

WaitingDashboard.template = "WaitingApprovalDashboard";
registry.category("actions").add("Waiting_approval_dashboard", WaitingDashboard);
