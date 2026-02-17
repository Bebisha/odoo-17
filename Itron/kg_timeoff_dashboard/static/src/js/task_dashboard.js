/** @odoo-module */
import { registry } from '@web/core/registry';
import { useService } from "@web/core/utils/hooks";
const { Component, onMounted } = owl;
import { jsonrpc } from "@web/core/network/rpc_service";
import { _t } from "@web/core/l10n/translation";
import { useState } from "@odoo/owl";

export class TaskDashboard extends Component {
    setup() {
        this.action = useService("action");
        this.orm = useService("orm");
        this.rpc = useService("rpc");
        onMounted(this.onMounted);
        this.state = useState({
            result: {},
            filteredResult: {},
            selectedCompanyId: null,
            overdue: {},
            filteredoverdue: {},
            filteredno_task: {},
            no_task: {},
            max_length:0,
            range_list:[],
            no_task_row_to_display:[],
            overdue_row_to_display:[],
            companies: [],
            is_admin:0
        });
    }

//    init(parent, context) {
//        this._super(parent, context);
//        this.dashboards_templates = ['KgDashboardProject'];
//        this.today_sale = [];
//    }

    async onMounted() {
        this.render_project_task();
    }



     async render_project_task() {
        const result = await this.orm.call('project.project', 'get_project_data',[[]]);
        this.state.result = result.summary;
        this.state.filteredResult = this.state.result ;
        this.state.overdue = result.overdue;
        this.state.filteredoverdue = this.state.overdue;
        this.state.no_task = result.no_task;
        this.state.filteredno_task = this.state.no_task;
        this.state.companies = result.companies;
        this.state.is_admin = result.is_admin;
        if (!this.state.is_admin){
            this.state.selectedCompanyId = result.companies[0]['id']
        }

        this.state.max_length = result.max_length;
        this.state.range_list = result.range_list;
        this.state.overdue_row_to_display = result.overdue_row_to_display;
        this.state.no_task_row_to_display = result.no_task_row_to_display;
        console.log('this.state',this.state)
        this.filterEmployees();

    }




    async FilterCompanytasks(event) {
        const selectedCompanyId = event.target.value;
        this.state.selectedCompanyId = parseInt(selectedCompanyId) || null;
        console.log(this.state.selectedCompanyId,'this.state.selectedCompanyId')
        this.filterEmployees();
        }

    filterEmployees() {
            const { selectedCompanyId, result,overdue,no_task} = this.state;
            let filtered = [...result];
            let filteredOverdue = [...overdue];
            let filteredNo = [...no_task];


            if (selectedCompanyId) {
                filtered = filtered.filter(result => result.company_id === selectedCompanyId);
                filteredOverdue = filteredOverdue.filter(result => result.company_id === selectedCompanyId);
                filteredNo = filteredNo.filter(result => result.company_id === selectedCompanyId);
            }

            this.state.filteredResult = filtered;
            this.state.filteredoverdue = filteredOverdue;
            this.state.filteredno_task = filteredNo;

        }




    async tot_tasks(e,oid) {
        e.stopPropagation();
        e.preventDefault();
        var options = {
            on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        };
        const result = await this.orm.call('project.project', 'get_project_data',[[]]);
        for(var x  of result.summary){
            if(x['id'] == oid){
                var task_ids = x['task_ids']['name'];
            }
        }
        this.action.doAction({
            name: _t("Tasks"),
            type: 'ir.actions.act_window',
            res_model: 'project.task',
            domain: [
                ["id", "in", task_ids]
            ],
            view_mode: 'tree,form',
            views: [
                [false, 'list'],
                [false, 'form']
            ],
            target: 'current'
        }, options);
    }



    async tot_assignee(e,oid) {
        e.stopPropagation();
        e.preventDefault();
        var options = {
            on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        };
        const result = await this.orm.call('project.project', 'get_project_data',[[]]);
        for(var x  of result.summary){
            if(x['id'] == oid){
                var task_ids = x['task_ids']['total'];
            }
        }
        this.action.doAction({
            name: _t("Tasks"),
            type: 'ir.actions.act_window',
            res_model: 'project.task',
            domain: [
                ["id", "in", task_ids]
            ],
            view_mode: 'tree,form',
            views: [
                [false, 'list'],
                [false, 'form']
            ],
            target: 'current'
        }, options);
    }

    async tot_open(e,oid) {
        e.stopPropagation();
        e.preventDefault();
        var options = {
            on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        };
        const result = await this.orm.call('project.project', 'get_project_data',[[]]);
        for(var x  of result.summary){
            if(x['id'] == oid){
                var task_ids = x['task_ids']['open'];
            }
        }
        this.action.doAction({
            name: _t("Tasks"),
            type: 'ir.actions.act_window',
            res_model: 'project.task',
            domain: [
                ["id", "in", task_ids]
            ],
            view_mode: 'tree,form',
            views: [
                [false, 'list'],
                [false, 'form']
            ],
            target: 'current'
        }, options);
    }

