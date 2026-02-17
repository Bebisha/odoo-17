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
            all_employees: [],
            companies: [],
            selectedCompanyId: null,
            selectedEmployeeId: null,
            filteredEmployees: [],
            startDate: null,
            endDate: null,
            tree_view: 0,
        });

        this.loadEmployeeData();
    }

    async loadEmployeeData() {
        try {
            const result = await this.orm.call("hr.employee", "get_values", []);
            this.state.employees = result.employees || [];
            this.state.all_employees = result.all_employees || [];
            this.state.companies = result.companies || [];
            this.state.tree_view = result.tree_view || [];

            const today = new Date().toISOString().split("T")[0];
            const temp_emp = this.state.employees
            console.log(temp_emp,'fjjjjjjjjjjjj')
            console.log(today,'llllllllllllllll')

            this.state.filteredEmployees = temp_emp.filter(employee => employee.date === today);

            console.log("Employee Data for Today:", this.state.filteredEmployees);
            console.log("Company Data:", this.state.companies);
        } catch (error) {
            console.error("Failed to fetch attendance data", error);
        }
    }

   async updateEmployeeDropdown(event) {
        const selectedCompanyId = event.target.value;
        this.state.selectedCompanyId = parseInt(selectedCompanyId) || null;


        if (this.state.selectedCompanyId != null) {
        console.log(this.state.selectedCompanyId,'this.state.selectedCompanyId')
            try {
                const employees = await this.orm.call('hr.employee', 'get_employees_by_company', [this.state.selectedCompanyId]);

                this.state.all_employees = employees;

                this.filterEmployees();

                this.render();
            } catch (error) {
                console.error('Error fetching employees:', error);
                this.state.all_employees = [];
                this.filterEmployees();
                this.render();
            }
        } else {
        console.log('vishnu')
            const employees = await this.orm.call('hr.employee', 'get_employees_by_company', []);

            this.state.all_employees = employees;
            this.filterEmployees();
            this.render();
        }
    }


    async updateEarlyLateRequests(event) {
        const selectedEmployeeId = event.target.value;
        this.state.selectedEmployeeId = parseInt(selectedEmployeeId) || null;


         this.filterEmployees();
    }

    async updateRequestsByStartDate(event) {
        const selectedStartDate = event.target.value;
        this.state.startDate = selectedStartDate;
        this.filterEmployees();

    }



    filterEmployees() {
    const { selectedCompanyId, startDate, endDate, selectedEmployeeId, employees } = this.state;
    let filtered = [...employees];

    if (selectedCompanyId === null && startDate === null && endDate === null && selectedEmployeeId === null) {
        const today = new Date().toISOString().split("T")[0];
        filtered = filtered.filter(employee => employee.date === today);
    } else {
        if (selectedCompanyId) {
            filtered = filtered.filter(employee => employee.company_id === selectedCompanyId);
        }

        if (startDate) {
            filtered = filtered.filter(employee => new Date(employee.date) >= new Date(startDate));
        }

        if (endDate) {
            filtered = filtered.filter(employee => new Date(employee.date) <= new Date(endDate));
        }

        if (selectedEmployeeId) {
            filtered = filtered.filter(employee => employee.employee_id === selectedEmployeeId);
        }
    }

    this.state.filteredEmployees = filtered;
    console.log("Filtered Employees:", filtered);
}



        updateEndDate(event) {
            this.state.endDate = event.target.value || null;
            this.filterEmployees();
        }




    async tot_late(e, oid) {
        e.stopPropagation();
        e.preventDefault();
        const options = { on_reverse_breadcrumb: this.on_reverse_breadcrumb };
        const employee = this.state.employees.find(emp => emp.id === oid);
        if (employee) {
            const task_ids = employee.late.total_late;
            this.action.doAction({
                name: _t("Total Late Arrival"),
                type: 'ir.actions.act_window',
                res_model: 'early.late.request',
                domain: [["id", "in", task_ids]],
                view_mode: 'tree,form',
                views: [[this.state.tree_view, 'list'], [false, 'form']],
                target: 'current',
            }, options);
        }
    }

    async current_late(e, oid) {
        e.stopPropagation();
        e.preventDefault();
        const options = { on_reverse_breadcrumb: this.on_reverse_breadcrumb };
        const employee = this.state.employees.find(emp => emp.id === oid);
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
        const employee = this.state.employees.find(emp => emp.id === oid);
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

LateComingDashboard.template = "late_coming_dashboard";
registry.category("actions").add("late_coming_dashboard", LateComingDashboard);