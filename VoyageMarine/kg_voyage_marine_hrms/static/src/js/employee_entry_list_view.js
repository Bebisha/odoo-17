/** @odoo-module */
import { ListController } from "@web/views/list/list_controller";
import { registry } from '@web/core/registry';
import { listView } from '@web/views/list/list_view';

export class EmployeeEntryListController extends ListController {
   setup() {
       super.setup();
   }
   GenerateEmpEntries() {
       this.actionService.doAction({
          type: 'ir.actions.act_window',
          res_model: 'generate.employee.entries.wizard',
          name:'Generate Employee Entries',
          view_mode: 'form',
          view_type: 'form',
          views: [[false, 'form']],
          target: 'new',
          res_id: false,
       });
   }
}

registry.category("views").add("button_in_tree", {
   ...listView,
   Controller: EmployeeEntryListController,
   buttonTemplate: "kg_voyage_marine_hrms.ListButtons",
});
