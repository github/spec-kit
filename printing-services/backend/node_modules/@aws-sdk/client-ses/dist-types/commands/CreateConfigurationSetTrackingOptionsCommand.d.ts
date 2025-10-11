import { Command as $Command } from "@smithy/smithy-client";
import { MetadataBearer as __MetadataBearer } from "@smithy/types";
import { CreateConfigurationSetTrackingOptionsRequest, CreateConfigurationSetTrackingOptionsResponse } from "../models/models_0";
import { ServiceInputTypes, ServiceOutputTypes, SESClientResolvedConfig } from "../SESClient";
/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link CreateConfigurationSetTrackingOptionsCommand}.
 */
export interface CreateConfigurationSetTrackingOptionsCommandInput extends CreateConfigurationSetTrackingOptionsRequest {
}
/**
 * @public
 *
 * The output of {@link CreateConfigurationSetTrackingOptionsCommand}.
 */
export interface CreateConfigurationSetTrackingOptionsCommandOutput extends CreateConfigurationSetTrackingOptionsResponse, __MetadataBearer {
}
declare const CreateConfigurationSetTrackingOptionsCommand_base: {
    new (input: CreateConfigurationSetTrackingOptionsCommandInput): import("@smithy/smithy-client").CommandImpl<CreateConfigurationSetTrackingOptionsCommandInput, CreateConfigurationSetTrackingOptionsCommandOutput, SESClientResolvedConfig, ServiceInputTypes, ServiceOutputTypes>;
    new (input: CreateConfigurationSetTrackingOptionsCommandInput): import("@smithy/smithy-client").CommandImpl<CreateConfigurationSetTrackingOptionsCommandInput, CreateConfigurationSetTrackingOptionsCommandOutput, SESClientResolvedConfig, ServiceInputTypes, ServiceOutputTypes>;
    getEndpointParameterInstructions(): import("@smithy/middleware-endpoint").EndpointParameterInstructions;
};
/**
 * <p>Creates an association between a configuration set and a custom domain for open and
 *             click event tracking. </p>
 *          <p>By default, images and links used for tracking open and click events are hosted on
 *             domains operated by Amazon SES. You can configure a subdomain of your own to handle these
 *             events. For information about using custom domains, see the <a href="https://docs.aws.amazon.com/ses/latest/dg/configure-custom-open-click-domains.html">Amazon SES Developer Guide</a>.</p>
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { SESClient, CreateConfigurationSetTrackingOptionsCommand } from "@aws-sdk/client-ses"; // ES Modules import
 * // const { SESClient, CreateConfigurationSetTrackingOptionsCommand } = require("@aws-sdk/client-ses"); // CommonJS import
 * // import type { SESClientConfig } from "@aws-sdk/client-ses";
 * const config = {}; // type is SESClientConfig
 * const client = new SESClient(config);
 * const input = { // CreateConfigurationSetTrackingOptionsRequest
 *   ConfigurationSetName: "STRING_VALUE", // required
 *   TrackingOptions: { // TrackingOptions
 *     CustomRedirectDomain: "STRING_VALUE",
 *   },
 * };
 * const command = new CreateConfigurationSetTrackingOptionsCommand(input);
 * const response = await client.send(command);
 * // {};
 *
 * ```
 *
 * @param CreateConfigurationSetTrackingOptionsCommandInput - {@link CreateConfigurationSetTrackingOptionsCommandInput}
 * @returns {@link CreateConfigurationSetTrackingOptionsCommandOutput}
 * @see {@link CreateConfigurationSetTrackingOptionsCommandInput} for command's `input` shape.
 * @see {@link CreateConfigurationSetTrackingOptionsCommandOutput} for command's `response` shape.
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
 * @throws {@link TrackingOptionsAlreadyExistsException} (client fault)
 *  <p>Indicates that the configuration set you specified already contains a TrackingOptions
 *             object.</p>
 *
 * @throws {@link SESServiceException}
 * <p>Base exception class for all service exceptions from SES service.</p>
 *
 *
 * @public
 */
export declare class CreateConfigurationSetTrackingOptionsCommand extends CreateConfigurationSetTrackingOptionsCommand_base {
    /** @internal type navigation helper, not in runtime. */
    protected static __types: {
        api: {
            input: CreateConfigurationSetTrackingOptionsRequest;
            output: {};
        };
        sdk: {
            input: CreateConfigurationSetTrackingOptionsCommandInput;
            output: CreateConfigurationSetTrackingOptionsCommandOutput;
        };
    };
}
