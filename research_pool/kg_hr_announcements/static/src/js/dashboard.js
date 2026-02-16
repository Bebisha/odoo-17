/**@odoo-module **/
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component } from  "@odoo/owl";
const actionRegistry = registry.category("actions");
class HRDashboard extends Component {
   setup() {
         super.setup()
         this.orm = useService('orm')
         this._fetch_data()
   }
   _fetch_data(){
   var self = this;
  this.orm.call("hr.employee", "get_upcoming", [], {}).then(function(result){

        if (result.announcements) {
                for (let j = 0; j < result.announcements.length; j++) {
                    $('#announcement_data').append('<span>' + result.announcements[j].name + "<br>" + "<hr>"+ '</span>');
                }
             }
             else {
                console.error("Announcement data is undefined.");
             }




           });

       };
}
HRDashboard.template = "HRDashboard";
actionRegistry.add("hr_dashboard_tag", HRDashboard);


//import { registry } from "@web/core/registry";
//import { useService } from "@web/core/utils/hooks";
//import { Component } from  "@odoo/owl";
//const actionRegistry = registry.category("actions");
//class HrDashboard extends Component {
//   setup() {
//         super.setup()
//         this.orm = useService('orm')
//         this._fetch_data()
//   }
//   _fetch_data(){
//   var self = this;
//  this.orm.call("hr.employee", "get_upcoming", [], {}).then(function(result){
////           $('#employee_birthday').append();
//           $('#my_lead').append('<span>' + result.name + '</span>');
//           });
//       };
//}
//HrDashboard.template = "bista_dashboard_hr.HrDashboard";
////  Tag name that we entered in the first step.
//actionRegistry.add("crm_dashboard_tag", HrDashboard);