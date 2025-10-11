import { Command as $Command } from "@smithy/smithy-client";
import { MetadataBearer as __MetadataBearer } from "@smithy/types";
import { UpdateConfigurationSetTrackingOptionsRequest, UpdateConfigurationSetTrackingOptionsResponse } from "../models/models_0";
import { ServiceInputTypes, ServiceOutputTypes, SESClientResolvedConfig } from "../SESClient";
/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link UpdateConfigurationSetTrackingOptionsCommand}.
 */
export interface UpdateConfigurationSetTrackingOptionsCommandInput extends UpdateConfigurationSetTrackingOptionsRequest {
}
/**
 * @public
 *
 * The output of {@link UpdateConfigurationSetTrackingOptionsCommand}.
 */
export interface UpdateConfigurationSetTrackingOptionsCommandOutput extends UpdateConfigurationSetTrackingOptionsResponse, __MetadataBearer {
}
declare const UpdateConfigurationSetTrackingOptionsCommand_base: {
    new (input: UpdateConfigurationSetTrackingOptionsCommandInput): import("@smithy/smithy-client").CommandImpl<UpdateConfigurationSetTrackingOptionsCommandInput, UpdateConfigurationSetTrackingOptionsCommandOutput, SESClientResolvedConfig, ServiceInputTypes, ServiceOutputTypes>;
    new (input: UpdateConfigurationSetTrackingOptionsCommandInput): import("@smithy/smithy-client").CommandImpl<UpdateConfigurationSetTrackingOptionsCommandInput, UpdateConfigurationSetTrackingOptionsCommandOutput, SESClientResolvedConfig, ServiceInputTypes, ServiceOutputTypes>;
    getEndpointParameterInstructions(): import("@smithy/middleware-endpoint").EndpointParameterInstructions;
};
/**
 * <p>Modifies an association between a configuration set and a custom domain for open and
 *             click event tracking. </p>
 *          <p>By default, images and links used for tracking open and click events are hosted on
 *             domains operated by Amazon SES. You can configure a subdomain of your own to handle these
 *             events. For information about using custom domains, see the <a href="https://docs.aws.amazon.com/ses/latest/dg/configure-custom-open-click-domains.html">Amazon SES Developer Guide</a>.</p>
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { SESClient, UpdateConfigurationSetTrackingOptionsCommand } from "@aws-sdk/client-ses"; // ES Modules import
 * // const { SESClient, UpdateConfigurationSetTrackingOptionsCommand } = require("@aws-sdk/client-ses"); // CommonJS import
 * // import type { SESClientConfig } from "@aws-sdk/client-ses";
 * const config = {}; // type is SESClientConfig
 * const client = new SESClient(config);
 * const input = { // UpdateConfigurationSetTrackingOptionsRequest
 *   ConfigurationSetName: "STRING_VALUE", // required
 *   TrackingOptions: { // TrackingOptions
 *     CustomRedirectDomain: "STRING_VALUE",
 *   },
 * };
 * const command = new UpdateConfigurationSetTrackingOptionsCommand(input);
 * const response = await client.send(command);
 * // {};
 *
 * ```
 *
 * @param UpdateConfigurationSetTrackingOptionsCommandInput - {@link UpdateConfigurationSetTrackingOptionsCommandInput}
 * @returns {@link UpdateConfigurationSetTrackingOptionsCommandOutput}
 * @see {@link UpdateConfigurationSetTrackingOptionsCommandInput} for command's `input` shape.
 * @see {@link UpdateConfigurationSetTrackingOptionsCommandOutput} for command's `response` shape.
 * @see {@link SESClientResolvedConfig | config} for SESClient's `config` shape.
 *
 * @throws {@link ConfigurationSetDoesNotExistException} (client fault)
 *  <p>Indicates that the configuration set does not exist.</p>
 *
 * @throws {@link InvalidTrackingOptionsException} (client fault)
 *  <p>Indicates that the custom domain to be used for open and click tracking redirects is
 *             invalid. This error appears most often in the following situations:</p>
 *          <ul>
 *             <li>
 *                <p>When the tracking domain you specified is not verified in Amazon SES.</p>
 *             </li>
 *             <li>
 *                <p>When the tracking domain you specified is not a valid domain or
 *                     subdomain.</p>
 *             </li>
 *          </ul>
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
export declare class UpdateConfigurationSetTrackingOptionsCommand extends UpdateConfigurationSetTrackingOptionsCommand_base {
    /** @internal type navigation helper, not in runtime. */
    protected static __types: {
        api: {
            input: UpdateConfigurationSetTrackingOptionsRequest;
            output: {};
        };
        sdk: {
            input: UpdateConfigurationSetTrackingOptionsCommandInput;
            output: UpdateConfigurationSetTrackingOptionsCommandOutput;
        };
    };
}
