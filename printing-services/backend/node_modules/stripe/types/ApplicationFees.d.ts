// File generated from our OpenAPI spec

declare module 'stripe' {
  namespace Stripe {
    /**
     * The ApplicationFee object.
     */
    interface ApplicationFee {
      /**
       * Unique identifier for the object.
       */
      id: string;

      /**
       * String representing the object's type. Objects of the same type share the same value.
       */
      object: 'application_fee';

      /**
       * ID of the Stripe account this fee was taken from.
       */
      account: string | Stripe.Account;

      /**
       * Amount earned, in cents (or local equivalent).
       */
      amount: number;

      /**
       * Amount in cents (or local equivalent) refunded (can be less than the amount attribute on the fee if a partial refund was issued)
       */
      amount_refunded: number;

      /**
       * ID of the Connect application that earned the fee.
       */
      application: string | Stripe.Application;

      /**
       * Balance transaction that describes the impact of this collected application fee on your account balance (not including refunds).
       */
      balance_transaction: string | Stripe.BalanceTransaction | null;

      /**
       * ID of the charge that the application fee was taken from.
       */
      charge: string | Stripe.Charge;

      /**
       * Time at which the object was created. Measured in seconds since the Unix epoch.
       */
      created: number;

      /**
       * Three-letter [ISO currency code](https://www.iso.org/iso-4217-currency-codes.html), in lowercase. Must be a [supported currency](https://stripe.com/docs/currencies).
       */
      currency: string;

      /**
       * Has the value `true` if the object exists in live mode or the value `false` if the object exists in test mode.
       */
      livemode: boolean;

      /**
       * ID of the corresponding charge on the platform account, if this fee was the result of a charge using the `destination` parameter.
       */
      originating_transaction: string | Stripe.Charge | null;

      /**
       * Whether the fee has been fully refunded. If the fee is only partially refunded, this attribute will still be false.
       */
      refunded: boolean;

      /**
       * A list of refunds that have been applied to the fee.
       */
      refunds: ApiList<Stripe.FeeRefund>;
    }
  }
}
