/*@odoo-module */
import { registry } from '@web/core/registry';
import { useService } from "@web/core/utils/hooks";
const { Component, onMounted } = owl;
import { _t } from "@web/core/l10n/translation";
import { useState } from "@odoo/owl";

export class PoolDashboard extends Component {
    setup() {
        this.action = useService("action");
        this.orm = useService("orm");
        this.rpc = useService("rpc");
        onMounted(this.onMounted.bind(this));
        this.state = useState({
            result: [],
            pool_lines: [], // Separate state for pool lines
            running_count: 0,
            engagement_count: 0,
        });
    }

    async onMounted() {
        await this.render_dashboards();
    }

    async render_dashboards() {
        const result = await this.orm.call('project.task', 'resource_pool_dashboard', [[]]);

        // Set the main state for tasks and pool lines separately
        this.state.result = result.task_details;
        this.state.pool_lines = result.pool_lines; // Separate pool lines
        console.log('Result:', result);

        this.state.running_count = result.running_count;
        this.state.running = result.running_project;
        this.state.engagement_count = result.engagement_count;
        this.state.engagement = result.engagement_project;
    }

    async redirectToRunningProjects() {
        this.action.doAction({
            name: _t("Running Projects"),
            type: 'ir.actions.act_window',
            res_model: 'project.project',
            view_mode: 'tree,form',
            domain: [['id', 'in', this.state.running]],
            views: [
                [false, 'list'],
                [false, 'form'],
            ],
            target: 'current'
        });
    }

    async redirectToEngagementProjects() {
        this.action.doAction({
            name: _t("Engagement Projects"),
            type: 'ir.actions.act_window',
            res_model: 'project.project',
            view_mode: 'tree,form',
            domain: [['id', 'in', this.state.engagement]],
            views: [
                [false, 'list'],
                [false, 'form'],
            ],
            target: 'current'
        });
    }
}

PoolDashboard.template = "PoolDashboard";
registry.category("actions").add("pool_dashboard", PoolDashboard);