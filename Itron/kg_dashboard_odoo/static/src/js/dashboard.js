/** @odoo-module */
import { registry } from '@web/core/registry';
import { useService } from "@web/core/utils/hooks";
const { Component, onMounted } = owl;
import { jsonrpc } from "@web/core/network/rpc_service";
import { _t } from "@web/core/l10n/translation";
import { useState } from "@odoo/owl";

export class KgDashboard extends Component {
    setup() {
        this.action = useService("action");
        this.orm = useService("orm");
        this.rpc = useService("rpc");
        onMounted(this.onMounted);
        this.state = useState({
            result: {},
        });
    }

    init(parent, context) {
        this._super(parent, context);
        this.dashboards_templates = ['KgDashboardProject'];
        this.today_sale = [];
    }

    async onMounted() {
        this.render_dashboards();
        this.render_project_task();
    }

    async render_dashboards() {
        var self = this;
        // Commented out for now since QWeb is not defined
        /*
        this.dashboards_templates.forEach(function(template) {
            self.$('.o_pj_dashboard').append(QWeb.render(template, {
                widget: self
            }));
        });
        */
    }

     async render_project_task() {
        const result = await this.orm.call('project.project', 'get_project');
        this.state.result = result;
    }

    async tot_tasks(e,oid) {
        e.stopPropagation();
        e.preventDefault();
        var options = {
            on_reverse_breadcrumb: this.on_reverse_breadcrumb,
        };
        const result = await this.orm.call('project.project', 'get_project');
        for(var x  of result){
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
        const result = await this.orm.call('project.project', 'get_project');
        for(var x  of result){
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
        const result = await this.orm.call('project.project', 'get_project');
        for(var x  of result){
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
        const result = await this.orm.call('project.project', 'get_project');
        for(var x  of result){
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
        const result = await this.orm.call('project.project', 'get_project');
        for(var x  of result){
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
        const result = await this.orm.call('project.project', 'get_project');
        for(var x  of result){
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
        const result = await this.orm.call('project.project', 'get_project');
        for(var x  of result){
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
        const result = await this.orm.call('project.project', 'get_project');
        for(var x  of result){
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
        const result = await this.orm.call('project.project', 'get_project');
        for(var x  of result){
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

KgDashboard.template = "KgDashboard";
registry.category("actions").add("kg_project_dashboard", KgDashboard);
