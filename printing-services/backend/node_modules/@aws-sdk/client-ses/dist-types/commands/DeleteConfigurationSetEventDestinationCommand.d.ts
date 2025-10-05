import { Command as $Command } from "@smithy/smithy-client";
import { MetadataBearer as __MetadataBearer } from "@smithy/types";
import { DeleteConfigurationSetEventDestinationRequest, DeleteConfigurationSetEventDestinationResponse } from "../models/models_0";
import { ServiceInputTypes, ServiceOutputTypes, SESClientResolvedConfig } from "../SESClient";
/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link DeleteConfigurationSetEventDestinationCommand}.
 */
export interface DeleteConfigurationSetEventDestinationCommandInput extends DeleteConfigurationSetEventDestinationRequest {
}
/**
 * @public
 *
 * The output of {@link DeleteConfigurationSetEventDestinationCommand}.
 */
export interface DeleteConfigurationSetEventDestinationCommandOutput extends DeleteConfigurationSetEventDestinationResponse, __MetadataBearer {
}
declare const DeleteConfigurationSetEventDestinationCommand_base: {
    new (input: DeleteConfigurationSetEventDestinationCommandInput): import("@smithy/smithy-client").CommandImpl<DeleteConfigurationSetEventDestinationCommandInput, DeleteConfigurationSetEventDestinationCommandOutput, SESClientResolvedConfig, ServiceInputTypes, ServiceOutputTypes>;
    new (input: DeleteConfigurationSetEventDestinationCommandInput): import("@smithy/smithy-client").CommandImpl<DeleteConfigurationSetEventDestinationCommandInput, DeleteConfigurationSetEventDestinationCommandOutput, SESClientResolvedConfig, ServiceInputTypes, ServiceOutputTypes>;
    getEndpointParameterInstructions(): import("@smithy/middleware-endpoint").EndpointParameterInstructions;
};
/**
 * <p>Deletes a configuration set event destination. Configuration set event destinations
 *             are associated with configuration sets, which enable you to publish email sending
 *             events. For information about using configuration sets, see the <a href="https://docs.aws.amazon.com/ses/latest/dg/monitor-sending-activity.html">Amazon SES
 *                 Developer Guide</a>.</p>
 *          <p>You can execute this operation no more than once per second.</p>
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { SESClient, DeleteConfigurationSetEventDestinationCommand } from "@aws-sdk/client-ses"; // ES Modules import
 * // const { SESClient, DeleteConfigurationSetEventDestinationCommand } = require("@aws-sdk/client-ses"); // CommonJS import
 * // import type { SESClientConfig } from "@aws-sdk/client-ses";
 * const config = {}; // type is SESClientConfig
 * const client = new SESClient(config);
 * const input = { // DeleteConfigurationSetEventDestinationRequest
 *   ConfigurationSetName: "STRING_VALUE", // required
 *   EventDestinationName: "STRING_VALUE", // required
 * };
 * const command = new DeleteConfigurationSetEventDestinationCommand(input);
 * const response = await client.send(command);
 * // {};
 *
 * ```
 *
 * @param DeleteConfigurationSetEventDestinationCommandInput - {@link DeleteConfigurationSetEventDestinationCommandInput}
 * @returns {@link DeleteConfigurationSetEventDestinationCommandOutput}
 * @see {@link DeleteConfigurationSetEventDestinationCommandInput} for command's `input` shape.
 * @see {@link DeleteConfigurationSetEventDestinationCommandOutput} for command's `response` shape.
 * @see {@link SESClientResolvedConfig | config} for SESClient's `config` shape.
 *
 * @throws {@link ConfigurationSetDoesNotExistException} (client fault)
 *  <p>Indicates that the configuration set does not exist.</p>
 *
 * @throws {@link EventDestinationDoesNotExistException} (client fault)
 *  <p>Indicates that the event destination does not exist.</p>
 *
 * @throws {@link SESServiceException}
 * <p>Base exception class for all service exceptions from SES service.</p>
 *
 *
 * @public
 */
export declare class DeleteConfigurationSetEventDestinationCommand extends DeleteConfigurationSetEventDestinationCommand_base {
    /** @internal type navigation helper, not in runtime. */
    protected static __types: {
        api: {
            input: DeleteConfigurationSetEventDestinationRequest;
            output: {};
        };
        sdk: {
            input: DeleteConfigurationSetEventDestinationCommandInput;
            output: DeleteConfigurationSetEventDestinationCommandOutput;
        };
    };
}
