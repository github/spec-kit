import { Command as $Command } from "@smithy/smithy-client";
import { MetadataBearer as __MetadataBearer } from "@smithy/types";
import { VerifyEmailIdentityRequest, VerifyEmailIdentityResponse } from "../models/models_0";
import { ServiceInputTypes, ServiceOutputTypes, SESClientResolvedConfig } from "../SESClient";
/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link VerifyEmailIdentityCommand}.
 */
export interface VerifyEmailIdentityCommandInput extends VerifyEmailIdentityRequest {
}
/**
 * @public
 *
 * The output of {@link VerifyEmailIdentityCommand}.
 */
export interface VerifyEmailIdentityCommandOutput extends VerifyEmailIdentityResponse, __MetadataBearer {
}
declare const VerifyEmailIdentityCommand_base: {
    new (input: VerifyEmailIdentityCommandInput): import("@smithy/smithy-client").CommandImpl<VerifyEmailIdentityCommandInput, VerifyEmailIdentityCommandOutput, SESClientResolvedConfig, ServiceInputTypes, ServiceOutputTypes>;
    new (input: VerifyEmailIdentityCommandInput): import("@smithy/smithy-client").CommandImpl<VerifyEmailIdentityCommandInput, VerifyEmailIdentityCommandOutput, SESClientResolvedConfig, ServiceInputTypes, ServiceOutputTypes>;
    getEndpointParameterInstructions(): import("@smithy/middleware-endpoint").EndpointParameterInstructions;
};
/**
 * <p>Adds an email address to the list of identities for your Amazon SES account in the current
 *             Amazon Web Services Region and attempts to verify it. As a result of executing this operation, a
 *             verification email is sent to the specified address.</p>
 *          <p>You can execute this operation no more than once per second.</p>
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { SESClient, VerifyEmailIdentityCommand } from "@aws-sdk/client-ses"; // ES Modules import
 * // const { SESClient, VerifyEmailIdentityCommand } = require("@aws-sdk/client-ses"); // CommonJS import
 * // import type { SESClientConfig } from "@aws-sdk/client-ses";
 * const config = {}; // type is SESClientConfig
 * const client = new SESClient(config);
 * const input = { // VerifyEmailIdentityRequest
 *   EmailAddress: "STRING_VALUE", // required
 * };
 * const command = new VerifyEmailIdentityCommand(input);
 * const response = await client.send(command);
 * // {};
 *
 * ```
 *
 * @param VerifyEmailIdentityCommandInput - {@link VerifyEmailIdentityCommandInput}
 * @returns {@link VerifyEmailIdentityCommandOutput}
 * @see {@link VerifyEmailIdentityCommandInput} for command's `input` shape.
 * @see {@link VerifyEmailIdentityCommandOutput} for command's `response` shape.
 * @see {@link SESClientResolvedConfig | config} for SESClient's `config` shape.
 *
 * @throws {@link SESServiceException}
 * <p>Base exception class for all service exceptions from SES service.</p>
 *
 *
 * @example VerifyEmailIdentity
 * ```javascript
 * // The following example starts the email address verification process with Amazon SES:
 * const input = {
 *   EmailAddress: "user@example.com"
 * };
 * const command = new VerifyEmailIdentityCommand(input);
 * const response = await client.send(command);
 * /* response is
 * { /* metadata only *\/ }
 * *\/
 * ```
 *
 * @public
 */
export declare class VerifyEmailIdentityCommand extends VerifyEmailIdentityCommand_base {
    /** @internal type navigation helper, not in runtime. */
    protected static __types: {
        api: {
            input: VerifyEmailIdentityRequest;
            output: {};
        };
        sdk: {
            input: VerifyEmailIdentityCommandInput;
            output: VerifyEmailIdentityCommandOutput;
        };
    };
}
