/* @odoo-module */
import { renderToElement } from "@web/core/utils/render";
import { jsonrpc } from "@web/core/network/rpc_service";
import publicWidget from "@web/legacy/js/public/public_widget";

export const PortalHomeCountersProductStock = publicWidget.Widget.extend({
    selector: '.o_website_product_search_move',

    events: {
        'keyup .o_portal_product_input_move': '_product_search_move',
    },

    async _product_search_move(result) {
        var product_name_stock = $('#product_name_input_move').val();

        await jsonrpc('/product/search/move', {
            args: {'product': product_name_stock}
        }).then(function(result){
            if (result !== 'false'){
                $('.product_move_results_table').html(renderToElement('productStockSearch', { result: result }));
                updateDownloadLink(product_name_stock);
            }
        }).catch(function(error){
            console.error('Error occurred during search:', error);
        });
    }
});

function updateDownloadLink(productName) {
    var downloadUrl = '/stock/download/move';
    if (productName) {
        downloadUrl += '?products_search_move=' + encodeURIComponent(productName);
    }
    $('#download_products_move').attr('href', downloadUrl);
}

publicWidget.registry.PortalHomeCountersProductStock = PortalHomeCountersProductStock;