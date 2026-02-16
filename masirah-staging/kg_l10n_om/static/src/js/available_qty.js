odoo.define('kg_pos_with_onhand_qty.available_qty', function (require) {
"use strict";
var {PosGlobalState,OrderLIne} = require('point_of_sale.models');
const Registries = require('point_of_sale.Registries');
const ProductItem = require('point_of_sale.ProductItem')
const NewPosGlobalState = (PosGlobalState) => class NewPosGlobalState extends PosGlobalState {

     async _processData(loadedData){
        await super._processData(...arguments);
        this.stock_quant = loadedData['stock.quant'];
    }
}
Registries.Model.extend(PosGlobalState,NewPosGlobalState)

  const NewProductItem = (ProductItem) =>
  class extends ProductItem {

        get onhand_qty() {
            const product_id = this.props.product;
            var check_id = this.props.product.id
            var value;

            const result = this.env.pos.stock_quant.filter( function (elem)  { return elem.product_id[0] == check_id } );
            if ( result.length){
                if (result[0].quantity>=0){
                   value = result[0].quantity
                }
                else{
                     value = 0
                }
            }
            else{
                  value = 0
 };
              return value
        }

     }

    Registries.Component.extend(ProductItem, NewProductItem);

});
