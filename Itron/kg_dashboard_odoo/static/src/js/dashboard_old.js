/** @odoo-module */
import { registry} from '@web/core/registry';
import { useService } from "@web/core/utils/hooks";
const { Component, onWillStart, onMounted} = owl
import { jsonrpc } from "@web/core/network/rpc_service";
import { _t } from "@web/core/l10n/translation";

//odoo.define('kg_dashboard_odoo.KgDashboard', function(require) {
//    "use strict";
export class KgDashboard extends Component {
    setup() {
            this.action = useService("action");
            this.orm = useService("orm");
            this.rpc = this.env.services.rpc
            onWillStart(this.onWillStart);
            onMounted(this.onMounted);
        }


//    async onWillStart() {
//		await this.dashboards_templates();
//	    }


//    var AbstractAction = require('web.AbstractAction');
//    var core = require('web.core');
//    var QWeb = core.qweb;
//    var ajax = require('web.ajax');
//    var rpc = require('web.rpc');
//    var _t = core._t;
//    var session = require('web.session');
//    var web_client = require('web.web_client');
//    var abstractView = require('web.AbstractView');
//    var flag = 0;
//    var tot_so = []
//    var tot_project = []
//    var tot_task = []
//    var tot_employee = []
//    var tot_hrs = []
//    var tot_margin = []
//    var KgDashboardProject = AbstractAction.extend({
//        template: 'KgDashboardProject',
//        cssLibs: [
//            '/kg_dashboard_odoo/static/src/css/lib/nv.d3.css'
//        ],
//        jsLibs: [
//            '/kg_dashboard_odoo/static/src/js/lib/d3.min.js'
//        ],
//
//        init: function(parent, context) {
//            this._super(parent, context);
//            this.dashboards_templates = ['KgDashboardProject'];
//            this.today_sale = [];
//        },
//
//        start: function() {
//            var self = this;
//            this.set("title", 'Dashboard');
//            return this._super().then(function() {
//                self.render_dashboards();
//                self.render_project_task();
//            });
//        },

    async onMounted() {
    console.log('KgDashboard onMounted');
		// Render other components after fetching data
		this.render_dashboards();
//		this.render_project_task();
	    }

        async render_dashboards() {
            var self = this;
            _.each(this.dashboards_templates, function(template) {
                self.$('.o_pj_dashboard').append(QWeb.render(template, {
                    widget: self
                }));
            });
        }

