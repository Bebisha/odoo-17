/** @odoo-module **/

import { registry } from '@web/core/registry';
import { useService } from "@web/core/utils/hooks";
import { useState } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";

const { Component, onMounted } = owl;

export class TimesheetDashboard extends Component {
    setup() {
        // Services
        this.action = useService("action");
        this.orm = useService("orm");
        this.rpc = useService("rpc");

        // State
        this.state = useState({
            employeeData: [],
            companyData: [],
            teamData: [],
            selectedCompanyId: null,
            selectedTeamId: null,
            filteredEmployeeData: [],
            result: {},
        });

        // Method bindings
        onMounted(this.onMounted.bind(this));
        this.onCompanyChange = this.onCompanyChange.bind(this);
        this.onTeamChange = this.onTeamChange.bind(this);
        this.openEmployeeTimesheet = this.openEmployeeTimesheet.bind(this);
    }

    async onMounted() {
        await this.render_dashboards();
    }

    async render_dashboards(companyId = null, teamId = null) {
        try {
            companyId = parseInt(companyId) || null;
            teamId = parseInt(teamId) || null;

            const result = await this.orm.call(
                'account.analytic.line',
                'missing_timesheet',
                [companyId, teamId]
            );

            this.state.employeeData = result.missing_timesheets || [];
            this.state.companyData = result.company_data || [];
            this.state.teamData = result.team_data || [];

            if (!companyId) {
                this.state.selectedCompanyId = result.current_company_id || null;
            }

            this.filterEmployeeData();
        } catch (error) {
            console.error("Failed to load dashboard data:", error);
        }
    }

    filterEmployeeData() {
        this.state.filteredEmployeeData = this.state.employeeData.filter(employee => {
            const matchesCompany = this.state.selectedCompanyId
                ? employee.company_id === this.state.selectedCompanyId
                : true;
            const matchesTeam = this.state.selectedTeamId
                ? employee.team_id === this.state.selectedTeamId
                : true;
            return matchesCompany && matchesTeam;
        });
    }

    onCompanyChange(event) {
        this.state.selectedCompanyId = parseInt(event.target.value) || null;
        this.render_dashboards(this.state.selectedCompanyId, this.state.selectedTeamId);
    }

    onTeamChange(event) {
        this.state.selectedTeamId = parseInt(event.target.value) || null;
        this.render_dashboards(this.state.selectedCompanyId, this.state.selectedTeamId);
    }

    async openEmployeeTimesheet(e) {
        e.stopPropagation();
        e.preventDefault();

        const oid = parseInt(e.currentTarget.dataset.id);
        const employee = this.state.employeeData.find(x => x.id === oid);

        if (!employee || !employee.timesheets || !employee.timesheets.length) {
            return;
        }

        const options = {
            on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        };

        await this.action.doAction({
            name: _t("Timesheet"),
            type: 'ir.actions.act_window',
            res_model: 'account.analytic.line',
            domain: [["id", "in", employee.timesheets]],
            view_mode: 'tree',
            views: [[false, 'list']],
            target: 'current',
        }, options);
    }
}

TimesheetDashboard.template = "TimesheetDashboard";
registry.category("actions").add("account_analytic_dashboard", TimesheetDashboard);
