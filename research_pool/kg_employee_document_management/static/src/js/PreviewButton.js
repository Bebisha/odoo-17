/** @odoo-module **/
     import FormController from 'web.FormController';
    import FormView from 'web.FormView';
    import viewRegistry from 'web.view_registry';

    var SaleFormController = FormController.extend({  buttons_template: 'button_near_create.buttons',
events: _.extend({}, ListController.prototype.events, {
       'click .open_wizard_action': '_MoreOptions',
   }),
   _MoreOptions: function () {
     console.log('Hello World!')
   }
});
var SFormView = FormView.extend({
        config: _.extend({}, FormView.prototype.config, {
            Controller: CrmFormController,
        }),
    });

viewRegistry.add('sale_order_blog', CrmFormView);

    export default {
        CrmFormController: CrmFormController,
        CrmFormView: CrmFormView,
    };