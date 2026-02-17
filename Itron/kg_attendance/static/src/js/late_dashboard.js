/** @odoo-module */
import { registry } from '@web/core/registry';
import { useService } from "@web/core/utils/hooks";
import { Component, useState } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";


export class LateComingDashboard extends Component {
    setup() {
        this.orm = useService("orm");
        this.action = useService("action");

        this.state = useState({
            employees: [],
            companies: [],
            selectedCompanyId: null,
            filteredEmployees: [],
            tree_view:0
        });

        this.loadEmployeeData();
    }

    async loadEmployeeData() {
        try {
            const result = await this.orm.call("kg.attendance", "get_values", []);
            this.state.employees = result.employees || [];
            this.state.companies = result.companies || [];
            this.state.tree_view = result.tree_view || [];
            this.state.selectedCompanyId = result.current_company_id || null; // Default company selection
            this.filterEmployees(); // Apply initial filter
            console.log("Employee Data:", this.state);
            console.log("Company Data:", this.state.companies);
        } catch (error) {
            console.error("Failed to fetch attendance data", error);
        }
    }
    async tot_late(e,oid) {
        e.stopPropagation();
        e.preventDefault();
        var options = {
            on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        };

        for(var x  of this.state.employees){
            if(x['id'] == oid){
                var task_ids = x['late']['total_late'];
            }
        }
        this.action.doAction({
            name: _t("Total Late Arrival"),
            type: 'ir.actions.act_window',
            res_model: 'early.late.request',
            domain: [
                ["id", "in", task_ids]
            ],
            view_mode: 'tree,form',
            views: [
                [this.state.tree_view, 'list'],
                [false, 'form']
            ],
            target: 'current'
        }, options);
    }
   async current_late(e,oid) {
        e.stopPropagation();
        e.preventDefault();
        var options = {
            on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        };
        for(var x  of this.state.employees){
        console.log(x,'ddddddddddd')
            if(x['id'] == oid){
                var task_ids = x['late']['current_late'];
            }
        }
        this.action.doAction({
            name: _t("Late Arrival"),
            type: 'ir.actions.act_window',
            res_model: 'early.late.request',
            domain: [
                ["id", "in", task_ids]
            ],
            view_mode: 'tree,form',
            views: [
                [this.state.tree_view, 'list'],
                [false, 'form']
            ],
            target: 'current'
        }, options);
    }
   async weekly_late(e,oid) {
        e.stopPropagation();
        e.preventDefault();
        var options = {
            on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        };
        for(var x  of this.state.employees){
        console.log(x,'ddddddddddd')
            if(x['id'] == oid){
                var task_ids = x['late']['week_late'];
            }
        }
        this.action.doAction({
            name: _t("Late Arrival"),
            type: 'ir.actions.act_window',
            res_model: 'early.late.request',
            domain: [
                ["id", "in", task_ids]
            ],
            view_mode: 'tree,form',
            views: [
                [this.state.tree_view, 'list'],
                [false, 'form']
            ],
            target: 'current'
        }, options);
    }


    filterEmployees() {
        this.state.filteredEmployees = this.state.selectedCompanyId
            ? this.state.employees.filter(employee => employee.company_id === this.state.selectedCompanyId)
            : this.state.employees;
    }


}

LateComingDashboard.template = "late_coming_dashboard";
registry.category("actions").add("late_coming_dashboard", LateComingDashboard);