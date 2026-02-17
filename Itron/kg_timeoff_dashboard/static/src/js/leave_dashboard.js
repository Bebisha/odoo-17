/**@odoo-module **/
import { registry } from '@web/core/registry';
import { useService } from "@web/core/utils/hooks";
const { Component, onMounted } = owl;
import { _t } from "@web/core/l10n/translation";
import { useState } from "@odoo/owl";

export class LeaveDashboard extends Component {
    setup() {
        this.action = useService("action");
        this.orm = useService("orm");
        this.rpc = useService("rpc");
        onMounted(this.onMounted.bind(this));
        this.state = useState({
            result: [],
        });
    }

    async onMounted() {
        await this.render_dashboards();
    }

    async render_dashboards() {
        const result = await this.orm.call('hr.leave', 'get_leave_details', [[]]);

        this.state.result = result;
    }
    async tot_leaves(e,oid) {
            e.stopPropagation();
            e.preventDefault();
            var options = {
                on_reverse_breadcrumb: this.on_reverse_breadcrumb,
            };

            for(var x  of this.state.result){
                if(x['id'] == oid){
                    var leaves = x['leaves'];
                }
            }
                                    console.log("ffffffffffffffffffffffffffff",leaves)

            this.action.doAction({
                name: _t("Leaves"),
                type: 'ir.actions.act_window',
                res_model: 'hr.leave',
                domain: [
                    ["id", "in", leaves]
                ],
                view_mode: 'tree,form',
                views: [
                    [false, 'list'],
                    [false, 'form'],
                ],
                target: 'current'
            }, options);
        }
}

LeaveDashboard.template = "LeaveDashboard";
registry.category("actions").add("timeoff_leave_dashboard", LeaveDashboard);