        async render_project_task(){
            var self = this
            rpc.query({
                model: "project.project",
                method: "get_project",
            }).then(function(result) {
                var due_count = 0;
                $('#odoo_project_details').empty();
                $('#task_table_thead').empty();
               $("#task_table_thead").append('<tr><th colspan="1" style="text-align:center"><b>ASSIGNEE</b></th><th colspan="1" style="text-align:center"><b>OPEN</b></th><th colspan="1" style="text-align:center"><b>TODAY</b></th><th colspan="1" style="text-align:center"><b>OVER DUE</b></th><th colspan="1" style="text-align:center"><b>PENDING TOTAL</b></th><th colspan="1" style="text-align:center"><b>FIXED</b></th><th colspan="1" style="text-align:center"><b>HELD</b></th><th colspan="1" style="text-align:center"><b>TOTAL</b></th></tr>')
                _.forEach(result, function(x) {
                    console.log("-----------",x)
                    $('#odoo_project_details').show();
                    $('#odoo_project_details').append('<tr><td colspan="1" style="text-align:center"><div id="line_user' + x['id'] + '"><b>'+ x['name'] + '</b></div>' +
                     '</td><td colspan="1" style="text-align:center;cursor: pointer;"><div id="line_open' + x['id'] + '">'+ x['open'] + '</div>' +
                      '</td><td colspan="1" style="text-align:center;cursor: pointer;"><div id="line_today' + x['id'] + '">'+ x['today'] + '</div>' +
                       '</td><td colspan="1" style="text-align:center;cursor: pointer;"><div id="line_overdue' + x['id'] + '">'+ x['overdue'] + '</div>' +
                        '</td><td colspan="1" style="text-align:center;cursor: pointer;"><div id="line_pending' + x['id'] + '">'+ x['pending'] + '</div>' +
                         '</td><td colspan="1" style="text-align:center;cursor: pointer;"><div id="line_fixed' + x['id'] + '">'+ x['fixed'] + '</div>' +
                         '</td><td colspan="1" style="text-align:center;cursor: pointer;"><div id="line_held' + x['id'] + '">'+ x['held'] + '</div>' +
                         '</td><td colspan="1" style="text-align:center;cursor: pointer;"><div id="line_total' + x['id'] + '">'+ x['total'] + '</div>' + '</td></tr>'
                    );

////                    $('#line_user' + x['id']).on("click", function() {
////                    console.log("uuuuuuuuuuu",x)
////                        self.do_action({
////                            res_model: 'res.users',
////                            name: _t('Project'),
////                            views: [
////                                [false, 'form']
////                            ],
////                            type: 'ir.actions.act_window',
////                            res_id: x['id'],
////                        });
////                    });
//
//
                    $('#line_open' + x['id']).on("click", function() {
                        var task_ids = x['task_ids']['open'];
                        var task_tree_id = x['task_tree_id'];
                        self.do_action({
                            res_model: 'project.task',
                            name: _t('Open Tasks - '+x['name']),
                            view_mode: 'tree',
                            views: [
                                [task_tree_id, 'list'],
                            ],
                            type: 'ir.actions.act_window',
                            target: 'new',
                            context: {'create': 0,
                            },
                            domain: [['id', 'in', task_ids]],
                        });
                    });

                    $('#line_today' + x['id']).on("click", function() {
                        var task_ids = x['task_ids']['today'];
                        var task_tree_id = x['task_tree_id'];
                        self.do_action({
                            res_model: 'project.task',
                            name: _t('Today Tasks - '+x['name']),
                            view_mode: 'tree',
                            views: [
                                [task_tree_id, 'list'],
                            ],
                            type: 'ir.actions.act_window',
                            target: 'new',
                            context: {'create': 0,
                            },
                            domain: [['id', 'in', task_ids]],
                        });
                    });
                    $('#line_overdue' + x['id']).on("click", function() {
                        var task_ids = x['task_ids']['overdue'];
                        var task_tree_id = x['task_tree_id'];
                        self.do_action({
                            res_model: 'project.task',
                            name: _t('Overdue Tasks - '+x['name']),
                            view_mode: 'tree',
                            views: [
                                [task_tree_id, 'list'],
                            ],
                            type: 'ir.actions.act_window',
                            target: 'new',
                            context: {'create': 0,
                            },
                            domain: [['id', 'in', task_ids]],
                        });
                    });

                    $('#line_pending' + x['id']).on("click", function() {
                        var task_ids = x['task_ids']['pending'];
                        var task_tree_id = x['task_tree_id'];
                        self.do_action({
                            res_model: 'project.task',
                            name: _t('Pending Tasks - '+x['name']),
                            view_mode: 'tree',
                            views: [
                                [task_tree_id, 'list'],
                            ],
                            type: 'ir.actions.act_window',
                            target: 'new',
                            context: {'create': 0,
                            },
                            domain: [['id', 'in', task_ids]],
                        });
                    });

                    $('#line_fixed' + x['id']).on("click", function() {
                        var task_ids = x['task_ids']['fixed'];
                        var task_tree_id = x['task_tree_id'];
                        self.do_action({
                            res_model: 'project.task',
                            name: _t('Fixed Tasks - '+x['name']),
                            view_mode: 'tree',
                            views: [
                                [task_tree_id, 'list'],
                            ],
                            type: 'ir.actions.act_window',
                            target: 'new',
                            context: {'create': 0,
                            },
                            domain: [['id', 'in', task_ids]],
                        });
                    });

                    $('#line_held' + x['id']).on("click", function() {
                        var task_ids = x['task_ids']['held'];
                        var task_tree_id = x['task_tree_id'];
                        self.do_action({
                            res_model: 'project.task',
                            name: _t('Held Tasks - '+x['name']),
                            view_mode: 'tree',
                            views: [
                                [task_tree_id, 'list'],
                            ],
                            type: 'ir.actions.act_window',
                            target: 'new',
                            context: {'create': 0,
                            },
                            domain: [['id', 'in', task_ids]],
                        });
                    });
                    $('#line_total' + x['id']).on("click", function() {
                        var task_ids = x['task_ids']['total'];
                        var task_tree_id = x['task_tree_id'];
                        self.do_action({
                            res_model: 'project.task',
                            name: _t('Total Tasks - '+x['name']),
                            view_mode: 'tree',
                            views: [
                                [task_tree_id, 'list'],
                            ],
                            type: 'ir.actions.act_window',
                            target: 'new',
                            context: {'create': 0,
                            },
                            domain: [['id', 'in', task_ids]],
                        });
                    });

                });
            })
        }

    }
//    );

KgDashboard.template = "KgDashboard"
registry.category("actions").add("kg_project_dashboard", KgDashboard)

//    core.action_registry.add('kg_project_dashboard', KgDashboardProject);
//
//    return KgDashboardProject;

//});