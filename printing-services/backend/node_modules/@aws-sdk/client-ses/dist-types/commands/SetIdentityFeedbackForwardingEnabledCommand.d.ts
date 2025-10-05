import { Command as $Command } from "@smithy/smithy-client";
import { MetadataBearer as __MetadataBearer } from "@smithy/types";
import { SetIdentityFeedbackForwardingEnabledRequest, SetIdentityFeedbackForwardingEnabledResponse } from "../models/models_0";
import { ServiceInputTypes, ServiceOutputTypes, SESClientResolvedConfig } from "../SESClient";
/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link SetIdentityFeedbackForwardingEnabledCommand}.
 */
export interface SetIdentityFeedbackForwardingEnabledCommandInput extends SetIdentityFeedbackForwardingEnabledRequest {
}
/**
 * @public
 *
 * The output of {@link SetIdentityFeedbackForwardingEnabledCommand}.
 */
export interface SetIdentityFeedbackForwardingEnabledCommandOutput extends SetIdentityFeedbackForwardingEnabledResponse, __MetadataBearer {
}
declare const SetIdentityFeedbackForwardingEnabledCommand_base: {
    new (input: SetIdentityFeedbackForwardingEnabledCommandInput): import("@smithy/smithy-client").CommandImpl<SetIdentityFeedbackForwardingEnabledCommandInput, SetIdentityFeedbackForwardingEnabledCommandOutput, SESClientResolvedConfig, ServiceInputTypes, ServiceOutputTypes>;
    new (input: SetIdentityFeedbackForwardingEnabledCommandInput): import("@smithy/smithy-client").CommandImpl<SetIdentityFeedbackForwardingEnabledCommandInput, SetIdentityFeedbackForwardingEnabledCommandOutput, SESClientResolvedConfig, ServiceInputTypes, ServiceOutputTypes>;
    getEndpointParameterInstructions(): import("@smithy/middleware-endpoint").EndpointParameterInstructions;
};
/**
 * <p>Given an identity (an email address or a domain), enables or disables whether Amazon SES
 *             forwards bounce and complaint notifications as email. Feedback forwarding can only be
 *             disabled when Amazon Simple Notification Service (Amazon SNS) topics are specified for both bounces and
 *             complaints.</p>
 *          <note>
 *             <p>Feedback forwarding does not apply to delivery notifications. Delivery
 *                 notifications are only available through Amazon SNS.</p>
 *          </note>
 *          <p>You can execute this operation no more than once per second.</p>
 *          <p>For more information about using notifications with Amazon SES, see the <a href="https://docs.aws.amazon.com/ses/latest/dg/monitor-sending-activity-using-notifications.html">Amazon SES
 *                 Developer Guide</a>.</p>
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { SESClient, SetIdentityFeedbackForwardingEnabledCommand } from "@aws-sdk/client-ses"; // ES Modules import
 * // const { SESClient, SetIdentityFeedbackForwardingEnabledCommand } = require("@aws-sdk/client-ses"); // CommonJS import
 * // import type { SESClientConfig } from "@aws-sdk/client-ses";
 * const config = {}; // type is SESClientConfig
 * const client = new SESClient(config);
 * const input = { // SetIdentityFeedbackForwardingEnabledRequest
 *   Identity: "STRING_VALUE", // required
 *   ForwardingEnabled: true || false, // required
 * };
 * const command = new SetIdentityFeedbackForwardingEnabledCommand(input);
 * const response = await client.send(command);
 * // {};
 *
 * ```
 *
 * @param SetIdentityFeedbackForwardingEnabledCommandInput - {@link SetIdentityFeedbackForwardingEnabledCommandInput}
 * @returns {@link SetIdentityFeedbackForwardingEnabledCommandOutput}
 * @see {@link SetIdentityFeedbackForwardingEnabledCommandInput} for command's `input` shape.
 * @see {@link SetIdentityFeedbackForwardingEnabledCommandOutput} for command's `response` shape.
 * @see {@link SESClientResolvedConfig | config} for SESClient's `config` shape.
 *
 * @throws {@link SESServiceException}
 * <p>Base exception class for all service exceptions from SES service.</p>
 *
 *
 * @example SetIdentityFeedbackForwardingEnabled
 * ```javascript
 * // The following example configures Amazon SES to forward an identity's bounces and complaints via email:
 * const input = {
 *   ForwardingEnabled: true,
 *   Identity: "user@example.com"
 * };
 * const command = new SetIdentityFeedbackForwardingEnabledCommand(input);
 * const response = await client.send(command);
 * /* response is
 * { /* metadata only *\/ }
 * *\/
 * ```
 *
 * @public
 */
export declare class SetIdentityFeedbackForwardingEnabledCommand extends SetIdentityFeedbackForwardingEnabledCommand_base {
    /** @internal type navigation helper, not in runtime. */
    protected static __types: {
        api: {
            input: SetIdentityFeedbackForwardingEnabledRequest;
            output: {};
        };
        sdk: {
            input: SetIdentityFeedbackForwardingEnabledCommandInput;
            output: SetIdentityFeedbackForwardingEnabledCommandOutput;
        };
    };
}
