
/** @odoo-module */
import { registry } from "@web/core/registry";
const { Component , onWillStart,onMounted} = owl;
const actionRegistry = registry.category("actions");
import { loadJS } from '@web/core/assets';
import { useService } from "@web/core/utils/hooks";
export class SalesDashboard extends Component {
    setup() {
        this.actionService = useService("action");

    }
    async fetchSalesData(methodName) {
        try {
            const response = await rpc.query({
                model: 'sale.order',
                method: search_read,
                args: [],
            });
            console.log(response,'bebiiiiiiiiiiiiiiiiiiiiiii')
            return response;
        } catch (error) {
            console.error(`Error calculating ${methodName} sales amount:`, error);
            return null;
        }
    }

//    async calculateLastMonthSalesAmount() {
//        const response = await this.fetchSalesData('calculate_last_month_sales_amount');
//        if (response !== null) {
//            this.updateSalesData(response, 'LastMonthSales', 'fa-calendar-o');
//        }
//    }
//
//    async calculateLastYearSalesAmount() {
//        const response = await this.fetchSalesData('calculate_last_year_sales_amount');
//        if (response !== null) {
//            this.updateSalesData(response, 'LastYearSales', 'fa-calendar');
//        }
//    }


}

SalesDashboard.template = "SalesDashboard";
actionRegistry.add("tag_sales_dashboard", SalesDashboard);



/** @odoo-module */

//import { registry } from "@web/core/registry"
//import { loadJS } from "@web/core/assets"
//const { Component, onWillStart, useRef, onMounted } = owl
//
//export class ChartRenderer extends Component {
//    setup(){
//        this.chartRef = useRef("chart")
//        onWillStart(async ()=>{
//            await loadJS("https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.0/chart.umd.min.js")
//        })
//
//        onMounted(()=>this.renderChart())
//    }
//
//    renderChart(){
//        new Chart(this.chartRef.el,
//        {
//          type: this.props.type,
//          data: {
//            labels: [
//                'Red',
//                'Blue',
//                'Yellow'
//              ],
//              datasets: [
//              {
//                label: 'My First Dataset',
//                data: [300, 50, 100],
//                hoverOffset: 4
//              },{
//                label: 'My Second Dataset',
//                data: [100, 70, 150],
//                hoverOffset: 4
//              }]
//          },
//          options: {
//            responsive: true,
//            plugins: {
//              legend: {
//                position: 'bottom',
//              },
//              title: {
//                display: true,
//                text: this.props.title,
//                position: 'bottom',
//              }
//            }
//          },
//        }
//      );
//    }
//}
//
//ChartRenderer.template = "owl.ChartRenderer"
//
