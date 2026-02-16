/** @odoo-module */

import { useService } from "@web/core/utils/hooks";
import { ListController } from "@web/views/list/list_controller";

export class ButtonNearCreateButtonController extends ListController {
    setup() {
        super.setup();
        this.orm = useService("orm");
        this.state = {
            salespersons: []
        };
        this.loadSalespersons();
        this.fetchProjectDetails();
    }

    async loadSalespersons() {
        try {
            const salespersons = await this.orm.call('res.users', 'search_read', [
                [['groups_id', 'in', this.env.ref('sales_team.group_sale_salesman').ids]],
                ['id', 'name']
            ]);
            this.state.salespersons = salespersons;
            this.model.notify();
        } catch (error) {
            console.error('Error loading salespersons:', error);
        }
    }
    async fetchProjectDetails() {
        try {
            const projectData = await this.orm.searchRead('res.users', [],
            ['name']);

            this.state.projects = projectData.map(project => ({
                id: project.id,
                name: project.name,
                projectManager: project.user_id ? project.user_id[1] : 'Unassigned',
//                assignees: project.task_ids.length,
                startDate: project.date_start,
                endDate: project.date
            }));

            console.log("Fetched Project Details:", this.state.projects);
        } catch (error) {
            console.error("Error fetching project details:", error);
        }
    }

    async selectProject(ev) {
    try {
        const projectId = ev.target.value;
        const users = await this.orm.searchRead('res.users', [['id','=',projectId]])
        console.log(users[0].id,'userssss')
        const projects = await this.orm.searchRead('crm.lead', [['user_id', '=', users[0].id]],
            []);
        console.log(projects,'projectsssssssss')

    } catch (error) {
        console.error('Error loading projects:', error);
    }
    }


//    async onSelectProject(ev) {
//    console .log('uuuuuuuuuuuuuuuuuuuu',ev)
//    const projectId = ev.target.value;
//
//
//    try {
//        console.log('Selected Project ID:', projectId);
//    } catch (error) {
//        console.error('Error selecting project:', error);
//    }
//    }
//
//    async selectProject(projectId) {
//    console.log(projectId,'projectttt')
//        try {
//            const projects = await rpc.query({
//                model: 'crm.lead',
//                method: 'search_read',
//                args: [],
//            });
//            this.state.selectProject = projects;
//        } catch (error) {
//            console.error('Error loading projects:', error);
//        }
//    }


    async onCreateProject() {
        // Implement your project creation logic here
    }
}

