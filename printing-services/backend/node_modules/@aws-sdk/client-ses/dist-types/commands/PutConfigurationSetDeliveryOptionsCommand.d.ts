import { Command as $Command } from "@smithy/smithy-client";
import { MetadataBearer as __MetadataBearer } from "@smithy/types";
import { PutConfigurationSetDeliveryOptionsRequest, PutConfigurationSetDeliveryOptionsResponse } from "../models/models_0";
import { ServiceInputTypes, ServiceOutputTypes, SESClientResolvedConfig } from "../SESClient";
/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link PutConfigurationSetDeliveryOptionsCommand}.
 */
export interface PutConfigurationSetDeliveryOptionsCommandInput extends PutConfigurationSetDeliveryOptionsRequest {
}
/**
 * @public
 *
 * The output of {@link PutConfigurationSetDeliveryOptionsCommand}.
 */
export interface PutConfigurationSetDeliveryOptionsCommandOutput extends PutConfigurationSetDeliveryOptionsResponse, __MetadataBearer {
}
declare const PutConfigurationSetDeliveryOptionsCommand_base: {
    new (input: PutConfigurationSetDeliveryOptionsCommandInput): import("@smithy/smithy-client").CommandImpl<PutConfigurationSetDeliveryOptionsCommandInput, PutConfigurationSetDeliveryOptionsCommandOutput, SESClientResolvedConfig, ServiceInputTypes, ServiceOutputTypes>;
    new (input: PutConfigurationSetDeliveryOptionsCommandInput): import("@smithy/smithy-client").CommandImpl<PutConfigurationSetDeliveryOptionsCommandInput, PutConfigurationSetDeliveryOptionsCommandOutput, SESClientResolvedConfig, ServiceInputTypes, ServiceOutputTypes>;
    getEndpointParameterInstructions(): import("@smithy/middleware-endpoint").EndpointParameterInstructions;
};
/**
 * <p>Adds or updates the delivery options for a configuration set.</p>
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { SESClient, PutConfigurationSetDeliveryOptionsCommand } from "@aws-sdk/client-ses"; // ES Modules import
 * // const { SESClient, PutConfigurationSetDeliveryOptionsCommand } = require("@aws-sdk/client-ses"); // CommonJS import
 * // import type { SESClientConfig } from "@aws-sdk/client-ses";
 * const config = {}; // type is SESClientConfig
 * const client = new SESClient(config);
 * const input = { // PutConfigurationSetDeliveryOptionsRequest
 *   ConfigurationSetName: "STRING_VALUE", // required
 *   DeliveryOptions: { // DeliveryOptions
 *     TlsPolicy: "Require" || "Optional",
 *   },
 * };
 * const command = new PutConfigurationSetDeliveryOptionsCommand(input);
 * const response = await client.send(command);
 * // {};
 *
 * ```
 *
 * @param PutConfigurationSetDeliveryOptionsCommandInput - {@link PutConfigurationSetDeliveryOptionsCommandInput}
 * @returns {@link PutConfigurationSetDeliveryOptionsCommandOutput}
 * @see {@link PutConfigurationSetDeliveryOptionsCommandInput} for command's `input` shape.
 * @see {@link PutConfigurationSetDeliveryOptionsCommandOutput} for command's `response` shape.
 * @see {@link SESClientResolvedConfig | config} for SESClient's `config` shape.
 *
 * @throws {@link ConfigurationSetDoesNotExistException} (client fault)
 *  <p>Indicates that the configuration set does not exist.</p>
 *
 * @throws {@link InvalidDeliveryOptionsException} (client fault)
 *  <p>Indicates that provided delivery option is invalid.</p>
 *
 * @throws {@link SESServiceException}
 * <p>Base exception class for all service exceptions from SES service.</p>
 *
 *
 * @public
 */
export declare class PutConfigurationSetDeliveryOptionsCommand extends PutConfigurationSetDeliveryOptionsCommand_base {
    /** @internal type navigation helper, not in runtime. */
    protected static __types: {
        api: {
            input: PutConfigurationSetDeliveryOptionsRequest;
            output: {};
        };
        sdk: {
            input: PutConfigurationSetDeliveryOptionsCommandInput;
            output: PutConfigurationSetDeliveryOptionsCommandOutput;
        };
    };
}
