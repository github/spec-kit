import { Command as $Command } from "@smithy/smithy-client";
import { MetadataBearer as __MetadataBearer } from "@smithy/types";
import { CreateCustomVerificationEmailTemplateRequest } from "../models/models_0";
import { ServiceInputTypes, ServiceOutputTypes, SESClientResolvedConfig } from "../SESClient";
/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link CreateCustomVerificationEmailTemplateCommand}.
 */
export interface CreateCustomVerificationEmailTemplateCommandInput extends CreateCustomVerificationEmailTemplateRequest {
}
/**
 * @public
 *
 * The output of {@link CreateCustomVerificationEmailTemplateCommand}.
 */
export interface CreateCustomVerificationEmailTemplateCommandOutput extends __MetadataBearer {
}
declare const CreateCustomVerificationEmailTemplateCommand_base: {
    new (input: CreateCustomVerificationEmailTemplateCommandInput): import("@smithy/smithy-client").CommandImpl<CreateCustomVerificationEmailTemplateCommandInput, CreateCustomVerificationEmailTemplateCommandOutput, SESClientResolvedConfig, ServiceInputTypes, ServiceOutputTypes>;
    new (input: CreateCustomVerificationEmailTemplateCommandInput): import("@smithy/smithy-client").CommandImpl<CreateCustomVerificationEmailTemplateCommandInput, CreateCustomVerificationEmailTemplateCommandOutput, SESClientResolvedConfig, ServiceInputTypes, ServiceOutputTypes>;
    getEndpointParameterInstructions(): import("@smithy/middleware-endpoint").EndpointParameterInstructions;
};
/**
 * <p>Creates a new custom verification email template.</p>
 *          <p>For more information about custom verification email templates, see <a href="https://docs.aws.amazon.com/ses/latest/dg/creating-identities.html#send-email-verify-address-custom">Using
 *                 Custom Verification Email Templates</a> in the <i>Amazon SES Developer
 *                 Guide</i>.</p>
 *          <p>You can execute this operation no more than once per second.</p>
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { SESClient, CreateCustomVerificationEmailTemplateCommand } from "@aws-sdk/client-ses"; // ES Modules import
 * // const { SESClient, CreateCustomVerificationEmailTemplateCommand } = require("@aws-sdk/client-ses"); // CommonJS import
 * // import type { SESClientConfig } from "@aws-sdk/client-ses";
 * const config = {}; // type is SESClientConfig
 * const client = new SESClient(config);
 * const input = { // CreateCustomVerificationEmailTemplateRequest
 *   TemplateName: "STRING_VALUE", // required
 *   FromEmailAddress: "STRING_VALUE", // required
 *   TemplateSubject: "STRING_VALUE", // required
 *   TemplateContent: "STRING_VALUE", // required
 *   SuccessRedirectionURL: "STRING_VALUE", // required
 *   FailureRedirectionURL: "STRING_VALUE", // required
 * };
 * const command = new CreateCustomVerificationEmailTemplateCommand(input);
 * const response = await client.send(command);
 * // {};
 *
 * ```
 *
 * @param CreateCustomVerificationEmailTemplateCommandInput - {@link CreateCustomVerificationEmailTemplateCommandInput}
 * @returns {@link CreateCustomVerificationEmailTemplateCommandOutput}
 * @see {@link CreateCustomVerificationEmailTemplateCommandInput} for command's `input` shape.
 * @see {@link CreateCustomVerificationEmailTemplateCommandOutput} for command's `response` shape.
 * @see {@link SESClientResolvedConfig | config} for SESClient's `config` shape.
 *
 * @throws {@link CustomVerificationEmailInvalidContentException} (client fault)
 *  <p>Indicates that custom verification email template provided content is invalid.</p>
 *
 * @throws {@link CustomVerificationEmailTemplateAlreadyExistsException} (client fault)
 *  <p>Indicates that a custom verification email template with the name you specified
 *             already exists.</p>
 *
 * @throws {@link FromEmailAddressNotVerifiedException} (client fault)
 *  <p>Indicates that the sender address specified for a custom verification email is not
 *             verified, and is therefore not eligible to send the custom verification email. </p>
 *
 * @throws {@link LimitExceededException} (client fault)
 *  <p>Indicates that a resource could not be created because of service limits. For a list
 *             of Amazon SES limits, see the <a href="https://docs.aws.amazon.com/ses/latest/DeveloperGuide/limits.html">Amazon SES Developer
 *             Guide</a>.</p>
 *
 * @throws {@link SESServiceException}
 * <p>Base exception class for all service exceptions from SES service.</p>
 *
 *
 * @public
 */
export declare class CreateCustomVerificationEmailTemplateCommand extends CreateCustomVerificationEmailTemplateCommand_base {
    /** @internal type navigation helper, not in runtime. */
    protected static __types: {
        api: {
            input: CreateCustomVerificationEmailTemplateRequest;
            output: {};
        };
        sdk: {
            input: CreateCustomVerificationEmailTemplateCommandInput;
            output: CreateCustomVerificationEmailTemplateCommandOutput;
        };
    };
}
