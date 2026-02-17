/**@odoo-module **/
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component } from  "@odoo/owl";
const actionRegistry = registry.category("actions");
class CrmDashboard extends Component {
   setup() {
         super.setup()
         this.orm = useService('orm')
         this._fetch_data()
   }
   _fetch_data(){
   var self = this;
  this.orm.call("hr.employee", "get_upcoming", [], {}).then(function(result){
            console.log(result,'ssssssss');
//            console.log(result.birthday.length,'lllllllllllllllllllll');
//            console.log(result.event_data.length,'ddddddddddddddddddddddddd');
//            console.log(result.birthday,'aaaaaa');
//            console.log(result.birthday[0].name,'cccccc');
             if (result.birthday) {
                    console.log(result.birthday.length, 'lllllllllllllllllllll');
                    console.log(result.birthday, 'aaaaaa');
                    console.log(result.birthday[0]?.name, 'cccccc');
                    for (let i = 0; i < result.birthday.length; i++) {
                        $('#my_lead').append('<span>' + result.birthday[i].name + "<br>" + result.birthday[i].job_id + "<br>" + result.birthday[i].birthday + "<br>" + "<hr>"+ '</span>');
                        console.log('aaaapppp',$('#my_lead'));
                    }
             }
             else {
                    console.error("Birthday data is undefined.");

             }
             if (result.event) {
                console.log(result.event.length, 'ddddddddddddddddddddddddd');
                for (let j = 0; j < result.event.length; j++) {
                    $('#event_data').append('<span>' + result.event[j].name + "<br>" + "<hr>"+ '</span>');
                }
             }
             else {
                console.error("Event data is undefined.");
             }


             if (result.announcements) {
                console.log(result.announcements.length, 'ttttttttpp');
                for (let j = 0; j < result.announcements.length; j++) {
                    $('#announcement_data').append('<span>' + result.announcements[j].name + "<br>" + "<hr>"+ '</span>');
                }
             }
             else {
                console.error("announcement data is undefined.");
             }

           });

       };
}
CrmDashboard.template = "bista_dashboard_hr.CrmDashboard";
actionRegistry.add("crm_dashboard_tag", CrmDashboard);


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