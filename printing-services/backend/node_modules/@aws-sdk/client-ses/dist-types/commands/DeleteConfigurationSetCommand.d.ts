import { Command as $Command } from "@smithy/smithy-client";
import { MetadataBearer as __MetadataBearer } from "@smithy/types";
import { DeleteConfigurationSetRequest, DeleteConfigurationSetResponse } from "../models/models_0";
import { ServiceInputTypes, ServiceOutputTypes, SESClientResolvedConfig } from "../SESClient";
/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link DeleteConfigurationSetCommand}.
 */
export interface DeleteConfigurationSetCommandInput extends DeleteConfigurationSetRequest {
}
/**
 * @public
 *
 * The output of {@link DeleteConfigurationSetCommand}.
 */
export interface DeleteConfigurationSetCommandOutput extends DeleteConfigurationSetResponse, __MetadataBearer {
}
declare const DeleteConfigurationSetCommand_base: {
    new (input: DeleteConfigurationSetCommandInput): import("@smithy/smithy-client").CommandImpl<DeleteConfigurationSetCommandInput, DeleteConfigurationSetCommandOutput, SESClientResolvedConfig, ServiceInputTypes, ServiceOutputTypes>;
    new (input: DeleteConfigurationSetCommandInput): import("@smithy/smithy-client").CommandImpl<DeleteConfigurationSetCommandInput, DeleteConfigurationSetCommandOutput, SESClientResolvedConfig, ServiceInputTypes, ServiceOutputTypes>;
    getEndpointParameterInstructions(): import("@smithy/middleware-endpoint").EndpointParameterInstructions;
};
/**
 * <p>Deletes a configuration set. Configuration sets enable you to publish email sending
 *             events. For information about using configuration sets, see the <a href="https://docs.aws.amazon.com/ses/latest/dg/monitor-sending-activity.html">Amazon SES
 *                 Developer Guide</a>.</p>
 *          <p>You can execute this operation no more than once per second.</p>
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { SESClient, DeleteConfigurationSetCommand } from "@aws-sdk/client-ses"; // ES Modules import
 * // const { SESClient, DeleteConfigurationSetCommand } = require("@aws-sdk/client-ses"); // CommonJS import
 * // import type { SESClientConfig } from "@aws-sdk/client-ses";
 * const config = {}; // type is SESClientConfig
 * const client = new SESClient(config);
 * const input = { // DeleteConfigurationSetRequest
 *   ConfigurationSetName: "STRING_VALUE", // required
 * };
 * const command = new DeleteConfigurationSetCommand(input);
 * const response = await client.send(command);
 * // {};
 *
 * ```
 *
 * @param DeleteConfigurationSetCommandInput - {@link DeleteConfigurationSetCommandInput}
 * @returns {@link DeleteConfigurationSetCommandOutput}
 * @see {@link DeleteConfigurationSetCommandInput} for command's `input` shape.
 * @see {@link DeleteConfigurationSetCommandOutput} for command's `response` shape.
 * @see {@link SESClientResolvedConfig | config} for SESClient's `config` shape.
 *
 * @throws {@link ConfigurationSetDoesNotExistException} (client fault)
 *  <p>Indicates that the configuration set does not exist.</p>
 *
 * @throws {@link SESServiceException}
 * <p>Base exception class for all service exceptions from SES service.</p>
 *
 *
 * @public
 */
export declare class DeleteConfigurationSetCommand extends DeleteConfigurationSetCommand_base {
    /** @internal type navigation helper, not in runtime. */
    protected static __types: {
        api: {
            input: DeleteConfigurationSetRequest;
            output: {};
        };
        sdk: {
            input: DeleteConfigurationSetCommandInput;
            output: DeleteConfigurationSetCommandOutput;
        };
    };
}
