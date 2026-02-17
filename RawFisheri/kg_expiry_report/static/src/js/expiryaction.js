/**@odoo-module **/
import { registry } from "@web/core/registry";
import { PassportExpiryPopup } from "./expirypopup.js";
import { Component } from "@odoo/owl";

class PassportExpiryAction extends Component {
    async openPopup() {
        const dialog = new PassportExpiryPopup(this);
        dialog.on('confirm', async ({ date }) => {
            // Use the new Odoo 17 ORM call to update the passport expiry date.
            // Make sure that the record id is passed as an array.
            await this.orm.call('hr.employee', 'action_update_passport_expiry', [[this.props.resId], date]);
            dialog.close();
        });
        dialog.on('cancel', () => dialog.close());
        dialog.mount(document.body);
    }
}
PassportExpiryAction.template = `
    <button class="btn btn-primary" t-on-click="openPopup">Confirm</button>
`;

registry.category("actions").add("passport_expiry_action", PassportExpiryAction);
