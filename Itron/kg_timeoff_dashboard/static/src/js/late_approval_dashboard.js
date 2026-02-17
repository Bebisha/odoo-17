 /** @odoo-module */
import { registry } from '@web/core/registry';
import { useService } from "@web/core/utils/hooks";
import { Component, useState } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";

export class LateComingWaitingDashboard extends Component {
    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.dialog = useService("dialog");

        this.state = useState({
            employees: [],
            employees_early: [],
            all_employees: [],
            companies: [],
            selectedCompanyId: null,
            selectedEmployeeId: null,
            filteredEmployees: [],
            filteredEmployeesEarly: [],
            startDate: null,
            endDate: null,
            tree_view: 0,
        });

        this.loadEmployeeData();
    }

    async loadEmployeeData() {
        try {
            const result = await this.orm.call("hr.employee", "get_values_to_approve", []);
            this.state.employees = result.employees || [];
            this.state.employees_early = result.employees_early || [];
            this.state.all_employees = result.all_employees || [];
            this.state.companies = result.companies || [];
            this.state.tree_view = result.tree_view || [];

            const today = new Date().toISOString().split("T")[0];
            const temp_emp = this.state.employees

            this.state.filteredEmployees = temp_emp
            this.state.filteredEmployeesEarly = this.state.employees_early

            console.log("Employee Data for Today:", this.state.filteredEmployees);
            console.log("Employee Data for Today:", this.state.employees_early);
            console.log("Company Data:", this.state.companies);
        } catch (error) {
            console.error("Failed to fetch attendance data", error);
        }
    }


    async FilterCompany(event) {
        const selectedCompanyId = event.target.value;
        this.state.selectedCompanyId = parseInt(selectedCompanyId) || null;
        this.filterEmployees();
        }

    async approveRequest(event, employeeId) {
        event.stopPropagation();
        event.preventDefault();

//        try {
            const result = await this.orm.call("early.late.request", "action_first_approval", [employeeId]);
            console.log("result",result)

            if (result.success) {
                alert("The request has been approved successfully!");
                await this.loadEmployeeData();
            } else {
                alert("Failed to approve the request. Please try again.");
            }
//        } catch (error) {
//            console.error("Error approving the request:", error);
//            alert("An error occurred while approving the request.");
//        }
    }

   async rejectRequest(event, rid) {
        event.stopPropagation();
        event.preventDefault();

        const action = {
        type: 'ir.actions.act_window',
        res_model: 'reject.reason.wizard',
        views: [[false, 'form']],
        view_mode: 'form',
        target: 'new',
        context: { from_dashboard: true, active_id: rid },
    };
        this.action.doAction(action);
   }

    filterEmployees() {
            const { selectedCompanyId, employees,employees_early} = this.state;
            let filtered = [...employees];
            let filtered_early = [...employees_early];


            if (selectedCompanyId) {
                filtered = filtered.filter(employee => employee.company_id === selectedCompanyId);
                filtered_early = filtered_early.filter(employee => employee.company_id === selectedCompanyId);
            }

            this.state.filteredEmployees = filtered;
            this.state.filteredEmployeesEarly = filtered_early;
            console.log("Filtered Employees:", filtered);
            console.log("Filtered Employees early:", filtered_early);
        }

    async tot_late(e, oid) {
            console.log('vishnu');
            e.stopPropagation();
            e.preventDefault();

            const options = { on_reverse_breadcrumb: this.on_reverse_breadcrumb };

            let employee = this.state.employees.find(emp => emp.id === oid);

            if (!employee) {
                employee = this.state.employees_early.find(emp => emp.id === oid);
            }

            if (employee) {
                const task_ids = employee.late ? employee.late.total_late : [];
                this.action.doAction({
                    name: _t("Total Late Arrival"),
                    type: 'ir.actions.act_window',
                    res_model: 'early.late.request',
                    domain: [["id", "in", task_ids]],
                    view_mode: 'tree,form',
                    views: [[this.state.tree_view, 'list'], [false, 'form']],
                    target: 'current',
                }, options);
            } else {
                console.log('No matching employee found in employees or employees_early.');

            }
        }

    async current_late(e, oid) {
        e.stopPropagation();
        e.preventDefault();
        const options = { on_reverse_breadcrumb: this.on_reverse_breadcrumb };
        let employee = this.state.employees.find(emp => emp.id === oid);

        if (!employee) {
            employee = this.state.employees_early.find(emp => emp.id === oid);
        }
        if (employee) {
            const task_ids = employee.late.current_late;
            this.action.doAction({
                name: _t("Late Arrival"),
                type: 'ir.actions.act_window',
                res_model: 'early.late.request',
                domain: [["id", "in", task_ids]],
                view_mode: 'tree,form',
                views: [[this.state.tree_view, 'list'], [false, 'form']],
                target: 'current',
            }, options);
        }
    }

    async weekly_late(e, oid) {
        e.stopPropagation();
        e.preventDefault();
        const options = { on_reverse_breadcrumb: this.on_reverse_breadcrumb };
        let employee = this.state.employees.find(emp => emp.id === oid);

        if (!employee) {
            employee = this.state.employees_early.find(emp => emp.id === oid);
        }
        if (employee) {
            const task_ids = employee.late.week_late;
            this.action.doAction({
                name: _t("Weekly Late Arrival"),
                type: 'ir.actions.act_window',
                res_model: 'early.late.request',
                domain: [["id", "in", task_ids]],
                view_mode: 'tree,form',
                views: [[this.state.tree_view, 'list'], [false, 'form']],
                target: 'current',
            }, options);
        }
    }
}

LateComingWaitingDashboard.template = "late_coming_approval_dashboard";
registry.category("actions").add("late_coming_approval_dashboard", LateComingWaitingDashboard);
