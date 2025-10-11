import { Command as $Command } from "@smithy/smithy-client";
import { MetadataBearer as __MetadataBearer } from "@smithy/types";
import { ListCustomVerificationEmailTemplatesRequest, ListCustomVerificationEmailTemplatesResponse } from "../models/models_0";
import { ServiceInputTypes, ServiceOutputTypes, SESClientResolvedConfig } from "../SESClient";
/**
 * @public
 */
export type { __MetadataBearer };
export { $Command };
/**
 * @public
 *
 * The input for {@link ListCustomVerificationEmailTemplatesCommand}.
 */
export interface ListCustomVerificationEmailTemplatesCommandInput extends ListCustomVerificationEmailTemplatesRequest {
}
/**
 * @public
 *
 * The output of {@link ListCustomVerificationEmailTemplatesCommand}.
 */
export interface ListCustomVerificationEmailTemplatesCommandOutput extends ListCustomVerificationEmailTemplatesResponse, __MetadataBearer {
}
declare const ListCustomVerificationEmailTemplatesCommand_base: {
    new (input: ListCustomVerificationEmailTemplatesCommandInput): import("@smithy/smithy-client").CommandImpl<ListCustomVerificationEmailTemplatesCommandInput, ListCustomVerificationEmailTemplatesCommandOutput, SESClientResolvedConfig, ServiceInputTypes, ServiceOutputTypes>;
    new (...[input]: [] | [ListCustomVerificationEmailTemplatesCommandInput]): import("@smithy/smithy-client").CommandImpl<ListCustomVerificationEmailTemplatesCommandInput, ListCustomVerificationEmailTemplatesCommandOutput, SESClientResolvedConfig, ServiceInputTypes, ServiceOutputTypes>;
    getEndpointParameterInstructions(): import("@smithy/middleware-endpoint").EndpointParameterInstructions;
};
/**
 * <p>Lists the existing custom verification email templates for your account in the current
 *             Amazon Web Services Region.</p>
 *          <p>For more information about custom verification email templates, see <a href="https://docs.aws.amazon.com/ses/latest/dg/creating-identities.html#send-email-verify-address-custom">Using
 *                 Custom Verification Email Templates</a> in the <i>Amazon SES Developer
 *                 Guide</i>.</p>
 *          <p>You can execute this operation no more than once per second.</p>
 * @example
 * Use a bare-bones client and the command you need to make an API call.
 * ```javascript
 * import { SESClient, ListCustomVerificationEmailTemplatesCommand } from "@aws-sdk/client-ses"; // ES Modules import
 * // const { SESClient, ListCustomVerificationEmailTemplatesCommand } = require("@aws-sdk/client-ses"); // CommonJS import
 * // import type { SESClientConfig } from "@aws-sdk/client-ses";
 * const config = {}; // type is SESClientConfig
 * const client = new SESClient(config);
 * const input = { // ListCustomVerificationEmailTemplatesRequest
 *   NextToken: "STRING_VALUE",
 *   MaxResults: Number("int"),
 * };
 * const command = new ListCustomVerificationEmailTemplatesCommand(input);
 * const response = await client.send(command);
 * // { // ListCustomVerificationEmailTemplatesResponse
 * //   CustomVerificationEmailTemplates: [ // CustomVerificationEmailTemplates
 * //     { // CustomVerificationEmailTemplate
 * //       TemplateName: "STRING_VALUE",
 * //       FromEmailAddress: "STRING_VALUE",
 * //       TemplateSubject: "STRING_VALUE",
 * //       SuccessRedirectionURL: "STRING_VALUE",
 * //       FailureRedirectionURL: "STRING_VALUE",
 * //     },
 * //   ],
 * //   NextToken: "STRING_VALUE",
 * // };
 *
 * ```
 *
 * @param ListCustomVerificationEmailTemplatesCommandInput - {@link ListCustomVerificationEmailTemplatesCommandInput}
 * @returns {@link ListCustomVerificationEmailTemplatesCommandOutput}
 * @see {@link ListCustomVerificationEmailTemplatesCommandInput} for command's `input` shape.
 * @see {@link ListCustomVerificationEmailTemplatesCommandOutput} for command's `response` shape.
 * @see {@link SESClientResolvedConfig | config} for SESClient's `config` shape.
 *
 * @throws {@link SESServiceException}
 * <p>Base exception class for all service exceptions from SES service.</p>
 *
 *
 * @public
 */
export declare class ListCustomVerificationEmailTemplatesCommand extends ListCustomVerificationEmailTemplatesCommand_base {
    /** @internal type navigation helper, not in runtime. */
    protected static __types: {
        api: {
            input: ListCustomVerificationEmailTemplatesRequest;
            output: ListCustomVerificationEmailTemplatesResponse;
        };
        sdk: {
            input: ListCustomVerificationEmailTemplatesCommandInput;
            output: ListCustomVerificationEmailTemplatesCommandOutput;
        };
    };
}
