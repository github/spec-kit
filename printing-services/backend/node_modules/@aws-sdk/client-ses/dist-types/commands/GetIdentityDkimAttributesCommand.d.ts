import { Command as $Command } from "@smithy/smithy-client";
import { MetadataBearer as __MetadataBearer } from "@smithy/types";
import { GetIdentityDkimAttributesRequest, GetIdentityDkimAttributesResponse } from "../models/models_0";
import { ServiceInputTypes, ServiceOutputTypes, SESClientResolvedConfig } from "../SESClient";
/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link GetIdentityDkimAttributesCommand}.
 */
export interface GetIdentityDkimAttributesCommandInput extends GetIdentityDkimAttributesRequest {
}
/**
 * @public
 *
 * The output of {@link GetIdentityDkimAttributesCommand}.
 */
export interface GetIdentityDkimAttributesCommandOutput extends GetIdentityDkimAttributesResponse, __MetadataBearer {
}
declare const GetIdentityDkimAttributesCommand_base: {
    new (input: GetIdentityDkimAttributesCommandInput): import("@smithy/smithy-client").CommandImpl<GetIdentityDkimAttributesCommandInput, GetIdentityDkimAttributesCommandOutput, SESClientResolvedConfig, ServiceInputTypes, ServiceOutputTypes>;
    new (input: GetIdentityDkimAttributesCommandInput): import("@smithy/smithy-client").CommandImpl<GetIdentityDkimAttributesCommandInput, GetIdentityDkimAttributesCommandOutput, SESClientResolvedConfig, ServiceInputTypes, ServiceOutputTypes>;
    getEndpointParameterInstructions(): import("@smithy/middleware-endpoint").EndpointParameterInstructions;
};
/**
 * <p>Returns the current status of Easy DKIM signing for an entity. For domain name
 *             identities, this operation also returns the DKIM tokens that are required for Easy DKIM
 *             signing, and whether Amazon SES has successfully verified that these tokens have been
 *             published.</p>
 *          <p>This operation takes a list of identities as input and returns the following
 *             information for each:</p>
 *          <ul>
 *             <li>
 *                <p>Whether Easy DKIM signing is enabled or disabled.</p>
 *             </li>
 *             <li>
 *                <p>A set of DKIM tokens that represent the identity. If the identity is an email
 *                     address, the tokens represent the domain of that address.</p>
 *             </li>
 *             <li>
 *                <p>Whether Amazon SES has successfully verified the DKIM tokens published in the
 *                     domain's DNS. This information is only returned for domain name identities, not
 *                     for email addresses.</p>
 *             </li>
 *          </ul>
 *          <p>This operation is throttled at one request per second and can only get DKIM attributes
 *             for up to 100 identities at a time.</p>
 *          <p>For more information about creating DNS records using DKIM tokens, go to the <a href="https://docs.aws.amazon.com/ses/latest/dg/send-email-authentication-dkim-easy-managing.html">Amazon SES
 *                 Developer Guide</a>.</p>
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { SESClient, GetIdentityDkimAttributesCommand } from "@aws-sdk/client-ses"; // ES Modules import
 * // const { SESClient, GetIdentityDkimAttributesCommand } = require("@aws-sdk/client-ses"); // CommonJS import
 * // import type { SESClientConfig } from "@aws-sdk/client-ses";
 * const config = {}; // type is SESClientConfig
 * const client = new SESClient(config);
 * const input = { // GetIdentityDkimAttributesRequest
 *   Identities: [ // IdentityList // required
 *     "STRING_VALUE",
 *   ],
 * };
 * const command = new GetIdentityDkimAttributesCommand(input);
 * const response = await client.send(command);
 * // { // GetIdentityDkimAttributesResponse
 * //   DkimAttributes: { // DkimAttributes // required
 * //     "<keys>": { // IdentityDkimAttributes
 * //       DkimEnabled: true || false, // required
 * //       DkimVerificationStatus: "Pending" || "Success" || "Failed" || "TemporaryFailure" || "NotStarted", // required
 * //       DkimTokens: [ // VerificationTokenList
 * //         "STRING_VALUE",
 * //       ],
 * //     },
 * //   },
 * // };
 *
 * ```
 *
 * @param GetIdentityDkimAttributesCommandInput - {@link GetIdentityDkimAttributesCommandInput}
 * @returns {@link GetIdentityDkimAttributesCommandOutput}
 * @see {@link GetIdentityDkimAttributesCommandInput} for command's `input` shape.
 * @see {@link GetIdentityDkimAttributesCommandOutput} for command's `response` shape.
 * @see {@link SESClientResolvedConfig | config} for SESClient's `config` shape.
 *
 * @throws {@link SESServiceException}
 * <p>Base exception class for all service exceptions from SES service.</p>
 *
 *
 * @example GetIdentityDkimAttributes
 * ```javascript
 * // The following example retrieves the Amazon SES Easy DKIM attributes for a list of identities:
 * const input = {
 *   Identities: [
 *     "example.com",
 *     "user@example.com"
 *   ]
 * };
 * const command = new GetIdentityDkimAttributesCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   DkimAttributes: {
 *     example.com: {
 *       DkimEnabled: true,
 *       DkimTokens: [
 *         "EXAMPLEjcs5xoyqytjsotsijas7236gr",
 *         "EXAMPLEjr76cvoc6mysspnioorxsn6ep",
 *         "EXAMPLEkbmkqkhlm2lyz77ppkulerm4k"
 *       ],
 *       DkimVerificationStatus: "Success"
 *     },
 *     user@example.com: {
 *       DkimEnabled: false,
 *       DkimVerificationStatus: "NotStarted"
 *     }
 *   }
 * }
 * *\/
 * ```
 *
 * @public
 */
export declare class GetIdentityDkimAttributesCommand extends GetIdentityDkimAttributesCommand_base {
    /** @internal type navigation helper, not in runtime. */
    protected static __types: {
        api: {
            input: GetIdentityDkimAttributesRequest;
            output: GetIdentityDkimAttributesResponse;
        };
        sdk: {
            input: GetIdentityDkimAttributesCommandInput;
            output: GetIdentityDkimAttributesCommandOutput;
        };
    };
}
