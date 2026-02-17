/** @odoo-module **/

import { GanttRenderer } from '@web_gantt/gantt_renderer';
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { onWillUpdateProps, onWillStart } from "@odoo/owl";

patch(GanttRenderer.prototype, {

    setup() {
        super.setup(...arguments);
        this.orm = useService("orm");
        this.activeModel = this.model.env.searchModel.resModel;
        if (this.activeModel == 'project.task'){
            onWillStart(async () => {
                this.activeModel = this.model.env.searchModel.resModel;
                this.rows = await this.getAssignedUser(this.rows);
            });
            onWillUpdateProps(async () => {
                this.activeModel = this.model.env.searchModel.resModel;
                this.rows = await this.getAssignedUser(this.rows);
            });
        }
    },

    async getAssignedUser(rows) {
        const values = await this.orm.call(
            "project.task",
            "get_gannt_values",
             [rows]);
        return values;
    },

});
