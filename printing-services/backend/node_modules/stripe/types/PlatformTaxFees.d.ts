// File generated from our OpenAPI spec

declare module 'stripe' {
  namespace Stripe {
    /**
     * The PlatformTaxFee object.
     */
    interface PlatformTaxFee {
      /**
       * Unique identifier for the object.
       */
      id: string;

      /**
       * String representing the object's type. Objects of the same type share the same value.
       */
      object: 'platform_tax_fee';

      /**
       * The Connected account that incurred this charge.
       */
      account: string;

      /**
       * The payment object that caused this tax to be inflicted.
       */
      source_transaction: string;

      /**
       * The type of tax (VAT).
       */
      type: string;
    }
  }
}