    async tot_today(e,oid) {
        e.stopPropagation();
        e.preventDefault();
        var options = {
            on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        };
        const result = await this.orm.call('project.project', 'get_project_data',[[]]);
        for(var x  of result.summary){
            if(x['id'] == oid){
                var task_ids = x['task_ids']['today'];
            }
        }
        this.action.doAction({
            name: _t("Tasks"),
            type: 'ir.actions.act_window',
            res_model: 'project.task',
            domain: [
                ["id", "in", task_ids]
            ],
            view_mode: 'tree,form',
            views: [
                [false, 'list'],
                [false, 'form']
            ],
            target: 'current'
        }, options);
    }

    async tot_overdue(e,oid) {
        e.stopPropagation();
        e.preventDefault();
        var options = {
            on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        };
        const result = await this.orm.call('project.project', 'get_project_data',[[]]);
        for(var x  of result.summary){
            if(x['id'] == oid){
                var task_ids = x['task_ids']['overdue'];
            }
        }
        this.action.doAction({
            name: _t("Tasks"),
            type: 'ir.actions.act_window',
            res_model: 'project.task',
            domain: [
                ["id", "in", task_ids]
            ],
            view_mode: 'tree,form',
            views: [
                [false, 'list'],
                [false, 'form']
            ],
            target: 'current'
        }, options);
    }

    async tota_overdue(e,oid) {
        e.stopPropagation();
        e.preventDefault();
        var options = {
            on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        };
        const result = await this.orm.call('project.project', 'get_project_data',[[]]);
        for(var x  of result.overdue){
            if(x['id'] == oid){
                var task_ids = x['task_ids']['overdue'];
            }
        }
        this.action.doAction({
            name: _t("Tasks"),
            type: 'ir.actions.act_window',
            res_model: 'project.task',
            domain: [
                ["id", "in", task_ids]
            ],
            view_mode: 'tree,form',
            views: [
                [false, 'list'],
                [false, 'form']
            ],
            target: 'current'
        }, options);
    }

    async tot_pending(e,oid) {
        e.stopPropagation();
        e.preventDefault();
        var options = {
            on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        };
        const result = await this.orm.call('project.project', 'get_project_data',[[]]);
        for(var x  of result.summary){
            if(x['id'] == oid){
                var task_ids = x['task_ids']['pending'];
            }
        }
        this.action.doAction({
            name: _t("Tasks"),
            type: 'ir.actions.act_window',
            res_model: 'project.task',
            domain: [
                ["id", "in", task_ids]
            ],
            view_mode: 'tree,form',
            views: [
                [false, 'list'],
                [false, 'form']
            ],
            target: 'current'
        }, options);
    }

    async tot_fixed(e,oid) {
        e.stopPropagation();
        e.preventDefault();
        var options = {
            on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        };
        const result = await this.orm.call('project.project', 'get_project_data',[[]]);
        for(var x  of result.summary){
            if(x['id'] == oid){
                var task_ids = x['task_ids']['fixed'];
            }
        }
        this.action.doAction({
            name: _t("Tasks"),
            type: 'ir.actions.act_window',
            res_model: 'project.task',
            domain: [
                ["id", "in", task_ids]
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
        const result = await this.orm.call('project.project', 'get_project_data',[[]]);
        for(var x  of result.summary){
            if(x['id'] == oid){
                var task_ids = x['task_ids']['held'];
            }
        }
        this.action.doAction({
            name: _t("Tasks"),
            type: 'ir.actions.act_window',
            res_model: 'project.task',
            domain: [
                ["id", "in", task_ids]
            ],
            view_mode: 'tree,form',
            views: [
                [false, 'list'],
                [false, 'form']
            ],
            target: 'current'
        }, options);
    }

    async tot_tasks(e,oid) {
        e.stopPropagation();
        e.preventDefault();
        var options = {
            on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        };
        const result = await this.orm.call('project.project', 'get_project_data',[[]]);
        for(var x  of result.summary){
            if(x['id'] == oid){
                var task_ids = x['task_ids']['total'];
            }
        }
        this.action.doAction({
            name: _t("Tasks"),
            type: 'ir.actions.act_window',
            res_model: 'project.task',
            domain: [
                ["id", "in", task_ids]
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

TaskDashboard.template = "TaskDashboard";
registry.category("actions").add("task_dashboard", TaskDashboard);