/**@odoo-module **/
import { Dialog } from "@web/core/dialog/dialog";
import { Component, onWillStart, useState } from "@odoo/owl";

export class PassportExpiryPopup extends Component {
    setup() {
        this.state = useState({
            expiry_date: "",
        });
    }

    confirm() {
        this.trigger('confirm', { date: this.state.expiry_date });
    }

    cancel() {
        this.trigger('cancel');
    }
}

PassportExpiryPopup.template = `
    <Dialog title="Update Passport Expiry Date" size="medium">
        <div class="p-3">
            <label for="expiry_date">New Expiry Date:</label>
            <input type="date" t-model="state.expiry_date" id="expiry_date" class="form-control"/>
        </div>
        <footer>
            <button type="button" class="btn btn-secondary" t-on-click="cancel">No</button>
            <button type="button" class="btn btn-primary" t-on-click="confirm">Yes</button>
        </footer>
    </Dialog>
`;
