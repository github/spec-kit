import { Command as $Command } from "@smithy/smithy-client";
import { MetadataBearer as __MetadataBearer } from "@smithy/types";
import { UpdateCustomVerificationEmailTemplateRequest } from "../models/models_0";
import { ServiceInputTypes, ServiceOutputTypes, SESClientResolvedConfig } from "../SESClient";
/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link UpdateCustomVerificationEmailTemplateCommand}.
 */
export interface UpdateCustomVerificationEmailTemplateCommandInput extends UpdateCustomVerificationEmailTemplateRequest {
}
/**
 * @public
 *
 * The output of {@link UpdateCustomVerificationEmailTemplateCommand}.
 */
export interface UpdateCustomVerificationEmailTemplateCommandOutput extends __MetadataBearer {
}
declare const UpdateCustomVerificationEmailTemplateCommand_base: {
    new (input: UpdateCustomVerificationEmailTemplateCommandInput): import("@smithy/smithy-client").CommandImpl<UpdateCustomVerificationEmailTemplateCommandInput, UpdateCustomVerificationEmailTemplateCommandOutput, SESClientResolvedConfig, ServiceInputTypes, ServiceOutputTypes>;
    new (input: UpdateCustomVerificationEmailTemplateCommandInput): import("@smithy/smithy-client").CommandImpl<UpdateCustomVerificationEmailTemplateCommandInput, UpdateCustomVerificationEmailTemplateCommandOutput, SESClientResolvedConfig, ServiceInputTypes, ServiceOutputTypes>;
    getEndpointParameterInstructions(): import("@smithy/middleware-endpoint").EndpointParameterInstructions;
};
/**
 * <p>Updates an existing custom verification email template.</p>
 *          <p>For more information about custom verification email templates, see <a href="https://docs.aws.amazon.com/ses/latest/dg/creating-identities.html#send-email-verify-address-custom">Using
 *                 Custom Verification Email Templates</a> in the <i>Amazon SES Developer
 *                 Guide</i>.</p>
 *          <p>You can execute this operation no more than once per second.</p>
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { SESClient, UpdateCustomVerificationEmailTemplateCommand } from "@aws-sdk/client-ses"; // ES Modules import
 * // const { SESClient, UpdateCustomVerificationEmailTemplateCommand } = require("@aws-sdk/client-ses"); // CommonJS import
 * // import type { SESClientConfig } from "@aws-sdk/client-ses";
 * const config = {}; // type is SESClientConfig
 * const client = new SESClient(config);
 * const input = { // UpdateCustomVerificationEmailTemplateRequest
 *   TemplateName: "STRING_VALUE", // required
 *   FromEmailAddress: "STRING_VALUE",
 *   TemplateSubject: "STRING_VALUE",
 *   TemplateContent: "STRING_VALUE",
 *   SuccessRedirectionURL: "STRING_VALUE",
 *   FailureRedirectionURL: "STRING_VALUE",
 * };
 * const command = new UpdateCustomVerificationEmailTemplateCommand(input);
 * const response = await client.send(command);
 * // {};
 *
 * ```
 *
 * @param UpdateCustomVerificationEmailTemplateCommandInput - {@link UpdateCustomVerificationEmailTemplateCommandInput}
 * @returns {@link UpdateCustomVerificationEmailTemplateCommandOutput}
 * @see {@link UpdateCustomVerificationEmailTemplateCommandInput} for command's `input` shape.
 * @see {@link UpdateCustomVerificationEmailTemplateCommandOutput} for command's `response` shape.
 * @see {@link SESClientResolvedConfig | config} for SESClient's `config` shape.
 *
 * @throws {@link CustomVerificationEmailInvalidContentException} (client fault)
 *  <p>Indicates that custom verification email template provided content is invalid.</p>
 *
 * @throws {@link CustomVerificationEmailTemplateDoesNotExistException} (client fault)
 *  <p>Indicates that a custom verification email template with the name you specified does
 *             not exist.</p>
 *
 * @throws {@link FromEmailAddressNotVerifiedException} (client fault)
 *  <p>Indicates that the sender address specified for a custom verification email is not
 *             verified, and is therefore not eligible to send the custom verification email. </p>
 *
 * @throws {@link SESServiceException}
 * <p>Base exception class for all service exceptions from SES service.</p>
 *
 *
 * @public
 */
export declare class UpdateCustomVerificationEmailTemplateCommand extends UpdateCustomVerificationEmailTemplateCommand_base {
    /** @internal type navigation helper, not in runtime. */
    protected static __types: {
        api: {
            input: UpdateCustomVerificationEmailTemplateRequest;
            output: {};
        };
        sdk: {
            input: UpdateCustomVerificationEmailTemplateCommandInput;
            output: UpdateCustomVerificationEmailTemplateCommandOutput;
        };
    };
}
