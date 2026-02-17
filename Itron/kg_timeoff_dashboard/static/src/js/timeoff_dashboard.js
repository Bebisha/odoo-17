/** @odoo-module */
import { registry } from '@web/core/registry';
import { useService } from "@web/core/utils/hooks";
import { Component, useState } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";

export class LeavesDashboard extends Component {
    setup() {
        this.orm = useService("orm");
        this.action = useService("action");

        this.state = useState({
            employeeData: [],
            companyData: [],
            selectedCompanyId: null,  // New state for selected company ID
            filteredEmployeeData: [], // New state for filtered employee data
        });
        this.loadEmployeeData();

    }

    async loadEmployeeData() {
        try {

            const result = await this.orm.call('hr.employee', 'get_employee_leave_data', []);

            this.state.employeeData = result.employee_data || [];
            this.state.companyData = result.company_data || [];
            this.state.selectedCompanyId = result.current_company_id || null;
            this.filterEmployeeData(); // Filter the employee data initially
        } catch (error) {
            console.error("Failed to fetch employee data", error);
        }
    }

    filterEmployeeData() {
        // Filter employee data based on selected company
        this.state.filteredEmployeeData = this.state.selectedCompanyId
            ? this.state.employeeData.filter(employee => employee.company_id === this.state.selectedCompanyId)
            : this.state.employeeData;
    }

    onCompanyChange(event) {
        // Update the selected company ID and filter employee data
        this.state.selectedCompanyId = parseInt(event.target.value) || null;
        this.filterEmployeeData();
    }
    async tot_sick(e,oid) {
        e.stopPropagation();
        e.preventDefault();
        var options = {
            on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        };
//    const result = await this.orm.call('hr.employee', 'missing_timesheet', [[]]);
        for(var x  of this.state.employeeData){
            if(x['id'] == oid){
                var leaves = x['leaves']['sick'];
            }
        }
        this.action.doAction({
            name: _t("Sick Leave"),
            type: 'ir.actions.act_window',
            res_model: 'hr.leave',
            domain: [
                ["id", "in", leaves]
            ],
            view_mode: 'tree,form',
            views: [
                [false, 'list'],
                [false, 'form']
            ],
            target: 'current'
        }, options);
    }
    async tot_casual(e,oid) {
        e.stopPropagation();
        e.preventDefault();
        var options = {
            on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        };
//    const result = await this.orm.call('hr.employee', 'missing_timesheet', [[]]);
        for(var x  of this.state.employeeData){
            if(x['id'] == oid){
                var leaves = x['leaves']['casual'];
            }
        }
        this.action.doAction({
            name: _t("Casual Leave"),
            type: 'ir.actions.act_window',
            res_model: 'hr.leave',
            domain: [
                ["id", "in", leaves]
            ],
            view_mode: 'tree,form',
            views: [
                [false, 'list'],
                [false, 'form']
            ],
            target: 'current'
        }, options);
    }
    async tot_unpaid(e,oid) {
        e.stopPropagation();
        e.preventDefault();
        var options = {
            on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        };
        for(var x  of this.state.employeeData){
            if(x['id'] == oid){
                var leaves = x['leaves']['unpaid'];
            }
        }
        this.action.doAction({
            name: _t("Unpaid Leave"),
            type: 'ir.actions.act_window',
            res_model: 'hr.leave',
            domain: [
                ["id", "in", leaves]
            ],
            view_mode: 'tree,form',
            views: [
                [false, 'list'],
                [false, 'form']
            ],
            target: 'current'
        }, options);
    }
}

LeavesDashboard.template = "LeavesDashboard";
registry.category("actions").add("leaves_dashboard", LeavesDashboard);
