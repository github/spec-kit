import { Command as $Command } from "@smithy/smithy-client";
import { MetadataBearer as __MetadataBearer } from "@smithy/types";
import { GetIdentityMailFromDomainAttributesRequest, GetIdentityMailFromDomainAttributesResponse } from "../models/models_0";
import { ServiceInputTypes, ServiceOutputTypes, SESClientResolvedConfig } from "../SESClient";
/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link GetIdentityMailFromDomainAttributesCommand}.
 */
export interface GetIdentityMailFromDomainAttributesCommandInput extends GetIdentityMailFromDomainAttributesRequest {
}
/**
 * @public
 *
 * The output of {@link GetIdentityMailFromDomainAttributesCommand}.
 */
export interface GetIdentityMailFromDomainAttributesCommandOutput extends GetIdentityMailFromDomainAttributesResponse, __MetadataBearer {
}
declare const GetIdentityMailFromDomainAttributesCommand_base: {
    new (input: GetIdentityMailFromDomainAttributesCommandInput): import("@smithy/smithy-client").CommandImpl<GetIdentityMailFromDomainAttributesCommandInput, GetIdentityMailFromDomainAttributesCommandOutput, SESClientResolvedConfig, ServiceInputTypes, ServiceOutputTypes>;
    new (input: GetIdentityMailFromDomainAttributesCommandInput): import("@smithy/smithy-client").CommandImpl<GetIdentityMailFromDomainAttributesCommandInput, GetIdentityMailFromDomainAttributesCommandOutput, SESClientResolvedConfig, ServiceInputTypes, ServiceOutputTypes>;
    getEndpointParameterInstructions(): import("@smithy/middleware-endpoint").EndpointParameterInstructions;
};
/**
 * <p>Returns the custom MAIL FROM attributes for a list of identities (email addresses :
 *             domains).</p>
 *          <p>This operation is throttled at one request per second and can only get custom MAIL
 *             FROM attributes for up to 100 identities at a time.</p>
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { SESClient, GetIdentityMailFromDomainAttributesCommand } from "@aws-sdk/client-ses"; // ES Modules import
 * // const { SESClient, GetIdentityMailFromDomainAttributesCommand } = require("@aws-sdk/client-ses"); // CommonJS import
 * // import type { SESClientConfig } from "@aws-sdk/client-ses";
 * const config = {}; // type is SESClientConfig
 * const client = new SESClient(config);
 * const input = { // GetIdentityMailFromDomainAttributesRequest
 *   Identities: [ // IdentityList // required
 *     "STRING_VALUE",
 *   ],
 * };
 * const command = new GetIdentityMailFromDomainAttributesCommand(input);
 * const response = await client.send(command);
 * // { // GetIdentityMailFromDomainAttributesResponse
 * //   MailFromDomainAttributes: { // MailFromDomainAttributes // required
 * //     "<keys>": { // IdentityMailFromDomainAttributes
 * //       MailFromDomain: "STRING_VALUE", // required
 * //       MailFromDomainStatus: "Pending" || "Success" || "Failed" || "TemporaryFailure", // required
 * //       BehaviorOnMXFailure: "UseDefaultValue" || "RejectMessage", // required
 * //     },
 * //   },
 * // };
 *
 * ```
 *
 * @param GetIdentityMailFromDomainAttributesCommandInput - {@link GetIdentityMailFromDomainAttributesCommandInput}
 * @returns {@link GetIdentityMailFromDomainAttributesCommandOutput}
 * @see {@link GetIdentityMailFromDomainAttributesCommandInput} for command's `input` shape.
 * @see {@link GetIdentityMailFromDomainAttributesCommandOutput} for command's `response` shape.
 * @see {@link SESClientResolvedConfig | config} for SESClient's `config` shape.
 *
 * @throws {@link SESServiceException}
 * <p>Base exception class for all service exceptions from SES service.</p>
 *
 *
 * @example GetIdentityMailFromDomainAttributes
 * ```javascript
 * // The following example returns the custom MAIL FROM attributes for an identity:
 * const input = {
 *   Identities: [
 *     "example.com"
 *   ]
 * };
 * const command = new GetIdentityMailFromDomainAttributesCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   MailFromDomainAttributes: {
 *     example.com: {
 *       BehaviorOnMXFailure: "UseDefaultValue",
 *       MailFromDomain: "bounces.example.com",
 *       MailFromDomainStatus: "Success"
 *     }
 *   }
 * }
 * *\/
 * ```
 *
 * @public
 */
export declare class GetIdentityMailFromDomainAttributesCommand extends GetIdentityMailFromDomainAttributesCommand_base {
    /** @internal type navigation helper, not in runtime. */
    protected static __types: {
        api: {
            input: GetIdentityMailFromDomainAttributesRequest;
            output: GetIdentityMailFromDomainAttributesResponse;
        };
        sdk: {
            input: GetIdentityMailFromDomainAttributesCommandInput;
            output: GetIdentityMailFromDomainAttributesCommandOutput;
        };
    };
}
