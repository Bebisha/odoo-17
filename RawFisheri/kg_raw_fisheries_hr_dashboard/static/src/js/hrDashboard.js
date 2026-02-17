/**@odoo-module **/
const { Component, useState } = owl;
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
const actionRegistry = registry.category("actions");
class HrDashboard extends Component {
   setup() {
         super.setup()
         this.orm = useService('orm')
         this.state = useState({
            data: { vessels_by_department: [] },
            filter: 'active',
        });
        this._fetch_data(this.state.filter);
   }
   _fetch_data(filter = 'active') {
        var self = this;
        this.orm.call("hr.employee", "get_employee_data", [filter], {}).then((result) => {
            this.state.data = result;
        });
   }
   onFilterChange(event) {
        const selectedFilter = event.target.value;
        this.state.filter = selectedFilter;
        this._fetch_data(selectedFilter);
   }
   fetchActiveEmployees() {
        this._fetch_data('active');
   }
   fetchInactiveEmployees() {
        this._fetch_data('inactive');
   }
   openEmployee(employeeId) {
        return async function(event) {
            event.preventDefault();

            const action = {
                type: 'ir.actions.act_window',
                res_model: 'hr.employee',
                views: [[false, 'form']],
                res_id: employeeId,
                target: 'current',
            };
            this.env.services.action.doAction(action);
        }.bind(this);
   }
}

HrDashboard.template = "hr_dashboard.HrDashboard";
actionRegistry.add("hr_dashboard", HrDashboard);