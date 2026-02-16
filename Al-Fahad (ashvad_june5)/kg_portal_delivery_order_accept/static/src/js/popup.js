odoo.define('kg_portal_delivery_order_accept.confirmation_popup', function (require) {
    'use strict';

    var core = require('web.core');
    var Widget = require('web.Widget');
    var rpc = require('web.rpc');

    var _t = core._t;

    var ConfirmationPopup = Widget.extend({
        template: 'confirmation_popup_template',

        showConfirmationPopup: function (pickingId) {
            this.pickingId = pickingId;
            this.$el.modal();
        },

        confirmAcceptance: function () {
            // Call the backend to accept the picking and create an invoice
            rpc.query({
                route: '/my/delivery/order/accept/' + this.pickingId,
            }).then(function (result) {
                if (result) {
                    // Close the popup and perform any additional actions
                    this.$el.modal('hide');
                    // Optionally, refresh the page or update UI elements
                    // window.location.reload();
                } else {
                    // Handle error scenarios
                }
            }.bind(this));
        },
    });

    core.action_registry.add('confirmation_popup', ConfirmationPopup);

    return ConfirmationPopup;
});