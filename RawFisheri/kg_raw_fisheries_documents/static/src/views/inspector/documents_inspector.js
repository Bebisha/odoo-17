/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { inspectorFields, DocumentsInspector } from "@documents/views/inspector/documents_inspector";

inspectorFields.push(
    "tag_id",
    "document_type_id",
    "document_date",
    "validity_start_date",
    "validity_end_date",
    "document_department_ids",
    "country_ids",
    "country_id",
    "counter_party_id",
    "original_file_name",
    "upload_date",
    "document_department_id",
    "company_id",
    "document_company_id",
    "vessel_id",
    "summary",
);

patch(DocumentsInspector.prototype, {
    getFieldProps(fieldName, additionalProps) {
        const rec = this.props.documents[0];
        const record = Object.create(rec.constructor.prototype);
        Object.assign(record, rec);
        const props = {
            record: record,
            name: fieldName,
            documents: [...this.props.documents],
            inspectorReadonly: !!record.data.lock_uid || this.isEditDisabled,
            lockAction: this.doLockAction.bind(this),
        };
        if (additionalProps) {
            Object.assign(props, additionalProps);
        }
        return props;
    },
});