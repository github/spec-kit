// File generated from our OpenAPI spec

declare module 'stripe' {
  namespace Stripe {
    interface CustomerSessionCreateParams {
      /**
       * Configuration for each component. Exactly 1 component must be enabled.
       */
      components: CustomerSessionCreateParams.Components;

      /**
       * The ID of an existing customer for which to create the customer session.
       */
      customer: string;

      /**
       * Specifies which fields in the response should be expanded.
       */
      expand?: Array<string>;
    }

    namespace CustomerSessionCreateParams {
      interface Components {
        /**
         * Configuration for buy button.
         */
        buy_button?: Components.BuyButton;

        /**
         * Configuration for the pricing table.
         */
        pricing_table?: Components.PricingTable;
      }

      namespace Components {
        interface BuyButton {
          /**
           * Whether the buy button is enabled.
           */
          enabled: boolean;
        }

        interface PricingTable {
          /**
           * Whether the pricing table is enabled.
           */
          enabled: boolean;
        }
      }
    }

    class CustomerSessionsResource {
      /**
       * Creates a customer session object that includes a single-use client secret that you can use on your front-end to grant client-side API access for certain customer resources.
       */
      create(
        params: CustomerSessionCreateParams,
        options?: RequestOptions
      ): Promise<Stripe.Response<Stripe.CustomerSession>>;
    }
  }
}
