import { Command as $Command } from "@smithy/smithy-client";
import { MetadataBearer as __MetadataBearer } from "@smithy/types";
import { DeleteConfigurationSetTrackingOptionsRequest, DeleteConfigurationSetTrackingOptionsResponse } from "../models/models_0";
import { ServiceInputTypes, ServiceOutputTypes, SESClientResolvedConfig } from "../SESClient";
/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link DeleteConfigurationSetTrackingOptionsCommand}.
 */
export interface DeleteConfigurationSetTrackingOptionsCommandInput extends DeleteConfigurationSetTrackingOptionsRequest {
}
/**
 * @public
 *
 * The output of {@link DeleteConfigurationSetTrackingOptionsCommand}.
 */
export interface DeleteConfigurationSetTrackingOptionsCommandOutput extends DeleteConfigurationSetTrackingOptionsResponse, __MetadataBearer {
}
declare const DeleteConfigurationSetTrackingOptionsCommand_base: {
    new (input: DeleteConfigurationSetTrackingOptionsCommandInput): import("@smithy/smithy-client").CommandImpl<DeleteConfigurationSetTrackingOptionsCommandInput, DeleteConfigurationSetTrackingOptionsCommandOutput, SESClientResolvedConfig, ServiceInputTypes, ServiceOutputTypes>;
    new (input: DeleteConfigurationSetTrackingOptionsCommandInput): import("@smithy/smithy-client").CommandImpl<DeleteConfigurationSetTrackingOptionsCommandInput, DeleteConfigurationSetTrackingOptionsCommandOutput, SESClientResolvedConfig, ServiceInputTypes, ServiceOutputTypes>;
    getEndpointParameterInstructions(): import("@smithy/middleware-endpoint").EndpointParameterInstructions;
};
/**
 * <p>Deletes an association between a configuration set and a custom domain for open and
 *             click event tracking.</p>
 *          <p>By default, images and links used for tracking open and click events are hosted on
 *             domains operated by Amazon SES. You can configure a subdomain of your own to handle these
 *             events. For information about using custom domains, see the <a href="https://docs.aws.amazon.com/ses/latest/dg/configure-custom-open-click-domains.html">Amazon SES Developer Guide</a>.</p>
 *          <note>
 *             <p>Deleting this kind of association results in emails sent using the specified
 *                 configuration set to capture open and click events using the standard,
 *                 Amazon SES-operated domains.</p>
 *          </note>
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { SESClient, DeleteConfigurationSetTrackingOptionsCommand } from "@aws-sdk/client-ses"; // ES Modules import
 * // const { SESClient, DeleteConfigurationSetTrackingOptionsCommand } = require("@aws-sdk/client-ses"); // CommonJS import
 * // import type { SESClientConfig } from "@aws-sdk/client-ses";
 * const config = {}; // type is SESClientConfig
 * const client = new SESClient(config);
 * const input = { // DeleteConfigurationSetTrackingOptionsRequest
 *   ConfigurationSetName: "STRING_VALUE", // required
 * };
 * const command = new DeleteConfigurationSetTrackingOptionsCommand(input);
 * const response = await client.send(command);
 * // {};
 *
 * ```
 *
 * @param DeleteConfigurationSetTrackingOptionsCommandInput - {@link DeleteConfigurationSetTrackingOptionsCommandInput}
 * @returns {@link DeleteConfigurationSetTrackingOptionsCommandOutput}
 * @see {@link DeleteConfigurationSetTrackingOptionsCommandInput} for command's `input` shape.
 * @see {@link DeleteConfigurationSetTrackingOptionsCommandOutput} for command's `response` shape.
 * @see {@link SESClientResolvedConfig | config} for SESClient's `config` shape.
 *
 * @throws {@link ConfigurationSetDoesNotExistException} (client fault)
 *  <p>Indicates that the configuration set does not exist.</p>
 *
 * @throws {@link TrackingOptionsDoesNotExistException} (client fault)
 *  <p>Indicates that the TrackingOptions object you specified does not exist.</p>
 *
 * @throws {@link SESServiceException}
 * <p>Base exception class for all service exceptions from SES service.</p>
 *
 *
 * @public
 */
export declare class DeleteConfigurationSetTrackingOptionsCommand extends DeleteConfigurationSetTrackingOptionsCommand_base {
    /** @internal type navigation helper, not in runtime. */
    protected static __types: {
        api: {
            input: DeleteConfigurationSetTrackingOptionsRequest;
            output: {};
        };
        sdk: {
            input: DeleteConfigurationSetTrackingOptionsCommandInput;
            output: DeleteConfigurationSetTrackingOptionsCommandOutput;
        };
    };
}
