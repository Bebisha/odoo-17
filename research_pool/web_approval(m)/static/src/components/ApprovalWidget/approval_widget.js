/** @odoo-module **/

import { registry } from "@web/core/registry";
import { usePopover } from "@web/core/popover/popover_hook";
import { useService } from "@web/core/utils/hooks";
import { parseDate, formatDate } from "@web/core/l10n/dates";
import { localization } from "@web/core/l10n/localization";
import { session } from "@web/session";

import { formatMonetary } from "@web/views/fields/formatters";

const { Component, onWillUpdateProps, onMounted } = owl;
const { useState } = owl;

class ApproverInfoPopOver extends Component {}
ApproverInfoPopOver.template = "web_approval.ApproverInfoPopOver";


export class ApprovalField extends Component {

    setup() {
        this.popover = usePopover();
        this.orm = useService("orm");
        this.state = useState({
            values: this.props.value
        });
        onMounted(this.onMounted);
        onWillUpdateProps((nextProps) => {
            this.state.values = nextProps.value;
        });
    }


   onMounted() {
        $('[data-toggle="popover"]').popover();
   }

   getUserImageUrl(userId) {
        return `/web/image?model=res.users&field=avatar_128&id=${userId}`;
   }

   async getApprovalData() {
        return await this.orm.call(this.props.record.resModel, "generate_approval_json", [this.fieldAmount], {});
   }

   onInfoClick(ev, values) {
        if (this.popoverCloseFn) {
            this.closePopover();
        }
        console.log(values)
        this.popoverCloseFn = this.popover.add(
            ev.currentTarget,
            ApproverInfoPopOver,
            {
                data: values,
            },
            {
                position: localization.direction === "rtl" ? "bottom" : "left",
            },
        );
    }

    closePopover() {
        this.popoverCloseFn();
        this.popoverCloseFn = null;
    }

    get fieldAmount() {
        return this.props.record.data[this.props.amountField]
    }
}
ApprovalField.template = "web_approval.ApprovalField";
ApprovalField.supportedTypes = ["text", "char"];

ApprovalField.extractProps = ({ attrs }) => {
    console.log(attrs);  // Debugging line
    return {
        amountField: attrs.options ? attrs.options.amount_field : null,
    };
};


registry.category("fields").add("approval", ApprovalField);
