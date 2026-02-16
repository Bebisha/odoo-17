/**@odoo-module **/
const { Component, useState } = owl;
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
const actionRegistry = registry.category("actions");
class SaleDashboard extends Component {
   setup() {
         super.setup()
         this.orm = useService('orm')
         this.state = useState({ data: [] });
         this._fetch_data()
   }
   _fetch_data(){
       var self = this;
       var domain =  [['state','=','draft']]
        this.orm.call("sale.dashboard", "get_sale_data", [domain], {}).then((result) => {
            this.state.data = result;
            console.log(result,'resultttttt')
        });
        };
//   openPurchaseOrder(orderId) {
//        return async function(event) {
//            event.preventDefault();
//
//           const action = {
//                type: 'ir.actions.act_window',
//                res_model: 'sale.order',
//                views: [[false, 'form']],
////                res_id: orderId,
//                target: 'current',
//            };
//            this.env.services.action.doAction(action);
//        }.bind(this);
//    }
}

SaleDashboard.template = "kg_oms.SaleDashboard";
actionRegistry.add("tag_sales_dashboard", SaleDashboard);