// File generated from our OpenAPI spec

declare module 'stripe' {
  namespace Stripe {
    namespace Billing {
      interface MeterEventCreateParams {
        /**
         * The name of the meter event. Corresponds with the `event_name` field on a meter.
         */
        event_name: string;

        /**
         * The payload of the event. This must contain a field with the event's numerical value and a field to map the event to a customer.
         */
        payload: {
          [key: string]: string;
        };

        /**
         * The time of the event. Measured in seconds since the Unix epoch.
         */
        timestamp: number;

        /**
         * Specifies which fields in the response should be expanded.
         */
        expand?: Array<string>;

        /**
         * A unique identifier for the event. If not provided, one will be generated. We recommend using a globally unique identifier for this. We'll enforce uniqueness within a rolling 24 hour period.
         */
        identifier?: string;
      }

      class MeterEventsResource {
        /**
         * Creates a billing meter event
         */
        create(
          params: MeterEventCreateParams,
          options?: RequestOptions
        ): Promise<Stripe.Response<Stripe.Billing.MeterEvent>>;
      }
    }
  }
}
