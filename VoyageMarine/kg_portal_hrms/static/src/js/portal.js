/* @odoo-module */
import { onWillStart, useState, onWillUpdateProps, Component } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
$(document).ready(function() {
console.log('vishnu')

    this.orm = useService("orm");
        $('#employee_select').on('change', function(event) {
        const employeeId = $(event.target).val();  // Get the selected employee ID
        console.log('Employee ID:', employeeId);

        if (employeeId) {
            // Make an ORM call to fetch projects and tasks based on employee ID
            this.orm.call('hr.employee', 'fetch_projects_and_tasks', [employeeId])
                .then((result) => {
                    const projectSelect = $('#project_select');
                    const taskSelect = $('#task_select');

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
    });















                    function calculateDays() {
                        var startDate = new Date($('#start_date').val());
                        var endDate = new Date($('#end_date').val());
                        var errorMessage = '';

                        if (!isNaN(startDate.getTime()) && !isNaN(endDate.getTime())) {
                            if (endDate < startDate) {
                                errorMessage = 'End date cannot be earlier than start date.';
                                $('#number_of_days_display').val('');
                                $('#number_of_days_display').prop('readonly', true);
                               
                            } else {
                                var timeDiff = Math.abs(endDate.getTime() - startDate.getTime());
                                var diffDays = Math.ceil(timeDiff / (1000 * 3600 * 24)) + 1;
                                $('#number_of_days_display').val(diffDays);
                                $('#number_of_days_display').prop('readonly', false);

                            }
                        } else {
                            $('#number_of_days_display').val('');
                            $('#number_of_days_display').prop('readonly', true);

                        }

                        $('#date_error_message').text(errorMessage);
                    }

                    $('#start_date').on('change', calculateDays);
                    $('#end_date').on('change', calculateDays);


                    $('#time_off_form').on('submit', function(event) {
                        if ($('#number_of_days_display').val() === '') {
                            event.preventDefault();
                            alert('Please ensure the duration is calculated and not empty.');
                            $('#number_of_days_display').focus();
                        }
                    });


                });


//document.addEventListener('DOMContentLoaded', function() {
//    var holidayStatusSelect = document.getElementById('holiday_status_id');
//    var attachmentGroup = document.getElementById('attachment_group');
//
//    function toggleAttachmentField() {
//        var selectedOption = holidayStatusSelect.options[holidayStatusSelect.selectedIndex].text;
//        if (selectedOption === 'Sick Time Off') {
//            attachmentGroup.style.display = 'block';
//        } else {
//            attachmentGroup.style.display = 'none';
//        }
//    }
//
//    holidayStatusSelect.addEventListener('change', toggleAttachmentField);
//
//    // Initialize visibility on page load
//    toggleAttachmentField();
//});


