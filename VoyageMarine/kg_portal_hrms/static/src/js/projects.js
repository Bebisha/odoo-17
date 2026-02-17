/** @odoo-module **/

import { useService } from "@web/core/utils/hooks";
import { useState, onWillStart } from "@odoo/owl";  // Importing OWL lifecycle hooks
import { Component } from "@odoo/owl";

export class DynamicSelectsComponent extends Component {
    setup() {

        this.orm = useService('orm');  // Getting ORM service
        this.state = useState({});  // Initializing component state (optional)

        // Using onWillStart to handle asynchronous calls before component is rendered
        onWillStart(async () => {
            await this.fetchHierarchy(this.props.record.resId);  // Fetch data before component starts
            this._initializeSelects();
        });
    }

    async fetchHierarchy(recordId) {
        console.log('Fetching hierarchy for record ID:', recordId);

        // Simulating an async fetch operation, such as calling an ORM method or API
        try {
            const result = await this.orm.call('hr.employee', 'fetch_projects_and_tasks', [recordId]);
            console.log('Fetched result:', result);
            // You can perform further actions with the result here if needed
        } catch (error) {
            console.error('Error fetching hierarchy:', error);
        }
    }

    _initializeSelects() {
        console.log('Initializing the select dropdowns');

        // Attach the change event to the employee select dropdown
        $(document).on("change", "#employee_select", this._onEmployeeChange.bind(this));

        // Trigger the change event when the page is ready (if needed)
        const employeeId = $("#employee_select").val();
        console.log('Employee ID on initialize:', employeeId);

        // If employee is already selected, trigger the change event
        if (employeeId) {
            this._onEmployeeChange({ target: { value: employeeId } });
        }
    }

    _onEmployeeChange(event) {
        const employeeId = $(event.target).val();  // Get the selected employee ID
        console.log('Employee ID:', employeeId);

        if (employeeId) {
            // Making an ORM call to fetch projects and tasks based on employee ID
            this.orm.call('hr.employee', 'fetch_projects_and_tasks', [employeeId])
                .then((result) => {
                    const projectSelect = $('#project_select');
                    const taskSelect = $('#task_select');

                    // Clear previous options
                    projectSelect.html('<option value="">Select a project</option>');
                    taskSelect.html('<option value="">Select a task</option>');

                    console.log('Projects:', result.projects);
                    console.log('Tasks:', result.tasks);

                    // Populate the project dropdown
                    result.projects.forEach((project) => {
                        const option = $('<option></option>').val(project.id).text(project.name);
                        projectSelect.append(option);
                    });

                    // Populate the task dropdown
                    result.tasks.forEach((task) => {
                        const option = $('<option></option>')
                            .val(task.id)
                            .text(task.name)
                            .attr('data-project-id', task.project_id.id);
                        taskSelect.append(option);
                    });
                })
                .catch((error) => {
                    console.error("Error fetching data:", error);
                });
        }
    }
}
