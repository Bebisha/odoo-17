//** @odoo-module **/

import { ListRenderer } from "@web/views/list/list_renderer";
import { registry } from "@web/core/registry";
import { Pager } from "@web/core/pager/pager";
import { KanbanRenderer } from "@web/views/kanban/kanban_renderer";
import { X2ManyField, x2ManyField } from "@web/views/fields/x2many/x2many_field";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { useService } from '@web/core/utils/hooks';
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { useX2ManyCrud } from "@web/views/fields/relational_utils";

export class O2mMultiDelete extends X2ManyField {
    setup() {
        super.setup();
        X2ManyField.components = { Pager, KanbanRenderer };
        this.orm = useService('orm');
        this.dialog = useService("dialog");
        this.operations = useX2ManyCrud(() => this.props.value, true);

    }

    async previewSelected() {
        console.log('Selected Records:', this.operations);

        if (!this.selectedRecords || this.selectedRecords.length === 0) {
            console.log('No records selected');
            this.dialog.add(AlertDialog, {
                title: 'No Selection',
                body: 'Please select a record to preview.',
                type: 'warning',
                buttons: [
                    {
                        text: 'OK',
                        close: true,
                    }
                ],
            });
            return;
        }

        const selectedRecordId = this.selectedRecords[0];
        console.log('Selected Record ID:', selectedRecordId);

        // Fetch the record data from the backend
        const { data } = await this.orm.call('sale.order', 'read', [selectedRecordId], {
            fields: ['preview_pdf']
        });

        if (!data || !data[0]) {
            console.log('Selected record not found');
            this.dialog.add(AlertDialog, {
                title: 'Record Not Found',
                body: 'The selected record could not be found.',
                type: 'warning',
                buttons: [
                    {
                        text: 'OK',
                        close: true,
                    }
                ],
            });
            return;
        }

        const imageData = data[0].preview_pdf;
        console.log('Image Data:', imageData);

        if (!imageData) {
            console.log('No image data available');
            this.dialog.add(AlertDialog, {
                title: 'No Image Available',
                body: 'The selected record does not have an image to preview.',
                type: 'warning',
                buttons: [
                    {
                        text: 'OK',
                        close: true,
                    }
                ],
            });
            return;
        }

        // Convert binary data to base64 format
        const base64Image = this.toBase64(imageData);
        const imageUrl = `data:application/pdf;base64,${base64Image}`;
        console.log('Image URL:', imageUrl);

        this.dialog.add(ConfirmationDialog, {
            title: 'Preview PDF',
            body: `<iframe src="${imageUrl}" style="width: 100%; height: 600px;" frameborder="0"></iframe>`,
            size: 'lg',
            buttons: [
                {
                    text: 'Close',
                    close: true,
                }
            ],
        });
    }

    toBase64(binaryData) {
        const binaryString = Array.from(new Uint8Array(binaryData))
            .map(byte => String.fromCharCode(byte))
            .join('');
        return window.btoa(binaryString);
    }
}

export const O2manyMultiDelete = {
    ...x2ManyField,
    component: O2mMultiDelete,
};

O2mMultiDelete.template = "O2mMultiDelete";
registry.category("fields").add("one2many_delete", O2manyMultiDelete);
