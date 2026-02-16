/**@odoo-module **/
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component } from  "@odoo/owl";
const actionRegistry = registry.category("actions");
class HrDashboards extends Component {
   setup() {
         super.setup()
         this.orm = useService('orm')
         this._fetch_data()
   }
   _fetch_data(){
   var self = this;
  this.orm.call("hr.employee", "get_upcoming", [], {}).then(function(result){

        if (result.birthday) {
                 result.birthday.sort((a, b) => {

        return new Date(a.birthday) - new Date(b.birthday);
                 });

                var htmlContent = '';
                for (let i = 0; i < result.birthday.length; i++) {
                    htmlContent += '<span>' +
                                    '<div class="media">' +
                                        '<div class="media-body">' +
                                            '<h5 id="name_' + i + '" class="mt-0">' + result.birthday[i].name + '</h5>' +
                                            '<p id="job_id_' + i + '">' + result.birthday[i].job_id + '</p>' +
                                            '<p id="birthday_' + i + '">' + result.birthday[i].birthday + '</p>' +
                                        '</div>' +
                                        '<img class="ml-3 rounded-circle employee-image" src="' + result.birthday[i].image_url + '" title="' + result.birthday[i].name + '" alt="' + result.birthday[i].name + '">' +
                                    '</div>' +
                                    '<hr>' +
                                    '</span>';
                }
                $('#my_lead').append(htmlContent);
                } else {
                console.error("Birthday data is undefined.");
                }
        if (result.event) {
               for (let j = 0; j < result.event.length; j++) {
                   let eventContent = '<div class="event-section">';
                  if (result.event[j].name) {
                      const eventUrl = `/web#id=${result.event[j].id}&model=event.event&view_type=form`;
                      eventContent += `<span><a href="${eventUrl}">${result.event[j].name}</a><br></span>`;
                      }

                  eventContent += '<span><strong>Start Date:</strong> ' + result.event[j].date_begin + ' <strong>End Date:</strong> ' + result.event[j].date_end + "<br></span>";

                 if (result.event[j].event_type_id) {
                    eventContent += '<span><strong>Event Type:</strong> ' + result.event[j].event_type_id + "<br></span>";
                }
                eventContent += '<span>' + result.event[j].address_id + "<br></span>";


                eventContent += '<hr>';


                $('#event_data').append(eventContent);
               }

        }
        else {
                console.error("Event data is undefined.");
             }




  });

};
}
HrDashboards.template = "HrDashboards";
actionRegistry.add("hr_dashboard_tag", HrDashboards);


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