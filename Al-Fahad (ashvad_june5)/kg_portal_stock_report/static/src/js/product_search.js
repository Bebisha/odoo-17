/* @odoo-module */
import { renderToElement } from "@web/core/utils/render";
import { jsonrpc } from "@web/core/network/rpc_service";
import publicWidget from "@web/legacy/js/public/public_widget";

export const PortalHomeCountersProduct = publicWidget.Widget.extend({
    selector: '.o_website_product_search',

    events: {
        'keyup .o_portal_product_input': '_product_search',
    },

    async _product_search(event) {
        var product_name = $('#product_name_input').val();

        try {
            const result = await jsonrpc('/product/search', {
                args: { 'product': product_name }
            });
            if (result !== 'false') {
                $('.product_results_table').html(renderToElement('productSearch', { result: result }));
                updateDownloadLink(product_name);
            }
        } catch (error) {
            console.error('Error occurred during search:', error);
        }
    }
});

function updateDownloadLink(productName) {
    var downloadUrl = '/stock/download/print';
    if (productName) {
        downloadUrl += '?products_search=' + encodeURIComponent(productName);
    }
    $('#download_products').attr('href', downloadUrl);
}

publicWidget.registry.PortalHomeCountersProduct = PortalHomeCountersProduct;
