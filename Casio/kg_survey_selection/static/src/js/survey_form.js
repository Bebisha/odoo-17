/* @odoo-module */

import publicWidget from '@web/legacy/js/public/public_widget';
import SurveyPreloadImageMixin from "@survey/js/survey_preload_image_mixin";

publicWidget.registry.SurveyFormWidgetExtend = publicWidget.Widget.extend(SurveyPreloadImageMixin, {
    selector: '.o_survey_form',

    events: {
            'change .css_attribute_select': 'changeSelectionAns',
    },

    changeSelectionAns: function(ev){
        var closestDiv = $(ev.target).closest('.js_question-wrapper');
        closestDiv.find('.o_survey_selected').removeClass('o_survey_selected');
        closestDiv.find('.o_survey_choice_btn input').prop('checked', false);
        var radioElement = closestDiv.find('.o_survey_choice_btn input[value="' + ev.target.value + '"]');
        radioElement.prop('checked', true);
        var labelElement = radioElement.closest('.o_survey_choice_btn');
        labelElement.addClass('o_survey_selected');
    },

});

export default publicWidget.registry.SurveyFormWidgetExtend;