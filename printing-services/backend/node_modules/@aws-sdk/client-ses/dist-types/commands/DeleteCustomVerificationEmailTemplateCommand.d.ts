import { Command as $Command } from "@smithy/smithy-client";
import { MetadataBearer as __MetadataBearer } from "@smithy/types";
import { DeleteCustomVerificationEmailTemplateRequest } from "../models/models_0";
import { ServiceInputTypes, ServiceOutputTypes, SESClientResolvedConfig } from "../SESClient";
/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link DeleteCustomVerificationEmailTemplateCommand}.
 */
export interface DeleteCustomVerificationEmailTemplateCommandInput extends DeleteCustomVerificationEmailTemplateRequest {
}
/**
 * @public
 *
 * The output of {@link DeleteCustomVerificationEmailTemplateCommand}.
 */
export interface DeleteCustomVerificationEmailTemplateCommandOutput extends __MetadataBearer {
}
declare const DeleteCustomVerificationEmailTemplateCommand_base: {
    new (input: DeleteCustomVerificationEmailTemplateCommandInput): import("@smithy/smithy-client").CommandImpl<DeleteCustomVerificationEmailTemplateCommandInput, DeleteCustomVerificationEmailTemplateCommandOutput, SESClientResolvedConfig, ServiceInputTypes, ServiceOutputTypes>;
    new (input: DeleteCustomVerificationEmailTemplateCommandInput): import("@smithy/smithy-client").CommandImpl<DeleteCustomVerificationEmailTemplateCommandInput, DeleteCustomVerificationEmailTemplateCommandOutput, SESClientResolvedConfig, ServiceInputTypes, ServiceOutputTypes>;
    getEndpointParameterInstructions(): import("@smithy/middleware-endpoint").EndpointParameterInstructions;
};
/**
 * <p>Deletes an existing custom verification email template. </p>
 *          <p>For more information about custom verification email templates, see <a href="https://docs.aws.amazon.com/ses/latest/dg/creating-identities.html#send-email-verify-address-custom">Using
 *                 Custom Verification Email Templates</a> in the <i>Amazon SES Developer
 *                 Guide</i>.</p>
 *          <p>You can execute this operation no more than once per second.</p>
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { SESClient, DeleteCustomVerificationEmailTemplateCommand } from "@aws-sdk/client-ses"; // ES Modules import
 * // const { SESClient, DeleteCustomVerificationEmailTemplateCommand } = require("@aws-sdk/client-ses"); // CommonJS import
 * // import type { SESClientConfig } from "@aws-sdk/client-ses";
 * const config = {}; // type is SESClientConfig
 * const client = new SESClient(config);
 * const input = { // DeleteCustomVerificationEmailTemplateRequest
 *   TemplateName: "STRING_VALUE", // required
 * };
 * const command = new DeleteCustomVerificationEmailTemplateCommand(input);
 * const response = await client.send(command);
 * // {};
 *
 * ```
 *
 * @param DeleteCustomVerificationEmailTemplateCommandInput - {@link DeleteCustomVerificationEmailTemplateCommandInput}
 * @returns {@link DeleteCustomVerificationEmailTemplateCommandOutput}
 * @see {@link DeleteCustomVerificationEmailTemplateCommandInput} for command's `input` shape.
 * @see {@link DeleteCustomVerificationEmailTemplateCommandOutput} for command's `response` shape.
 * @see {@link SESClientResolvedConfig | config} for SESClient's `config` shape.
 *
 * @throws {@link SESServiceException}
 * <p>Base exception class for all service exceptions from SES service.</p>
 *
 *
 * @public
 */
export declare class DeleteCustomVerificationEmailTemplateCommand extends DeleteCustomVerificationEmailTemplateCommand_base {
    /** @internal type navigation helper, not in runtime. */
    protected static __types: {
        api: {
            input: DeleteCustomVerificationEmailTemplateRequest;
            output: {};
        };
        sdk: {
            input: DeleteCustomVerificationEmailTemplateCommandInput;
            output: DeleteCustomVerificationEmailTemplateCommandOutput;
        };
    };
}
