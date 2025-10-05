import { Command as $Command } from "@smithy/smithy-client";
import { MetadataBearer as __MetadataBearer } from "@smithy/types";
import { GetIdentityVerificationAttributesRequest, GetIdentityVerificationAttributesResponse } from "../models/models_0";
import { ServiceInputTypes, ServiceOutputTypes, SESClientResolvedConfig } from "../SESClient";
/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link GetIdentityVerificationAttributesCommand}.
 */
export interface GetIdentityVerificationAttributesCommandInput extends GetIdentityVerificationAttributesRequest {
}
/**
 * @public
 *
 * The output of {@link GetIdentityVerificationAttributesCommand}.
 */
export interface GetIdentityVerificationAttributesCommandOutput extends GetIdentityVerificationAttributesResponse, __MetadataBearer {
}
declare const GetIdentityVerificationAttributesCommand_base: {
    new (input: GetIdentityVerificationAttributesCommandInput): import("@smithy/smithy-client").CommandImpl<GetIdentityVerificationAttributesCommandInput, GetIdentityVerificationAttributesCommandOutput, SESClientResolvedConfig, ServiceInputTypes, ServiceOutputTypes>;
    new (input: GetIdentityVerificationAttributesCommandInput): import("@smithy/smithy-client").CommandImpl<GetIdentityVerificationAttributesCommandInput, GetIdentityVerificationAttributesCommandOutput, SESClientResolvedConfig, ServiceInputTypes, ServiceOutputTypes>;
    getEndpointParameterInstructions(): import("@smithy/middleware-endpoint").EndpointParameterInstructions;
};
/**
 * <p>Given a list of identities (email addresses and/or domains), returns the verification
 *             status and (for domain identities) the verification token for each identity.</p>
 *          <p>The verification status of an email address is "Pending" until the email address owner
 *             clicks the link within the verification email that Amazon SES sent to that address. If the
 *             email address owner clicks the link within 24 hours, the verification status of the
 *             email address changes to "Success". If the link is not clicked within 24 hours, the
 *             verification status changes to "Failed." In that case, to verify the email address, you
 *             must restart the verification process from the beginning.</p>
 *          <p>For domain identities, the domain's verification status is "Pending" as Amazon SES searches
 *             for the required TXT record in the DNS settings of the domain. When Amazon SES detects the
 *             record, the domain's verification status changes to "Success". If Amazon SES is unable to
 *             detect the record within 72 hours, the domain's verification status changes to "Failed."
 *             In that case, to verify the domain, you must restart the verification process from the
 *             beginning.</p>
 *          <p>This operation is throttled at one request per second and can only get verification
 *             attributes for up to 100 identities at a time.</p>
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { SESClient, GetIdentityVerificationAttributesCommand } from "@aws-sdk/client-ses"; // ES Modules import
 * // const { SESClient, GetIdentityVerificationAttributesCommand } = require("@aws-sdk/client-ses"); // CommonJS import
 * // import type { SESClientConfig } from "@aws-sdk/client-ses";
 * const config = {}; // type is SESClientConfig
 * const client = new SESClient(config);
 * const input = { // GetIdentityVerificationAttributesRequest
 *   Identities: [ // IdentityList // required
 *     "STRING_VALUE",
 *   ],
 * };
 * const command = new GetIdentityVerificationAttributesCommand(input);
 * const response = await client.send(command);
 * // { // GetIdentityVerificationAttributesResponse
 * //   VerificationAttributes: { // VerificationAttributes // required
 * //     "<keys>": { // IdentityVerificationAttributes
 * //       VerificationStatus: "Pending" || "Success" || "Failed" || "TemporaryFailure" || "NotStarted", // required
 * //       VerificationToken: "STRING_VALUE",
 * //     },
 * //   },
 * // };
 *
 * ```
 *
 * @param GetIdentityVerificationAttributesCommandInput - {@link GetIdentityVerificationAttributesCommandInput}
 * @returns {@link GetIdentityVerificationAttributesCommandOutput}
 * @see {@link GetIdentityVerificationAttributesCommandInput} for command's `input` shape.
 * @see {@link GetIdentityVerificationAttributesCommandOutput} for command's `response` shape.
 * @see {@link SESClientResolvedConfig | config} for SESClient's `config` shape.
 *
 * @throws {@link SESServiceException}
 * <p>Base exception class for all service exceptions from SES service.</p>
 *
 *
 * @example GetIdentityVerificationAttributes
 * ```javascript
 * // The following example returns the verification status and the verification token for a domain identity:
 * const input = {
 *   Identities: [
 *     "example.com"
 *   ]
 * };
 * const command = new GetIdentityVerificationAttributesCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   VerificationAttributes: {
 *     example.com: {
 *       VerificationStatus: "Success",
 *       VerificationToken: "EXAMPLE3VYb9EDI2nTOQRi/Tf6MI/6bD6THIGiP1MVY="
 *     }
 *   }
 * }
 * *\/
 * ```
 *
 * @public
 */
export declare class GetIdentityVerificationAttributesCommand extends GetIdentityVerificationAttributesCommand_base {
    /** @internal type navigation helper, not in runtime. */
    protected static __types: {
        api: {
            input: GetIdentityVerificationAttributesRequest;
            output: GetIdentityVerificationAttributesResponse;
        };
        sdk: {
            input: GetIdentityVerificationAttributesCommandInput;
            output: GetIdentityVerificationAttributesCommandOutput;
        };
    };
}
