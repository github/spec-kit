import { Command as $Command } from "@smithy/smithy-client";
import { MetadataBearer as __MetadataBearer } from "@smithy/types";
import { ListIdentityPoliciesRequest, ListIdentityPoliciesResponse } from "../models/models_0";
import { ServiceInputTypes, ServiceOutputTypes, SESClientResolvedConfig } from "../SESClient";
/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link ListIdentityPoliciesCommand}.
 */
export interface ListIdentityPoliciesCommandInput extends ListIdentityPoliciesRequest {
}
/**
 * @public
 *
 * The output of {@link ListIdentityPoliciesCommand}.
 */
export interface ListIdentityPoliciesCommandOutput extends ListIdentityPoliciesResponse, __MetadataBearer {
}
declare const ListIdentityPoliciesCommand_base: {
    new (input: ListIdentityPoliciesCommandInput): import("@smithy/smithy-client").CommandImpl<ListIdentityPoliciesCommandInput, ListIdentityPoliciesCommandOutput, SESClientResolvedConfig, ServiceInputTypes, ServiceOutputTypes>;
    new (input: ListIdentityPoliciesCommandInput): import("@smithy/smithy-client").CommandImpl<ListIdentityPoliciesCommandInput, ListIdentityPoliciesCommandOutput, SESClientResolvedConfig, ServiceInputTypes, ServiceOutputTypes>;
    getEndpointParameterInstructions(): import("@smithy/middleware-endpoint").EndpointParameterInstructions;
};
/**
 * <p>Returns a list of sending authorization policies that are attached to the given
 *             identity (an email address or a domain). This operation returns only a list. To get the
 *             actual policy content, use <code>GetIdentityPolicies</code>.</p>
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
 * import { SESClient, ListIdentityPoliciesCommand } from "@aws-sdk/client-ses"; // ES Modules import
 * // const { SESClient, ListIdentityPoliciesCommand } = require("@aws-sdk/client-ses"); // CommonJS import
 * // import type { SESClientConfig } from "@aws-sdk/client-ses";
 * const config = {}; // type is SESClientConfig
 * const client = new SESClient(config);
 * const input = { // ListIdentityPoliciesRequest
 *   Identity: "STRING_VALUE", // required
 * };
 * const command = new ListIdentityPoliciesCommand(input);
 * const response = await client.send(command);
 * // { // ListIdentityPoliciesResponse
 * //   PolicyNames: [ // PolicyNameList // required
 * //     "STRING_VALUE",
 * //   ],
 * // };
 *
 * ```
 *
 * @param ListIdentityPoliciesCommandInput - {@link ListIdentityPoliciesCommandInput}
 * @returns {@link ListIdentityPoliciesCommandOutput}
 * @see {@link ListIdentityPoliciesCommandInput} for command's `input` shape.
 * @see {@link ListIdentityPoliciesCommandOutput} for command's `response` shape.
 * @see {@link SESClientResolvedConfig | config} for SESClient's `config` shape.
 *
 * @throws {@link SESServiceException}
 * <p>Base exception class for all service exceptions from SES service.</p>
 *
 *
 * @example ListIdentityPolicies
 * ```javascript
 * // The following example returns a list of sending authorization policies that are attached to an identity:
 * const input = {
 *   Identity: "example.com"
 * };
 * const command = new ListIdentityPoliciesCommand(input);
 * const response = await client.send(command);
 * /* response is
 * {
 *   PolicyNames: [
 *     "MyPolicy"
 *   ]
 * }
 * *\/
 * ```
 *
 * @public
 */
export declare class ListIdentityPoliciesCommand extends ListIdentityPoliciesCommand_base {
    /** @internal type navigation helper, not in runtime. */
    protected static __types: {
        api: {
            input: ListIdentityPoliciesRequest;
            output: ListIdentityPoliciesResponse;
        };
        sdk: {
            input: ListIdentityPoliciesCommandInput;
            output: ListIdentityPoliciesCommandOutput;
        };
    };
}
