$(document).ready(function() {
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


