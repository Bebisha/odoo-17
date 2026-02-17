/** @odoo-module */
import { registry } from '@web/core/registry';
import { useService } from "@web/core/utils/hooks";
const { Component, onMounted } = owl;
import { jsonrpc } from "@web/core/network/rpc_service";
import { _t } from "@web/core/l10n/translation";
import { useState } from "@odoo/owl";

export class HelpdeskDashboard extends Component {
    setup() {
        this.action = useService("action");
        this.orm = useService("orm");
        this.rpc = useService("rpc");
        onMounted(this.onMounted);
        this.state = useState({
            result:{},
            selectedCompanyId:0,
            is_admin:0,
            is_heldesk_manager:0,
            companies:[],
            filteredResult:[]
        });
    }

    async onMounted() {
        this.render_project_task();
    }

     async render_project_task() {
        const result = await this.orm.call('helpdesk.ticket', 'get_helpdesk_ticket_data',[[]]);
        this.state.result = result.vals;
        this.state.companies = result.company_data;
        this.state.is_admin = result.is_admin;
        this.state.is_heldesk_manager = result.is_heldesk_manager;
        if (!this.state.is_admin){
            this.state.selectedCompanyId = result.company_data[0]['id']
        }
        this.filterEmployees();

    }
     async FilterCompanytasks(event) {
        const selectedCompanyId = event.target.value;
        this.state.selectedCompanyId = parseInt(selectedCompanyId) || null;
        this.filterEmployees();
        }
        filterEmployees() {
            const { selectedCompanyId, result} = this.state;
            let filtered = [...result];
//            let filteredOverdue = [...overdue]

            if (selectedCompanyId) {
            console.log('result,result',result)
                filtered = filtered.filter(result => result.company_id === selectedCompanyId || result.company_id===false);
//                filteredOverdue = filteredOverdue.filter(result => result.company_id === selectedCompanyId);
//                filteredNo = filteredNo.filter(result => result.company_id === selectedCompanyId);
            }

            this.state.filteredResult = filtered;
//            this.state.filteredoverdue = filteredOverdue;
//            this.state.filteredno_task = filteredNo;

        }


    async tot_open(e,oid) {
        e.stopPropagation();
        e.preventDefault();
        var options = {
            on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        };
        for(var x  of this.state.result){
            if(x['id'] == oid){
                var ticket_ids = x['ticket_ids']['open'];
            }
        }
        this.action.doAction({
            name: _t("Open Ticket"),
            type: 'ir.actions.act_window',
            res_model: 'helpdesk.ticket',
            domain: [
                ["id", "in", ticket_ids]
            ],
            view_mode: 'tree,form',
            views: [
                [false, 'list'],
                [false, 'form']
            ],
            target: 'current'
        }, options);
    }

    async tot_inprogress(e,oid) {
        e.stopPropagation();
        e.preventDefault();
        var options = {
            on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        };
        for(var x  of this.state.result){
            if(x['id'] == oid){
                var ticket_ids = x['ticket_ids']['inprogress'];
                console.log("ticket_ids",ticket_ids)
            }
        }
        this.action.doAction({
            name: _t("In progress Ticket"),
            type: 'ir.actions.act_window',
            res_model: 'helpdesk.ticket',
            domain: [
                ["id", "in", ticket_ids]
            ],
            view_mode: 'tree,form',
            views: [
                [false, 'list'],
                [false, 'form']
            ],
            target: 'current'
        }, options);
    }
    async tot_uat(e,oid) {
        e.stopPropagation();
        e.preventDefault();
        var options = {
            on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        };
        for(var x  of this.state.result){
            if(x['id'] == oid){
                var ticket_ids = x['ticket_ids']['uat'];
            }
        }
        this.action.doAction({
            name: _t("UAT Ticket"),
            type: 'ir.actions.act_window',
            res_model: 'helpdesk.ticket',
            domain: [
                ["id", "in", ticket_ids]
            ],
            view_mode: 'tree,form',
            views: [
                [false, 'list'],
                [false, 'form']
            ],
            target: 'current'
        }, options);
    }
    async tot_returned(e,oid) {
        e.stopPropagation();
        e.preventDefault();
        var options = {
            on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        };
        for(var x  of this.state.result){
            if(x['id'] == oid){
                var ticket_ids = x['ticket_ids']['returned'];
            }
        }
        this.action.doAction({
            name: _t("Returned Ticket"),
            type: 'ir.actions.act_window',
            res_model: 'helpdesk.ticket',
            domain: [
                ["id", "in", ticket_ids]
            ],
            view_mode: 'tree,form',
            views: [
                [false, 'list'],
                [false, 'form']
            ],
            target: 'current'
        }, options);
    }
    async tot_cr(e,oid) {
        e.stopPropagation();
        e.preventDefault();
        var options = {
            on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        };
        for(var x  of this.state.result){
            if(x['id'] == oid){
                var ticket_ids = x['ticket_ids']['cr'];
            }
        }
        this.action.doAction({
            name: _t("CR Ticket"),
            type: 'ir.actions.act_window',
            res_model: 'helpdesk.ticket',
            domain: [
                ["id", "in", ticket_ids]
            ],
            view_mode: 'tree,form',
            views: [
                [false, 'list'],
                [false, 'form']
            ],
            target: 'current'
        }, options);
    }

    async tot_held(e,oid) {
        e.stopPropagation();
        e.preventDefault();
        var options = {
            on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        };
        for(var x  of this.state.result){
            if(x['id'] == oid){
                var ticket_ids = x['ticket_ids']['held'];
            }
        }
        this.action.doAction({
            name: _t("Hold Ticket"),
            type: 'ir.actions.act_window',
            res_model: 'helpdesk.ticket',
            domain: [
                ["id", "in", ticket_ids]
            ],
            view_mode: 'tree,form',
            views: [
                [false, 'list'],
                [false, 'form']
            ],
            target: 'current'
        }, options);
    }

   async tot_closed(e,oid) {
        e.stopPropagation();
        e.preventDefault();
        var options = {
            on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        };
        for(var x  of this.state.result){
            if(x['id'] == oid){
                var ticket_ids = x['ticket_ids']['closed'];
            }
        }
        this.action.doAction({
            name: _t("Closed Ticket"),
            type: 'ir.actions.act_window',
            res_model: 'helpdesk.ticket',
            domain: [
                ["id", "in", ticket_ids]
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

HelpdeskDashboard.template = "HelpdeskDashboard";
registry.category("actions").add("helpdesk_dashboard", HelpdeskDashboard);
