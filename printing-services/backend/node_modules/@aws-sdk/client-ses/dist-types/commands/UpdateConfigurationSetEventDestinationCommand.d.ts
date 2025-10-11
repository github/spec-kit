import { Command as $Command } from "@smithy/smithy-client";
import { MetadataBearer as __MetadataBearer } from "@smithy/types";
import { UpdateConfigurationSetEventDestinationRequest, UpdateConfigurationSetEventDestinationResponse } from "../models/models_0";
import { ServiceInputTypes, ServiceOutputTypes, SESClientResolvedConfig } from "../SESClient";
/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link UpdateConfigurationSetEventDestinationCommand}.
 */
export interface UpdateConfigurationSetEventDestinationCommandInput extends UpdateConfigurationSetEventDestinationRequest {
}
/**
 * @public
 *
 * The output of {@link UpdateConfigurationSetEventDestinationCommand}.
 */
export interface UpdateConfigurationSetEventDestinationCommandOutput extends UpdateConfigurationSetEventDestinationResponse, __MetadataBearer {
}
declare const UpdateConfigurationSetEventDestinationCommand_base: {
    new (input: UpdateConfigurationSetEventDestinationCommandInput): import("@smithy/smithy-client").CommandImpl<UpdateConfigurationSetEventDestinationCommandInput, UpdateConfigurationSetEventDestinationCommandOutput, SESClientResolvedConfig, ServiceInputTypes, ServiceOutputTypes>;
    new (input: UpdateConfigurationSetEventDestinationCommandInput): import("@smithy/smithy-client").CommandImpl<UpdateConfigurationSetEventDestinationCommandInput, UpdateConfigurationSetEventDestinationCommandOutput, SESClientResolvedConfig, ServiceInputTypes, ServiceOutputTypes>;
    getEndpointParameterInstructions(): import("@smithy/middleware-endpoint").EndpointParameterInstructions;
};
/**
 * <p>Updates the event destination of a configuration set. Event destinations are
 *             associated with configuration sets, which enable you to publish email sending events to
 *             Amazon CloudWatch, Amazon Kinesis Firehose, or Amazon Simple Notification Service (Amazon SNS). For information about using configuration sets,
 *             see <a href="https://docs.aws.amazon.com/ses/latest/dg/monitor-sending-activity.html">Monitoring Your Amazon SES Sending Activity</a> in the <i>Amazon SES Developer
 *                 Guide.</i>
 *          </p>
 *          <note>
 *             <p>When you create or update an event destination, you must provide one, and only
 *                 one, destination. The destination can be Amazon CloudWatch, Amazon Kinesis Firehose, or Amazon Simple Notification Service
 *                 (Amazon SNS).</p>
 *          </note>
 *          <p>You can execute this operation no more than once per second.</p>
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { SESClient, UpdateConfigurationSetEventDestinationCommand } from "@aws-sdk/client-ses"; // ES Modules import
 * // const { SESClient, UpdateConfigurationSetEventDestinationCommand } = require("@aws-sdk/client-ses"); // CommonJS import
 * // import type { SESClientConfig } from "@aws-sdk/client-ses";
 * const config = {}; // type is SESClientConfig
 * const client = new SESClient(config);
 * const input = { // UpdateConfigurationSetEventDestinationRequest
 *   ConfigurationSetName: "STRING_VALUE", // required
 *   EventDestination: { // EventDestination
 *     Name: "STRING_VALUE", // required
 *     Enabled: true || false,
 *     MatchingEventTypes: [ // EventTypes // required
 *       "send" || "reject" || "bounce" || "complaint" || "delivery" || "open" || "click" || "renderingFailure",
 *     ],
 *     KinesisFirehoseDestination: { // KinesisFirehoseDestination
 *       IAMRoleARN: "STRING_VALUE", // required
 *       DeliveryStreamARN: "STRING_VALUE", // required
 *     },
 *     CloudWatchDestination: { // CloudWatchDestination
 *       DimensionConfigurations: [ // CloudWatchDimensionConfigurations // required
 *         { // CloudWatchDimensionConfiguration
 *           DimensionName: "STRING_VALUE", // required
 *           DimensionValueSource: "messageTag" || "emailHeader" || "linkTag", // required
 *           DefaultDimensionValue: "STRING_VALUE", // required
 *         },
 *       ],
 *     },
 *     SNSDestination: { // SNSDestination
 *       TopicARN: "STRING_VALUE", // required
 *     },
 *   },
 * };
 * const command = new UpdateConfigurationSetEventDestinationCommand(input);
 * const response = await client.send(command);
 * // {};
 *
 * ```
 *
 * @param UpdateConfigurationSetEventDestinationCommandInput - {@link UpdateConfigurationSetEventDestinationCommandInput}
 * @returns {@link UpdateConfigurationSetEventDestinationCommandOutput}
 * @see {@link UpdateConfigurationSetEventDestinationCommandInput} for command's `input` shape.
 * @see {@link UpdateConfigurationSetEventDestinationCommandOutput} for command's `response` shape.
 * @see {@link SESClientResolvedConfig | config} for SESClient's `config` shape.
 *
 * @throws {@link ConfigurationSetDoesNotExistException} (client fault)
 *  <p>Indicates that the configuration set does not exist.</p>
 *
 * @throws {@link EventDestinationDoesNotExistException} (client fault)
 *  <p>Indicates that the event destination does not exist.</p>
 *
 * @throws {@link InvalidCloudWatchDestinationException} (client fault)
 *  <p>Indicates that the Amazon CloudWatch destination is invalid. See the error message for
 *             details.</p>
 *
 * @throws {@link InvalidFirehoseDestinationException} (client fault)
 *  <p>Indicates that the Amazon Kinesis Firehose destination is invalid. See the error
 *             message for details.</p>
 *
 * @throws {@link InvalidSNSDestinationException} (client fault)
 *  <p>Indicates that the Amazon Simple Notification Service (Amazon SNS) destination is
 *             invalid. See the error message for details.</p>
 *
 * @throws {@link SESServiceException}
 * <p>Base exception class for all service exceptions from SES service.</p>
 *
 *
 * @public
 */
export declare class UpdateConfigurationSetEventDestinationCommand extends UpdateConfigurationSetEventDestinationCommand_base {
    /** @internal type navigation helper, not in runtime. */
    protected static __types: {
        api: {
            input: UpdateConfigurationSetEventDestinationRequest;
            output: {};
        };
        sdk: {
            input: UpdateConfigurationSetEventDestinationCommandInput;
            output: UpdateConfigurationSetEventDestinationCommandOutput;
        };
    };
}
