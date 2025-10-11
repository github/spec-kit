import { Command as $Command } from "@smithy/smithy-client";
import { MetadataBearer as __MetadataBearer } from "@smithy/types";
import { GetIdentityPoliciesRequest, GetIdentityPoliciesResponse } from "../models/models_0";
import { ServiceInputTypes, ServiceOutputTypes, SESClientResolvedConfig } from "../SESClient";
/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link GetIdentityPoliciesCommand}.
 */
export interface GetIdentityPoliciesCommandInput extends GetIdentityPoliciesRequest {
}
/**
 * @public
 *
 * The output of {@link GetIdentityPoliciesCommand}.
 */
export interface GetIdentityPoliciesCommandOutput extends GetIdentityPoliciesResponse, __MetadataBearer {
}
declare const GetIdentityPoliciesCommand_base: {
    new (input: GetIdentityPoliciesCommandInput): import("@smithy/smithy-client").CommandImpl<GetIdentityPoliciesCommandInput, GetIdentityPoliciesCommandOutput, SESClientResolvedConfig, ServiceInputTypes, ServiceOutputTypes>;
    new (input: GetIdentityPoliciesCommandInput): import("@smithy/smithy-client").CommandImpl<GetIdentityPoliciesCommandInput, GetIdentityPoliciesCommandOutput, SESClientResolvedConfig, ServiceInputTypes, ServiceOutputTypes>;
    getEndpointParameterInstructions(): import("@smithy/middleware-endpoint").EndpointParameterInstructions;
};
/**
 * <p>Returns the requested sending authorization policies for the given identity (an email
 *             address or a domain). The policies are returned as a map of policy names to policy
 *             contents. You can retrieve a maximum of 20 policies at a time.</p>
 *          <note>
 *             <p>This operation is for the identity owner only. If you have not verified the
 *                 identity, it returns an error.</p>
 *          </note>
 *          <p>Sending authorization is a feature that enables an identity owner to authorize other
 *             senders to use its identities. For information about using sending authorization, see
 *             the <a href="https://docs.aws.amazon.com/ses/latest/dg/sending-authorization.html">Amazon SES
 *                 Developer Guide</a>.</p>
 *          <p>You can execute this operation no more than once per second.</p>
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { SESClient, GetIdentityPoliciesCommand } from "@aws-sdk/client-ses"; // ES Modules import
 * // const { SESClient, GetIdentityPoliciesCommand } = require("@aws-sdk/client-ses"); // CommonJS import
 * // import type { SESClientConfig } from "@aws-sdk/client-ses";
 * const config = {}; // type is SESClientConfig
 * const client = new SESClient(config);
 * const input = { // GetIdentityPoliciesRequest
 *   Identity: "STRING_VALUE", // required
 *   PolicyNames: [ // PolicyNameList // required
 *     "STRING_VALUE",
 *   ],
 * };
 * const command = new GetIdentityPoliciesCommand(input);
 * const response = await client.send(command);
 * // { // GetIdentityPoliciesResponse
 * //   Policies: { // PolicyMap // required
 * //     "<keys>": "STRING_VALUE",
 * //   },
 * // };
 *
 * ```
 *
 * @param GetIdentityPoliciesCommandInput - {@link GetIdentityPoliciesCommandInput}
 * @returns {@link GetIdentityPoliciesCommandOutput}
 * @see {@link GetIdentityPoliciesCommandInput} for command's `input` shape.
 * @see {@link GetIdentityPoliciesCommandOutput} for command's `response` shape.
 * @see {@link SESClientResolvedConfig | config} for SESClient's `config` shape.
 *
 * @throws {@link SESServiceException}
 * <p>Base exception class for all service exceptions from SES service.</p>
 *
 *
 * @example GetIdentityPolicies
 * ```javascript
 * // The following example returns a sending authorization policy for an identity:
 * const input = {
 *   Identity: "example.com",
 *   PolicyNames: [
 *     "MyPolicy"
 *   ]
 * };
 * const command = new GetIdentityPoliciesCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   Policies: {
 *     MyPolicy: `{"Version":"2008-10-17","Statement":[{"Sid":"stmt1469123904194","Effect":"Allow","Principal":{"AWS":"arn:aws:iam::123456789012:root"},"Action":["ses:SendEmail","ses:SendRawEmail"],"Resource":"arn:aws:ses:us-east-1:EXAMPLE65304:identity/example.com"}]}`
 *   }
 * }
 * *\/
 * ```
 *
 * @public
 */
export declare class GetIdentityPoliciesCommand extends GetIdentityPoliciesCommand_base {
    /** @internal type navigation helper, not in runtime. */
    protected static __types: {
        api: {
            input: GetIdentityPoliciesRequest;
            output: GetIdentityPoliciesResponse;
        };
        sdk: {
            input: GetIdentityPoliciesCommandInput;
            output: GetIdentityPoliciesCommandOutput;
        };
    };
}
