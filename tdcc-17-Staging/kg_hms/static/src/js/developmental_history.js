odoo.define('kg_hms.developmental_history_form', function(require){
    "use strict";
    var publicWidget = require('web.public.widget');
    var core = require('web.core');
    var ajax = require('web.ajax');
    var rpc = require('web.rpc');
    const Dialog = require('web.Dialog');
    var _t = core._t;

    publicWidget.registry.developmentHistory = publicWidget.Widget.extend({
        selector: '#developmental_history_form',
        events: {
               'click .show_dev_page_2': '_showDevelopmentalFormPage2',
        },

         _showDevelopmentalFormPage2: async function (ev) {
            console.log("_showDevelopmentalFormPage2")
            ev.preventDefault();
            var self = this;
            console.log(values,"VALUESSSSSS")
            var values = await self.DataSave();
            console.log(values,"NEWWWWWW")
            ajax.jsonRpc('/dev-history-pg1-values', 'call', values).then(function (json_data) {
                window.location.href = '/Dev_History/page-2?values=' + encodeURIComponent(json_data['list_val'])});
          },


         DataSave: async function() {
            var self = this;
            var form = $('#dev_form');
            var values = {};
            var serialize_form = form.serializeArray();

            let today_date = $(form).find('input[name="dev_today_date"]').val();
            let first_name = $(form).find('input[name="dev_first_name"]').val();
            let dev_last_name = $(form).find('input[name="dev_last_name"]').val();
            let dev_dob = $(form).find('input[name="dev_dob"]').val();
            let age = $(form).find('input[name="age"]').val();
            let nationality = $(form).find("select[id='nationality']").val()
            let gender = $(form).find('input[name="gender"]').val();
            let dev_language = $(form).find('input[name="dev_language"]').val();
            let dev_dominant_language = $(form).find('input[name="dev_dominant_language"]').val();
            let dev_current_school = $(form).find('input[name="dev_current_school"]').val();
            let dev_school_year_grade = $(form).find('input[name="dev_school_year_grade"]').val();
            let dev_classroom_teacher = $(form).find('input[name="dev_classroom_teacher"]').val();
            let dev_mother_first_name = $(form).find('input[name="dev_mother_first_name"]').val();
            let mother_phone = $(form).find('input[name="mother_phone"]').val();
            let mother_nationality = $(form).find('select[id="mother_nationality"]').val();
            let dev_mother_email = $(form).find('input[name="dev_mother_email"]').val();
            let dev_father_name = $(form).find('input[name="dev_father_name"]').val();
            let father_phone = $(form).find('input[name="father_phone"]').val();
            let father_nationality = $(form).find('select[id="father_nationality"]').val();
            let dev_father_email = $(form).find('input[name="dev_father_email"]').val();
            let dev_home_address = $(form).find('input[name="dev_home_address"]').val();
            let dev_previous_place = $(form).find('input[name="dev_previous_place"]').val();
            let dev_siblings = $(form).find('input[name="dev_siblings"]').val();
            let dev_grand_parents = $(form).find('input[name="dev_grand_parents"]').val();
            let dev_others = $(form).find('input[name="dev_others"]').val();

            values['today_date'] = today_date
            values['first_name'] = first_name
            values['dev_last_name'] = dev_last_name
            values['dev_dob'] = dev_dob
            values['age'] = age
            values['nationality'] = nationality
            values['gender'] = gender
            values['dev_language'] = dev_language
            values['dev_dominant_language'] = dev_dominant_language
            values['dev_current_school'] = dev_current_school
            values['dev_school_year_grade'] = dev_school_year_grade
            values['dev_classroom_teacher'] = dev_classroom_teacher
            values['dev_mother_first_name'] = dev_mother_first_name
            values['mother_phone'] = mother_phone
            values['mother_nationality'] = mother_nationality
            values['dev_mother_email'] = dev_mother_email
            values['dev_father_name'] = dev_father_name
            values['father_phone'] = father_phone
            values['father_nationality'] = father_nationality
            values['dev_father_email'] = dev_father_email
            values['dev_home_address'] = dev_home_address
            values['dev_previous_place'] = dev_previous_place
            values['dev_siblings'] = dev_siblings
            values['dev_grand_parents'] = dev_grand_parents
            values['dev_others'] = dev_others
            return new Promise(function(resolve, reject) {
                resolve(values);
            });
        },

    });

});

