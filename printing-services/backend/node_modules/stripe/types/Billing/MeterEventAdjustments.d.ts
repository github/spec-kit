// File generated from our OpenAPI spec

declare module 'stripe' {
  namespace Stripe {
    namespace Billing {
      /**
       * A billing meter event adjustment represents the status of a meter event adjustment.
       */
      interface MeterEventAdjustment {
        /**
         * String representing the object's type. Objects of the same type share the same value.
         */
        object: 'billing.meter_event_adjustment';

        cancel: MeterEventAdjustment.Cancel;

        /**
         * The name of the meter event. Corresponds with the `event_name` field on a meter.
         */
        event_name: string;

        /**
         * Has the value `true` if the object exists in live mode or the value `false` if the object exists in test mode.
         */
        livemode: boolean;

        /**
         * The meter event adjustment's status.
         */
        status: MeterEventAdjustment.Status;

        /**
         * Specifies whether to cancel a single event or a range of events for a time period.
         */
        type: 'cancel';
      }

      namespace MeterEventAdjustment {
        interface Cancel {
          /**
           * Unique identifier for the event.
           */
          identifier: string;
        }

        type Status = 'complete' | 'pending';
      }
    }
  }
}
