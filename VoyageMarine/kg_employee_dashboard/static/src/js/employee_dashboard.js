/** @odoo-module **/
import { registry } from "@web/core/registry";
import { Component, onWillStart, useState } from "@odoo/owl";
import { jsonrpc } from "@web/core/network/rpc_service";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";

class EmployeeDashboard extends Component {
    setup() {
        this.state = useState({
            assigned: [],
            unassigned: [],
            forecasted: [],
        });

        // Access action service for navigation
        this.action = useService("action");

        onWillStart(async () => {
            const result = await jsonrpc('/employee_dashboard/employees');
            this.state.assigned = result.assigned || [];
            this.state.unassigned = result.unassigned || [];
            this.state.forecasted = result.forecasted || [];
        });
    }

    viewEmployeeProjects(e, projectIds) {
        e.stopPropagation();
        e.preventDefault();

        if (projectIds && projectIds.length) {
            const options = {
                on_reverse_breadcrumb: this.on_reverse_breadcrumb,
            };

            this.action.doAction({
                name: _t("Projects"),
                type: 'ir.actions.act_window',
                res_model: 'project.project',
                domain: [
                    ["id", "in", projectIds]
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
navigateToEmployeeProjects(emp) {
        if (emp.project_ids && emp.project_ids.length) {
            const options = {
                on_reverse_breadcrumb: this.on_reverse_breadcrumb,
            };

            this.action.doAction({
                name: _t("Projects"),
                type: 'ir.actions.act_window',
                res_model: 'project.project',
                domain: [
                    ["id", "in", emp.project_ids]
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
    }

EmployeeDashboard.template = "kg_employee_dashboard.EmployeeDashboard";

registry.category("actions").add("employee_dashboard_tag", EmployeeDashboard);