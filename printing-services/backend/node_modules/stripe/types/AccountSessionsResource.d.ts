// File generated from our OpenAPI spec

declare module 'stripe' {
  namespace Stripe {
    interface AccountSessionCreateParams {
      /**
       * The identifier of the account to create an Account Session for.
       */
      account: string;

      /**
       * Each key of the dictionary represents an embedded component, and each embedded component maps to its configuration (e.g. whether it has been enabled or not).
       */
      components: AccountSessionCreateParams.Components;

      /**
       * Specifies which fields in the response should be expanded.
       */
      expand?: Array<string>;
    }

    namespace AccountSessionCreateParams {
      interface Components {
        /**
         * Configuration for the account onboarding embedded component.
         */
        account_onboarding?: Components.AccountOnboarding;

        /**
         * Configuration for the documents embedded component.
         */
        documents?: Components.Documents;

        /**
         * Configuration for the payment details embedded component.
         */
        payment_details?: Components.PaymentDetails;

        /**
         * Configuration for the payments embedded component.
         */
        payments?: Components.Payments;

        /**
         * Configuration for the payouts embedded component.
         */
        payouts?: Components.Payouts;
      }

      namespace Components {
        interface AccountOnboarding {
          /**
           * Whether the embedded component is enabled.
           */
          enabled: boolean;

          /**
           * The list of features enabled in the embedded component.
           */
          features?: AccountOnboarding.Features;
        }

        namespace AccountOnboarding {
          interface Features {}
        }

        interface Documents {
          /**
           * Whether the embedded component is enabled.
           */
          enabled: boolean;

          /**
           * The list of features enabled in the embedded component.
           */
          features?: Documents.Features;
        }

        namespace Documents {
          interface Features {}
        }

        interface PaymentDetails {
          /**
           * Whether the embedded component is enabled.
           */
          enabled: boolean;

          /**
           * The list of features enabled in the embedded component.
           */
          features?: PaymentDetails.Features;
        }

        namespace PaymentDetails {
          interface Features {
            /**
             * Whether to allow capturing and cancelling payment intents. This is `true` by default.
             */
            capture_payments?: boolean;

            /**
             * Whether to allow connected accounts to manage destination charges that are created on behalf of them. This is `false` by default.
             */
            destination_on_behalf_of_charge_management?: boolean;

            /**
             * Whether to allow responding to disputes, including submitting evidence and accepting disputes. This is `true` by default.
             */
            dispute_management?: boolean;

            /**
             * Whether to allow sending refunds. This is `true` by default.
             */
            refund_management?: boolean;
          }
        }

        interface Payments {
          /**
           * Whether the embedded component is enabled.
           */
          enabled: boolean;

          /**
           * The list of features enabled in the embedded component.
           */
          features?: Payments.Features;
        }

        namespace Payments {
          interface Features {
            /**
             * Whether to allow capturing and cancelling payment intents. This is `true` by default.
             */
            capture_payments?: boolean;

            /**
             * Whether to allow connected accounts to manage destination charges that are created on behalf of them. This is `false` by default.
             */
            destination_on_behalf_of_charge_management?: boolean;

            /**
             * Whether to allow responding to disputes, including submitting evidence and accepting disputes. This is `true` by default.
             */
            dispute_management?: boolean;

            /**
             * Whether to allow sending refunds. This is `true` by default.
             */
            refund_management?: boolean;
          }
        }

        interface Payouts {
          /**
           * Whether the embedded component is enabled.
           */
          enabled: boolean;

          /**
           * The list of features enabled in the embedded component.
           */
          features?: Payouts.Features;
        }

        namespace Payouts {
          interface Features {
            /**
             * Whether to allow payout schedule to be changed. Default `true` when Stripe owns Loss Liability, default `false` otherwise.
             */
            edit_payout_schedule?: boolean;

            /**
             * Whether to allow creation of instant payouts. Default `true` when Stripe owns Loss Liability, default `false` otherwise.
             */
            instant_payouts?: boolean;

            /**
             * Whether to allow creation of standard payouts. Default `true` when Stripe owns Loss Liability, default `false` otherwise.
             */
            standard_payouts?: boolean;
          }
        }
      }
    }

    class AccountSessionsResource {
      /**
       * Creates a AccountSession object that includes a single-use token that the platform can use on their front-end to grant client-side API access.
       */
      create(
        params: AccountSessionCreateParams,
        options?: RequestOptions
      ): Promise<Stripe.Response<Stripe.AccountSession>>;
    }
  }
}
