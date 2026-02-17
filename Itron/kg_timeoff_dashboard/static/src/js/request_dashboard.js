/** @odoo-module **/
import { registry } from '@web/core/registry';
import { useService } from "@web/core/utils/hooks";
const { Component, onMounted } = owl;
import { _t } from "@web/core/l10n/translation";
import { useState } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";



export class RequestDashboard extends Component {
    setup() {
        this.action = useService("action");
        this.orm = useService("orm");
        this.rpc = useService("rpc");
        this.notification = useService("notification");
        this.dialogService = useService("dialog");
        onMounted(this.onMounted.bind(this));

        this.state = useState({
            allResults: [],
            result: [],
            companies: [],
            selectedCompanyId: null,
            selectedDateFilter : "today",
            StatusVals: [],
            selectedStatusId: '',
        });
    }
    async onMounted() {
        await this.loadDashboardData();
    }

    async loadDashboardData() {
        try {
            const params = this.state.selectedCompanyId ? [this.state.selectedCompanyId] : [];
            const result = await this.orm.call('project.resource.pool', 'resource_request_dashboard', [params]);
            this.state.allResults = result['resource_requests'];
            this.state.result = result['resource_requests'];
            this.state.companies = result['companies'];
            this.state.StatusVals = result.status;
            this.applyDateFilter();

        } catch (error) {
            console.error("Error loading dashboard data:", error);
            this.notification.add(_t("Failed to load dashboard data."), { type: "danger" });
        }
    }

    onCompanyChange(event) {
        const selectedCompanyId = event.target.value;
        this.state.selectedCompanyId = selectedCompanyId;

        if (selectedCompanyId) {
            this.state.result = this.state.allResults.filter(resource => {
                const resourceCompanyId = String(resource.company_id);
                return resourceCompanyId === selectedCompanyId;
            });
        } else {
            this.state.result = [...this.state.allResults];
        }
    }

    applyDateFilter() {
        const filter = this.state.selectedDateFilter;
        const now = new Date();
        const todayStr = now.toISOString().split("T")[0];

        const startOfWeek = new Date(now);
        startOfWeek.setDate(now.getDate() - now.getDay());
        const endOfWeek = new Date(startOfWeek);
        endOfWeek.setDate(startOfWeek.getDate() + 6);

        const startOfMonth = new Date(now.getFullYear(), now.getMonth(), 1);
        const endOfMonth = new Date(now.getFullYear(), now.getMonth() + 1, 0);

        const normalizeDate = (dateStr) => new Date(dateStr).toISOString().split("T")[0];

        let filtered = [...this.state.allResults];

        if (filter === "today") {
            filtered = filtered.filter(item =>
                item.start_date && normalizeDate(item.start_date) === todayStr
            );
        } else if (filter === "this_week") {
            const startOfWeekStr = startOfWeek.toISOString().split("T")[0];
            const endOfWeekStr = endOfWeek.toISOString().split("T")[0];
            filtered = filtered.filter(item =>
                item.start_date && normalizeDate(item.start_date) >= startOfWeekStr &&
                normalizeDate(item.start_date) <= endOfWeekStr
            );
        } else if (filter === "this_month") {
            const startOfMonthStr = startOfMonth.toISOString().split("T")[0];
            const endOfMonthStr = endOfMonth.toISOString().split("T")[0];
            filtered = filtered.filter(item =>
                item.start_date && normalizeDate(item.start_date) >= startOfMonthStr &&
                normalizeDate(item.start_date) <= endOfMonthStr
            );
        }

        // Company filter
        if (this.state.selectedCompanyId) {
            filtered = filtered.filter(resource =>
                String(resource.company_id) === this.state.selectedCompanyId
            );
        }
        if (this.state.selectedStatusId && this.state.selectedStatusId !== '') {
            filtered = filtered.filter(result => result.status_key === this.state.selectedStatusId);
        }

        this.state.result = filtered;
    }

    onDateChange(event){
        const filter = event.target.value;
        this.state.selectedDateFilter = filter;
        this.applyDateFilter();
    }


    updateStatusFilter(event){
        console.log("SSSSSSSs", event.target.value);
        this.state.selectedStatusId = event.target.value
        this.applyDateFilter();
    }

    async approveRequestResource(event, rid) {
        event.stopPropagation();
        event.preventDefault();

        try {
            const result = await this.orm.call("project.resource.pool", "button_approve", [rid]);
            window.location.reload();

        } catch (error) {
            console.error("Error approving the request:", error);
            alert("An error occurred while approving the request.");
        }
    }

    async rejectRequestResource(event, rid) {
        event.stopPropagation();
        event.preventDefault();
        const action = await this.orm.call(
            'project.resource.pool',
            'button_reject',
            [rid],
            { context: { from_dashboard: true } }
        );
        if (action) {
            this.action.doAction(action);
        } else {
            this.env.services.action.doAction({ type: 'ir.actions.client', tag: 'reload' });
        }
    }

    async onRefNoClicknw(event, oid) {
        event.stopPropagation();
        event.preventDefault();
        let domain = [["id", "=", oid]];
        this.action.doAction({
            name: _t("Resource Request"),
            type: 'ir.actions.act_window',
            res_model: 'project.resource.pool',
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
RequestDashboard.template = "RequestDashboard";
registry.category("actions").add("request_dashboard", RequestDashboard);