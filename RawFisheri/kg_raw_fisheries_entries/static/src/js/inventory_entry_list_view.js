/** @odoo-module */
import { ListController } from "@web/views/list/list_controller";
import { registry } from '@web/core/registry';
import { listView } from '@web/views/list/list_view';

export class InventoryEntryListController extends ListController {
   setup() {
       super.setup();
   }
   ImportInventoryEntries() {
       this.actionService.doAction({
          type: 'ir.actions.act_window',
          res_model: 'import.pol.wizard',
          name:'Import Entries',
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
   Controller: InventoryEntryListController,
   buttonTemplate: "kg_raw_fisheries_entries.ListButtons",
});