// File generated from our OpenAPI spec

declare module 'stripe' {
  namespace Stripe {
    namespace TestHelpers {
      namespace Treasury {
        interface OutboundTransferFailParams {
          /**
           * Specifies which fields in the response should be expanded.
           */
          expand?: Array<string>;
        }
      }

      namespace Treasury {
        interface OutboundTransferPostParams {
          /**
           * Specifies which fields in the response should be expanded.
           */
          expand?: Array<string>;
        }
      }

      namespace Treasury {
        interface OutboundTransferReturnOutboundTransferParams {
          /**
           * Specifies which fields in the response should be expanded.
           */
          expand?: Array<string>;

          /**
           * Details about a returned OutboundTransfer.
           */
          returned_details?: OutboundTransferReturnOutboundTransferParams.ReturnedDetails;
        }

        namespace OutboundTransferReturnOutboundTransferParams {
          interface ReturnedDetails {
            /**
             * Reason for the return.
             */
            code?: ReturnedDetails.Code;
          }

          namespace ReturnedDetails {
            type Code =
              | 'account_closed'
              | 'account_frozen'
              | 'bank_account_restricted'
              | 'bank_ownership_changed'
              | 'declined'
              | 'incorrect_account_holder_name'
              | 'invalid_account_number'
              | 'invalid_currency'
              | 'no_account'
              | 'other';
          }
        }
      }

      namespace Treasury {
        class OutboundTransfersResource {
          /**
           * Transitions a test mode created OutboundTransfer to the failed status. The OutboundTransfer must already be in the processing state.
           */
          fail(
            id: string,
            params?: OutboundTransferFailParams,
            options?: RequestOptions
          ): Promise<Stripe.Response<Stripe.Treasury.OutboundTransfer>>;
          fail(
            id: string,
            options?: RequestOptions
          ): Promise<Stripe.Response<Stripe.Treasury.OutboundTransfer>>;

          /**
           * Transitions a test mode created OutboundTransfer to the posted status. The OutboundTransfer must already be in the processing state.
           */
          post(
            id: string,
            params?: OutboundTransferPostParams,
            options?: RequestOptions
          ): Promise<Stripe.Response<Stripe.Treasury.OutboundTransfer>>;
          post(
            id: string,
            options?: RequestOptions
          ): Promise<Stripe.Response<Stripe.Treasury.OutboundTransfer>>;

          /**
           * Transitions a test mode created OutboundTransfer to the returned status. The OutboundTransfer must already be in the processing state.
           */
          returnOutboundTransfer(
            id: string,
            params?: OutboundTransferReturnOutboundTransferParams,
            options?: RequestOptions
          ): Promise<Stripe.Response<Stripe.Treasury.OutboundTransfer>>;
          returnOutboundTransfer(
            id: string,
            options?: RequestOptions
          ): Promise<Stripe.Response<Stripe.Treasury.OutboundTransfer>>;
        }
      }
    }
  }
}
