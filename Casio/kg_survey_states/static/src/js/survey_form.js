/* @odoo-module */

import publicWidget from '@web/legacy/js/public/public_widget';
import SurveyPreloadImageMixin from "@survey/js/survey_preload_image_mixin";

publicWidget.registry.SurveyFormWidgetQuestionExtend = publicWidget.Widget.extend(SurveyPreloadImageMixin, {
    selector: '.o_survey_form',

    events: {
            'change .onchange-selection-many2one': '_onChangeQuestions',
    },

    init() {
        this._super(...arguments);
        this.rpc = this.bindService("rpc");
    },
/*
    onChangeQuestions: function(ev){
        console.log('testtttttttt',ev.target.value)
        var closestDiv = $(ev.target).closest('.js_question-wrapper');
        closestDiv.find('.o_survey_selected').removeClass('o_survey_selected');
        closestDiv.find('.o_survey_choice_btn input').prop('checked', false);
        var radioElement = closestDiv.find('.o_survey_choice_btn input[value="' + ev.target.value + '"]');
        radioElement.prop('checked', true);
        var labelElement = radioElement.closest('.o_survey_choice_btn');
        labelElement.addClass('o_survey_selected');
    },
*/

     _onChangeQuestions: function(ev){
        console.log('testtttttttt',ev.target.value);
        const answer_id = ev.target.value;
        const model = $(ev.target).find(':selected').data('model')
        console.log(model,'modelmodel')
        this.rpc("/fetch/survey/answers", {answer_id,model}, { silent: true }).then(function(res){
            console.log('resres',res);
        });
    },

});

export default publicWidget.registry.SurveyFormWidgetQuestionExtend;